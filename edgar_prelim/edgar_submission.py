from collections import namedtuple
from functools import partial
from itertools import zip_longest, takewhile
from operator import attrgetter, itemgetter
from typing import Iterator, Optional, List, Iterable, Tuple

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from retrying import retry

from edgar_prelim.bs4_util import read_table_tag, sanitize_text
from edgar_prelim.edgar_fiscal_period import has_fiscal_period, is_header_part, parse_fiscal_period_row
from edgar_prelim.edgar_items import PrelimItem, prelim_items
from edgar_prelim.edgar_re import *
from edgar_prelim.edgar_title import title_from_table_tag, is_units, units_from_table
from edgar_prelim.func_util import head_option

Submission = namedtuple('Submission', ['cik', 'raw', 'number', 'header', 'documents'])
SubmissionDocument = namedtuple("SubmissionDocument", ['type', 'filename', 'text'])


@retry(stop_max_attempt_number=7, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def load_submission(href: str) -> Submission:
    """ Downloads and parses a submission into its component documents."""
    result = requests.get(href)
    if result.status_code != requests.codes.ok:
        result.raise_for_status()
    else:
        return parse_submission(result.text)


def _iter_submission_tags(raw: str, tag: str) -> Iterator[str]:
    """Returns an iterator over the contents of the specified tag."""
    start_tag = f'<{tag}>'
    end_tag = f'</{tag}>'
    start_index = raw.find(start_tag)
    while start_index != -1:
        end_index = raw.find(end_tag, start_index)
        yield raw[start_index + len(start_tag):end_index]
        start_index = raw.find(start_tag, end_index)


def parse_submission(raw: str) -> Submission:
    """Parses submission text into a Submission tuple."""
    number = re.search(r'<SEC-DOCUMENT>(.+)\n', raw).group(1)
    header = list(_iter_submission_tags(raw, 'SEC-HEADER'))[0]
    cik = re.search(r'CENTRAL INDEX KEY:\s+(\d+)', header).group(1)
    documents = [
        SubmissionDocument(doc_type, filename, txt)
        for doc in _iter_submission_tags(raw, 'DOCUMENT')
        for doc_type in [re.search(r'<TYPE>(.+)\s', doc).group(1)]
        if doc_type != 'GRAPHIC'
        for filename in [re.search(r'<FILENAME>(.+)\s', doc).group(1)]
        if filename.endswith(".htm") or filename.endswith(".html")
        for txt in _iter_submission_tags(doc, 'TEXT')
    ]
    return Submission(cik, raw, number, header, documents)


def _split_tables(raw_df: pd.DataFrame, prior_df: Optional[pd.DataFrame] = None) -> List[pd.DataFrame]:
    """
    If a table contains what appears to be multiple header rows, splits the tables into parts so that the headers
    rows are at the start of each table. If the start of the table contains no no headers, but has the same number of
    columns as the previous table, copies the headers from the previous to this table.
    """
    df = raw_df.dropna(axis=0, how='all')
    if df.empty:
        return []

    n_rows, n_cols = df.shape
    header_rows = df.apply(_is_header_row, axis=1)
    if prior_df is not None and not any(header_rows[0:min(len(header_rows), 5)]) and n_cols == prior_df.shape[1]:
        # Special Case
        # If the table is missing a header, perhaps it is a continuation of the prior table?
        # If the prior table has the same number of columns, "borrow" those headers by pre-pending them.
        prior_header_rows = prior_df.apply(_is_header_row, axis=1)
        return _split_tables(pd.concat([prior_df[prior_header_rows], df]))

    start_idx = [
        i
        for i, v in enumerate(header_rows)
        if v
        # Take the first row of each block of header rows.
        if i == 0 or not header_rows.iloc[i - 1]
        # A standalone header row must have at least one fiscal period in it.
        if i == n_rows - 1 or header_rows.iloc[i + 1] or has_fiscal_period(df.iloc[i, :])
    ]
    return [df.iloc[slice(i, j), :] for i, j in zip_longest(start_idx, start_idx[1:])]


TableTuple = namedtuple('TableTuple', ['title', 'df', 'raw_df', 'tag', 'rank'])


def parse_tables(submission: Submission) -> List[TableTuple]:
    """Extracts all of the tables with relevant titles in the submission."""
    tables = []
    prior_table = None
    for doc in submission.documents:
        for table_tag in BeautifulSoup(doc.text, features='lxml').find_all('table'):
            if table_tag.find_all('table'):
                # Ignore tables with nested tables for now.
                continue

            table_title = title_from_table_tag(table_tag, submission.cik)
            if table_title is None:
                # No title or irrelevant title.
                continue

            title, rank = table_title
            raw_df = read_table_tag(table_tag)
            if raw_df is None:
                continue

            for split_df in _split_tables(raw_df, prior_df=prior_table):
                table_tuple = TableTuple(title, clean_table(split_df), split_df, table_tag, rank)
                tables.append(table_tuple)
                prior_table = split_df

    return sorted(tables, key=attrgetter('rank'))


def _drop_single_value_rows_and_columns(df: pd.DataFrame) -> pd.DataFrame:
    def is_not_unique(s: pd.Series):
        return s.nunique() > 1

    def is_header_related(s: pd.Series):
        unique_values = s.dropna().unique()
        return len(unique_values) != 0 and is_header_part(unique_values[0])

    if df.empty:
        return df
    else:
        keep_rows = df.apply(lambda s: is_not_unique(s) or is_header_related(s), axis=1)
        df = df[keep_rows]

    if df.empty:
        return df
    else:
        keep_columns = df.apply(lambda s: is_not_unique(s) or is_header_related(s), axis=0)
        return df.loc[:, keep_columns]


# noinspection PyTypeChecker
def _collapse_identical_rows(df: pd.DataFrame, start_row: int = 0) -> pd.DataFrame:
    n_rows, _ = df.shape
    if start_row >= n_rows - 1:
        return df
    else:
        row1 = df.iloc[start_row, :]
        row2 = df.iloc[start_row + 1, :]
        if all(row1 == row2):
            retained_idx = [i for i in range(0, n_rows) if i != start_row]
            return _collapse_identical_rows(df.iloc[retained_idx, :], start_row)
        else:
            return _collapse_identical_rows(df, start_row + 1)


# noinspection PyTypeChecker
def _collapse_identical_columns(df: pd.DataFrame, start_col: int = 0) -> pd.DataFrame:
    _, n_cols = df.shape
    if start_col >= n_cols - 1:
        return df
    else:
        col1 = df.iloc[:, start_col]
        col2 = df.iloc[:, start_col + 1]
        col1_span = col1.mask(col1 == '', col2)
        col2_span = col2.mask(col2 == '', col1)

        if any(col1 == col2) and all(col1_span == col2_span):
            collapsed = df.pipe(_replace_columns, col1_span, start_col)
            return _collapse_identical_columns(collapsed, start_col)
        else:
            return _collapse_identical_columns(df, start_col + 1)


def _concat(row: pd.Series, sep=''):
    if row.nunique() == 1:
        return row.iloc[0]
    else:
        res = row.iloc[0]
        for i in range(1, len(row)):
            if not res.endswith(row.iloc[i]):
                res += sep + row.iloc[i]
        return res


def _collapse_header_rows(df: pd.DataFrame, start_row: int = 0) -> pd.DataFrame:
    n_rows, _ = df.shape
    if start_row + 1 >= n_rows:
        return df
    else:
        second_row = df.iloc[1, 0:-1]
        if _is_header_row(second_row) or all(second_row == ''):
            parts = []
            if start_row > 0:
                parts.append(df.iloc[:start_row, :])

            if not _is_ignorable_header_row(second_row):
                rows = df.iloc[start_row:start_row + 2, :]
                row_combined = rows.apply(partial(_concat, sep=' '), axis=0)
            else:
                row_combined = df.iloc[start_row]

            parts.append(pd.DataFrame(row_combined).T)

            if start_row + 2 < n_rows:
                parts.append(df.iloc[start_row + 2:, :])

            combined_row_df = pd.concat(parts, axis=0, ignore_index=True)
            return _collapse_header_rows(combined_row_df, start_row)
        else:
            return df


def _cols_share_header(df: pd.DataFrame) -> bool:
    return not df.empty and df.iloc[0, 0] != '' and df.iloc[0, :].where(df.iloc[0, :] != '').nunique() == 1


def _collapse_columns_with_identical_header(df: pd.DataFrame, start_col: int = 1) -> pd.DataFrame:
    _, n_cols = df.shape
    if start_col + 1 >= n_cols:
        return df
    else:
        cols = df.iloc[:, start_col:start_col + 2]
        if _cols_share_header(cols):
            col_combined = cols.apply(_concat, axis=1)
            collapsed = df.pipe(_replace_columns, col_combined, start_col)
            return _collapse_columns_with_identical_header(collapsed, start_col)
        else:
            return _collapse_columns_with_identical_header(df, start_col + 1)


def _replace_columns(df: pd.DataFrame, col_combined: pd.Series, start_col: int, num_cols: int = 2) -> pd.DataFrame:
    _, total_cols = df.shape
    parts = []

    if start_col > 0:
        parts.append(df.iloc[:, :start_col])

    parts.append(col_combined)

    if start_col + num_cols < total_cols:
        parts.append(df.iloc[:, start_col + num_cols:])

    return pd.concat(parts, axis=1, ignore_index=True)


def _drop_null_rows_and_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(axis=0, how='all').dropna(axis=1, how='all')


def _drop_bogus_header_rows(df: pd.DataFrame) -> pd.DataFrame:
    row_idx = list(takewhile(lambda i: not any(df.iloc[i, 1:].map(is_header_part)), range(len(df))))
    return df.iloc[max(row_idx) + 1:, :] if row_idx else df


def _filter_bad_table(df: pd.DataFrame, raw_df: pd.DataFrame) -> pd.DataFrame:
    _, cols = df.shape
    _, raw_cols = raw_df.shape
    return df if raw_cols <= 4 or cols > 2 else pd.DataFrame()


def clean_table(df: pd.DataFrame) -> pd.DataFrame:
    """Transforms a table into one where the header is in the first row and the items are in the leading columns."""
    return df.pipe(_drop_single_value_rows_and_columns) \
        .pipe(_drop_null_rows_and_columns) \
        .fillna(value='') \
        .apply(lambda c: c.str.replace(r'\s+', ' ')) \
        .pipe(_collapse_identical_rows) \
        .pipe(_collapse_identical_columns) \
        .pipe(_drop_bogus_header_rows) \
        .pipe(_collapse_header_rows) \
        .pipe(_collapse_columns_with_identical_header) \
        .pipe(_filter_bad_table, df)


def _is_row_part(cell: str) -> bool:
    """Returns true if the cell can reasonably be inferred to be from a row values."""
    prepped = str(cell).lower().strip()
    if re.match(r'^[$(]?\s*[\d,]+\.?\d*[)%]*$', prepped) is not None:
        value = _parse_item_value(prepped)
        return value is not None and not ((2000 <= value <= 2050) or (28 <= value <= 31))
    else:
        return is_hyphen(prepped)


def _is_ignorable_header_row(row: pd.Series) -> bool:
    """Returns true if this is a row that might appear inside a header, but plays no part in forming
    the fiscal periods."""
    s = row.replace('', np.nan).dropna()
    return all(s.map(is_units)) or all(s.str.contains(UNAUDITED_EXACT, flags=re.IGNORECASE))


def _is_header_row(row: pd.Series) -> bool:
    """Returns true if the row can reasonably be assumed to be a header row."""
    s = row.replace('', np.nan).dropna()
    return (any(s.map(is_header_part)) and not any(s.map(_is_row_part))) or _is_ignorable_header_row(s)


def _parse_item_value(src_value: str) -> Optional[float]:
    """
    Does its darndest to extract a value from a table cell. Hyphens are considered zero. Values in parent (or with at
    least a leading parent are negative."""
    value = re.sub(r'[$%,*]', '', src_value)
    if is_hyphen(value):
        return 0.

    if value == '' or re.search(rf'\d', value) is None:
        return None

    signum = 1.0
    value = re.sub(r'\s+', '', value)
    neg = re.match(r'\(([\d.]+)\)?', value)
    if neg:
        value = neg.group(1)
        signum = -1.0
    else:
        pos = re.search(r'([\d.]+)', value)
        if pos:
            value = pos.group(1)

    try:
        return signum * float(value)
    except ValueError:
        return np.nan


ItemValue = namedtuple('ItemValue', ['fiscal_period', 'src_row', 'src_column', 'src_value', 'value', 'rank'])


def _item_value_from_table(df: pd.DataFrame, item_pattern: str, pattern_rank: int, multiplier: float,
                           fiscal_periods: List[Tuple[int, str]]) -> Optional[ItemValue]:
    """
    Looks for an item matching the pattern in the leading columns of the table and returns the parsable value with the
    latest fiscal period.
    :param df: the cleaned table in a pd.DataFrame
    :param item_pattern: the pattern to match against an item name
    :param pattern_rank: the relative rank of this pattern over other patterns for the same item
    :param multiplier: the units multiplier
    :param fiscal_periods: the fiscal periods (column and name) in order from most to least recent.
    :return:
    """
    first_fp_column = min(map(itemgetter(0), fiscal_periods))
    for item_col in range(0, min(first_fp_column, len(df.columns))):
        item_df = df[df.iloc[:, item_col].str.contains(allow_space_between_letters(item_pattern), flags=re.IGNORECASE)]
        if item_df.empty:
            continue

        for fp_index, fiscal_period in fiscal_periods:
            for src_row, src_value in item_df.loc[:, [df.columns[item_col], fp_index]].itertuples(index=False):
                value = _parse_item_value(src_value)
                if value is not None:
                    return ItemValue(
                        fiscal_period=fiscal_period,
                        src_row=sanitize_text(src_row),
                        src_column=sanitize_text(df.iloc[0, :].loc[fp_index]),
                        src_value=sanitize_text(src_value),
                        value=multiplier * value,
                        rank=pattern_rank)
    return None


# noinspection PyProtectedMember
def items_from_table(table: TableTuple, items: Iterable[PrelimItem] = None) -> pd.DataFrame:
    """Extracts all items from the table into a pd.DataFrame whose columns describe the item and its value along
    with the source row, column, value and units"""
    if items is None:
        items = prelim_items

    df = table.df
    if df.empty:
        return pd.DataFrame()

    fiscal_periods = parse_fiscal_period_row(df.iloc[0, :])
    if not fiscal_periods:
        return pd.DataFrame()

    units, units_multiplier = units_from_table(table.tag, table.title)
    item_rows = []
    for item in items:
        src_units = units
        per_share = 'per share' in item.name
        multiplier = 1.0 if per_share else units_multiplier
        item_value = head_option(
            _item_value_from_table(df, pattern, item_rank, multiplier, fiscal_periods)
            for item_rank, pattern in enumerate(item.patterns))

        if item_value is not None:
            if not per_share and units_multiplier == 1.0 and abs(item_value.value) < item.min_abs_value:
                src_units = "inferred: thousands"
                item_value = item_value._replace(value=item_value.value * 1e3)

            item_dict = {
                'item': item.name,
                'item_rank': item_value.rank,
                'item_value': item_value.value if abs(item_value.value) < 1.e12 else np.nan,
                'fiscal_period': item_value.fiscal_period,
                'table_rank': table.rank,
                'src_row': item_value.src_row,
                'src_column': item_value.src_column,
                'src_value': item_value.src_value,
                'src_table': sanitize_text(table.title),
                'src_units': sanitize_text(src_units)
            }

            item_rows.append(item_dict)

    return pd.DataFrame(item_rows) if len(item_rows) > 0 else pd.DataFrame()


def items_from_tables(df_iter: Iterable[TableTuple], items: List[PrelimItem] = None) -> pd.DataFrame:
    """Returns a table of items and their values found in the selection of tables supplied. If the items are found
    more than once, the values are ordered first by item rank then by item rank, and then the first is selected."""
    if items is None:
        items = prelim_items

    if not items:
        return pd.DataFrame()

    item_dfs = [
        item_df
        for table_tuple in df_iter
        for item_df in [items_from_table(table_tuple)]
        if not item_df.empty
    ]
    return choose_item_by_rank(pd.concat(item_dfs, sort=False, ignore_index=True)) if item_dfs else pd.DataFrame()


def choose_item_by_rank(df: pd.DataFrame) -> pd.DataFrame:
    """Groups by item and selects the row with the minimum item rank and table rank."""
    res = df.groupby('item').apply(
        lambda x: x.sort_values(['table_rank', 'item_rank']).iloc[[0], :].set_index('item')
    )
    return res.droplevel(0, axis=0).reset_index()

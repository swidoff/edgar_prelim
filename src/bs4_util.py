import re
from functools import reduce
from itertools import chain, takewhile
from typing import Iterator, Optional, Iterable, Pattern, Tuple

import numpy as np
import pandas as pd
import unicodedata
from bs4 import Tag, NavigableString

from func_util import head_option


def read_table_tag(table: Tag) -> Optional[pd.DataFrame]:
    """
    Wrapper around pd.read_html that attempts to compensate for certain oddities in the implementation and the
    html.

    :param table: a BeautifulSoup Tag object for a table that should not contain nested tables.
    :return: a single table whose values are either str or np.NaN, parsed from the tag.
    """
    if table.name != 'table':
        raise ValueError(f'Expected a table tag, got {table.name}')

    if table.find_all('table'):
        raise ValueError('table tag contains a nested table.')

    if table.df is not None:
        return table.df

    def count_table_columns(tag: Tag) -> int:
        def count_columns(r: Tag):
            return sum(int(td['colspan']) if 'colspan' in td.attrs else 1 for td in r.find_all('td'))

        return max(chain((count_columns(r) for r in tag.find_all('tr')), (0,)))

    def reset_table_index(df: pd.DataFrame) -> pd.DataFrame:
        return df.reset_index() if isinstance(df.index, pd.MultiIndex) or df.index.dtype.type != np.int64 else df

    col_count = count_table_columns(table)
    if not col_count:
        return None
    else:
        for row in table.find_all("tr"):
            # Remove invisible rows. These are horrible.
            if 'style' in row.attrs and re.search(r'visibility:\s*hidden', row['style']):
                row.extract()

            # Set missing colspan on singleton columns.
            cols = list(row.find_all("td"))
            if len(cols) == 1 and 'colspan' not in cols[0].attrs:
                cols[0].attrs['colspan'] = col_count

        # Replace header cells with regular cells.
        html = table.prettify().replace("<th", "<td").replace("</th", "</td")
        try:
            # Read the table with all columns as str.
            df_ls = pd.read_html(html, flavor='html5lib', converters={i: str for i in range(col_count)})
            df = df_ls[0] if df_ls else None
        except IndexError:
            # Sometimes we can't anticipate the number of columns, so parse the table, remove any index and set to str.
            df_ls = pd.read_html(html, flavor='html5lib')
            df = df_ls[0].pipe(reset_table_index).astype(str).replace('nan', np.NaN) if df_ls else None

        table.df = df
        return df


def iter_tag_text(tag: Tag) -> Iterator[str]:
    """
    Iterates over the text components of an html tag, using read_table_tag for table tags to take advantage of
    pd.read_html's smart handling of the text components of table cells.
    :param tag: a bs4 Tag object.
    :return: an iterator over the text components of tag.
    """
    for c in tag.children:
        if type(c) is NavigableString:
            yield c.strip()
        elif type(c) is Tag:
            yield from iter_tag_text(c)

    if tag.name == 'table':
        tab = read_table_tag(tag)
        if tab is not None:
            yield from (str(tab.iloc[row, 0]) for row in range(0, tab.shape[0]))


def iter_previous_tags(tag: Tag,
                       max_parents: int = 1e6,
                       max_previous: int = 1e6,
                       parent_threshold: int = 2,
                       top_level_tag: str = 'text') -> Iterator[Tag]:
    """
    Iterates over the previous siblings of a tag that are also tags, with the added feature that if there are fewer
    than 'parent_threshold' previous tags, it will continue iterating over the previous siblings of the parent tag.

    :param tag: The tag whose previous siblings to iterate over.
    :param max_parents: The max number of times to continue iterating at the parent's level.
    :param max_previous: The max number of previous tags to iterate over.
    :param parent_threshold: If there are fewer than this number of previous siblings for a tag, the iteration will
    continue with the parent's previous siblings.
    :param top_level_tag: If this tag is the parent when the iteration would move to the parent's level, iteration
    ceases.
    :return: An iterator over BeautifulSoup Tag objects.
    """
    count = 0
    for prev in tag.previous_siblings:
        if type(prev) is Tag:
            yield prev
            count += 1
            if count == max_previous:
                break

    if count < parent_threshold and max_parents > 0 and tag.parent and tag.parent.name != top_level_tag:
        yield from iter_previous_tags(tag.parent, max_parents - 1, max_previous, parent_threshold, top_level_tag)


def match_tag_text(tag: Tag, patterns: Iterable[Pattern]) -> Iterator[Tuple[str, int]]:
    """
    Returns all text parts of tag (as produced by iter_tag_text) that matches at least one of the supplied patterns.

    :param tag: the tag whose text components will be searched in the order returned by iter_tag_text.
    :param patterns: The re.Pattern objects used to match the text components.
    :return: an iterator of Tuples, where the first element is the matched text and the second the index of the matched
    pattern.
    """
    for txt in iter_tag_text(tag):
        for pattern_idx, pattern in enumerate(patterns):
            match = re.search(pattern, txt.lower())
            if match:
                yield txt, pattern_idx


def find_tag_text_matches(tag_iter: Iterable[Tag],
                          inclusion_patterns: Iterable[Pattern],
                          exclusion_patterns: Iterable[Pattern] = None,
                          max_tables: int = 2,
                          continue_to_next_table_after_match: str = None) -> Iterator[Optional[Tuple[str, int]]]:
    """
    Finds all the text components (as produced by iter_tag_text) in the iterable of Tags that is supplied that matches
    the supplied patterns. Includes addition options to tune the search.

    :param tag_iter: The Iterable of tags that will be searched in order.
    :param inclusion_patterns: The patterns against which to match the text components.
    :param exclusion_patterns: If this argument is not None, the Iterator will stop once a text component matches one of these
    patterns and issue a None, to indicate that the search terminated before reaching all text components.
    :param max_tables: The search will stop after this number of table is encountered, so as not search to far in
    the document, beyond where the match is likely to be relevant. If max tables is encountered, then the Iterator will
    return a 'None' to indicate that the search terminated before searching all text components.
    :param continue_to_next_table_after_match: If not None, if this exact text is encountered, the search will continue
    to the next table and then issue a 'None' to indicate that the search terminated before searching all text
    components.
    :return: An iterator of tuples where the first element is the matched text and the second is the index of matched
    pattern. If the search terminated due to one of the above conditions, a None will be yielded as the last element.
    """
    remaining_tables = max_tables
    for tag in tag_iter:
        if remaining_tables <= 0 and (tag.name == 'table' or tag.find('table') is not None):
            yield None
            return

        if exclusion_patterns and any(match_tag_text(tag, exclusion_patterns)) > 0:
            yield None
            return

        yield from match_tag_text(tag, inclusion_patterns)

        # If until_match is specified, don't continue past its location to avoid matching an earlier table.
        if continue_to_next_table_after_match and \
                any(txt == continue_to_next_table_after_match for txt in iter_tag_text(tag)):
            remaining_tables = 0

        if tag.name == 'table' or tag.find('table') is not None:
            remaining_tables -= 1
            if remaining_tables <= 0:
                yield None
                return


def match_table_title_text(table: Tag,
                           inclusion_patterns: Iterable[Pattern],
                           exclusion_patterns: Iterable[Pattern] = None,
                           first_match: bool = False,
                           continue_to_next_table_after_match: str = None,
                           max_previous: int = 15,
                           max_parents: int = 50,
                           max_tables: int = 2) -> Optional[Tuple[str, int]]:
    """
    Attempt to locate a best guess at the title for a table tag by first matching the text components inside the table
    and then the text inside tags previous to the table. The inclusion_patterns are supplied in their rank order and
    if multiple matches are found, the match to the lowest indexed pattern is returned.

    :param table: The table tag from which to begin the search
    :param inclusion_patterns: The patterns to match against in their order of preference.
    :param exclusion_patterns: The search will not continue past a tag where an exclusion pattern is reached (or
    return any matches within that tag).
    :param first_match: If True, returns the first match encountered rather than best among all matches.
    :param continue_to_next_table_after_match: If this str is supplied and that text is encountered in a tag, the search
    will not continue into or past the next tag that is or contains a table.
    :param max_previous: The number of tags previous to the table to search.
    :param max_parents: If the table is nested within another tag, the number of levels the search will go up until
    it encounters previous siblings.
    :param max_tables: The max number of tables (or tags containing tables) the search will encounter before returning
    :return: A guess for the table's title, or None if no matches were found.
    """
    table_matches = find_tag_text_matches(
        [table],
        inclusion_patterns,
        exclusion_patterns,
        max_tables=2,
        continue_to_next_table_after_match=continue_to_next_table_after_match)

    prev_matches = find_tag_text_matches(
        iter_previous_tags(table, max_parents=max_parents, max_previous=max_previous, parent_threshold=2),
        inclusion_patterns,
        exclusion_patterns,
        max_tables=max_tables,
        continue_to_next_table_after_match=continue_to_next_table_after_match
    )

    all_matches = takewhile(lambda x: x is not None, chain(table_matches, prev_matches))
    if first_match:
        return head_option(all_matches)
    else:
        return reduce(lambda x, y: y if not x or y[1] < x[1] else x, all_matches, None)


def sanitize_text(txt: str) -> str:
    """Handles non-ascii data found in text tags so that it can be saved to a database with any collation."""
    if not txt:
        return txt
    else:
        b = unicodedata.normalize('NFD', txt)
        return re.sub(r'\s+', ' ', b.encode('ascii', 'ignore').decode('ascii'))[:1024]

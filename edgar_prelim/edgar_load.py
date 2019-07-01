# noinspection PyUnresolvedReferences
from collections import OrderedDict, namedtuple, ChainMap
from datetime import timedelta
from operator import attrgetter
from pathlib import Path
from typing import Union

import papermill as pm
import qgrid
# noinspection PyProtectedMember
from nbconvert.nbconvertapp import NbConvertApp
from sqlalchemy import and_, between

from bs4_util import *
from edgar_db import *
from edgar_items import *
from edgar_query import *
from edgar_submission import load_submission, items_from_tables, parse_tables, choose_item_by_rank
from edgar_validate import validate_prelims
from logging_config import init_logging

# TODO:
# Split tables with multiple sections
# Clean up regexes.
# Find items in text highlights
#   (https://www.sec.gov/Archives/edgar/data/1253317/000117184319002623/exh_991.htm)
# Find partial fiscal periods in table titles:
#   (https://www.sec.gov/Archives/edgar/data/1178409/000110465913037162/a13-11516_1ex99d1.htm)
# Deal with statements that only report income statement items YTD:
#   (https://www.sec.gov/Archives/edgar/data/1087456/000143774918018688/0001437749-18-018688-index.htm)
# Deal with statements only report income Q4 statement items full-year:
#   (https://www.sec.gov/Archives/edgar/data/740971/000074097117000007/0000740971-17-000007-index.htm)
# Deal with statements that have multiple FPs in a table, but the header is shared:
#   (https://www.sec.gov/Archives/edgar/data/714562/000110465911057065/a11-28324_1ex99d1.htm)
# Separate IS and BS items and tolerate different fiscal periods for each.
# Record all periods reported, for intra-report comparison.
# Factor tables into something more configurable, to allow for cik overrides without changing code.

logger = init_logging(__name__)

"""
Top-level module for loading new filings into the database.
"""


def _to_filing_df(cik: str, filing: Filing, report: Report, item_df: pd.DataFrame) -> pd.DataFrame:
    """ Adds columns to the item_df produced by items_from_tables for a particular filing."""

    def item_fpe_offset(item_quarter: int) -> pd.DateOffset:
        months = 3 * (4 - item_quarter) if item_quarter != 4 else 12
        return pd.DateOffset(months=months)

    return item_df.assign(
        cik=cik,
        filing_date=filing.date,
        filing_type=filing.type,
        filing_href=filing.href,
        fiscal_period=item_df.fiscal_period.str.replace(r'\d+QTD', str(report.fiscal_period - 1)),
        fiscal_year=lambda x: x.fiscal_period.str[:4],
        fiscal_quarter=lambda x: x.fiscal_period.str[-1:],
        fpe_date=lambda x: report.fye_date - x.fiscal_quarter.map(lambda q: item_fpe_offset((int(q)))),
        is_overridden=False
    ).loc[:, [c.name for c in prelim_statement_table.columns]]


def extract_prelim_statement(cik: str, filing: Filing, items: List[PrelimItem] = None) -> pd.DataFrame:
    """ The complete end-to-end extraction for a particular filing. """
    if filing.type.upper() != '8-K':
        return pd.DataFrame()

    report = query_edgar_for_submission_text(filing.href)
    submission = load_submission(report.href)
    item_df = items_from_tables(parse_tables(submission), items=items)
    return _to_filing_df(cik, filing, report, item_df) if not item_df.empty else item_df


def extract_prelim_statements(cik: str, start: date = None, end: date = None,
                              items: List[PrelimItem] = None) -> pd.DataFrame:
    """The complete end-to-end extraction for a time series of filings. """
    filings = query_edgar_for_filings(cik, "8-K", start=start, end=end, require_xbrl=False)
    dfs = [
        extract_prelim_statement(cik, filing)
        for filing in filings
        for item_df in [extract_prelim_statement(cik, filing, items)]
        if not item_df.empty
    ]
    return pd.concat(dfs, sort=False) if dfs else pd.DataFrame()


def _query_prelims(*clauses, conn: Connection = prelim_engine) -> pd.DataFrame:
    """Queries the statements table for those items that match the supplied clauses, and chooses the value with the
    highest rank."""
    df = pd.read_sql(
        prelim_statement_table.select().where(and_(*clauses)), conn
    )
    return df[df.item_value.notna()] \
        .groupby('filing_date') \
        .apply(choose_item_by_rank) \
        .droplevel(0) if not df.empty else pd.DataFrame()


def query_prelims(cik: str, conn: Connection = prelim_engine) -> pd.DataFrame:
    """Queries items for the specified CIK."""
    return _query_prelims(prelim_statement_table.c.cik == cik, conn=conn)


def query_prelims_for_override(cik: str, filing_date: Union[date, str] = None, item: str = None,
                               items: Iterable[PrelimItem] = None,
                               conn: Connection = prelim_engine) -> qgrid.QgridWidget:
    """Produces a QgridWidget where changes to the grid will apply overrides to the modified items."""
    if items is None:
        items = prelim_items

    clauses = [prelim_statement_table.c.cik == cik]
    if filing_date:
        clauses.append(prelim_statement_table.c.filing_date == filing_date)
    if item:
        clauses.append(prelim_statement_table.c.item == item)

    index_columns = ['filing_date', 'item']
    override_columns = ['fpe_date', 'fiscal_year', 'fiscal_quarter', 'fiscal_period', 'item_value']
    query_df = _query_prelims(*clauses, conn=conn)

    if query_df.empty:
        if filing_date:
            rows = [
                {'cik': cik, 'filing_date': filing_date, 'filing_type': '8-K', 'filing_href': 'Unknown', 'item': i}
                for i in ([item] if item else [i.name for i in items if i.rank == 0])
            ]
            query_df = pd.DataFrame(rows).assign(**{c: None for c in override_columns})

    original_df = query_df.set_index(index_columns)
    qgrid_widget = qgrid.show_grid(original_df.loc[:, override_columns])

    def save():
        changed_df = qgrid_widget.get_changed_df()
        changed_rows = reduce(lambda x, y: x | y, (changed_df[col] != original_df[col] for col in override_columns))
        override_df = original_df. \
            drop(override_columns, axis=1). \
            join(changed_df[changed_rows], how="inner"). \
            reset_index()
        save_overrides(override_df, conn=conn)
        return override_df

    qgrid_widget.save = save
    return qgrid_widget


def summarize_prelims(*ciks, items: List[PrelimItem] = None, conn: Connection = prelim_engine) -> pd.DataFrame:
    """Produces a summary quality report for a collection of CIKs."""
    summary_dfs = []
    if items is None:
        items = prelim_items

    for cik in ciks:
        prelim_df = query_prelims(cik, conn)
        if prelim_df.empty:
            continue

        validation_df = validate_prelims(prelim_df, items)
        cik_df = query_cik(cik).set_index('cik').loc[:, ['company_name', 'ticker']]

        if validation_df.empty:
            validation_summary_df = pd.DataFrame([
                {'cik': cik, 'item': i.name, 'missing': 0, 'duplicate': 0, 'outlier': 0} for i in items if i.rank == 0
            ]).set_index(['cik', 'item'])
        else:
            validation_summary_df = (
                validation_df[validation_df.msg_type.isin({'missing', 'duplicate', 'outlier'})]
                    .groupby(['cik', 'item', 'msg_type'])
                    .count()
                    .loc[:, 'message']
                    .unstack()
            )
        prelim_grouped = (
            prelim_df.loc[:, ['cik', 'filing_date', 'fiscal_period', 'item']]
                .groupby(['cik', 'item'])
        )
        prelim_summary_df = pd.concat([
            prelim_grouped.agg({'fiscal_period': 'count'}).rename({'fiscal_period': 'count'}, axis=1),
            prelim_grouped.agg({'fiscal_period': 'min'}).rename({'fiscal_period': 'start'}, axis=1),
            prelim_grouped.agg({'fiscal_period': 'max'}).rename({'fiscal_period': 'end'}, axis=1)
        ], axis=1)

        for v in {'missing', 'duplicate', 'outlier'}:
            if v not in validation_summary_df.columns:
                validation_summary_df = validation_summary_df.assign(**{v: 0.})

        for i in items:
            if i.name not in prelim_summary_df.index.levels[1]:
                prelim_summary_df.loc[(cik, i.name), ['count', 'start', 'end']] = [0, '-', '-']
                validation_summary_df.loc[(cik, i.name), 'missing'] = prelim_summary_df['count'].max()

        summary_dfs.append(pd.concat([validation_summary_df, prelim_summary_df], axis=1).join(cik_df, on='cik'))

    return (
        pd.concat(summary_dfs, sort=True)
            .reset_index()
            .set_index(['cik', 'company_name', 'ticker', 'item'])
            .sort_index()
            .loc[:, ['count', 'missing', 'duplicate', 'outlier', 'start', 'end']]
            .fillna(0)
    ) if summary_dfs else pd.DataFrame()


def is_prelim_statement_loaded(conn: Connection, cik: str, filing: Filing) -> bool:
    res = conn.execute(
        text("""select count(*) from prelim_statement 
                where cik = :cik and filing_date = :filing_date and 
                filing_type = :filing_type and filing_href = :filing_href""").bindparams(
            cik=cik, filing_date=filing.date, filing_type=filing.type, filing_href=filing.href))
    return res.fetchone()[0] > 0


def prelim_last_updated(conn: Connection, cik: str) -> date:
    res = conn.execute(text("select max(filing_date) from prelim_statement where cik = :cik").bindparams(cik=cik))
    rows = res.fetchone()
    return rows[0] if rows else date(2002, 6, 30)


class FilingTable(object):
    def __init__(self, filings: pd.DataFrame):
        self.filings = filings

    def contains(self, cik: str, filing: Filing):
        key = (cik, filing.date, filing.type, filing.href)
        return key in self.filings.index

    def is_prelim(self, cik: str, filing: Filing):
        key = (cik, filing.date, filing.type, filing.href)
        return self.filings.loc[key, :].iloc[0]

    def insert(self, cik: str, filing: Filing, is_prelim: bool, conn: Connection = prelim_engine):
        if not self.contains(cik, filing):
            stmt = prelim_filing_table.insert().values(
                cik=cik, filing_date=filing.date, filing_type=filing.type, filing_href=filing.href, is_prelim=is_prelim)
            conn.execute(stmt)

    def prelim_keys(self):
        return self.filings[self.filings.is_prelim].index.values

    @staticmethod
    def from_query(cik: str, start: date = None, end: date = None, conn: Connection = prelim_engine):
        query = prelim_filing_table.select().where(and_(
            prelim_filing_table.c.cik == cik,
            between(prelim_filing_table.c.filing_date, start if start else PRELIM_START, end if end else EOT)))

        return FilingTable(pd.read_sql(query, conn).set_index(keys=[c.name for c in prelim_core_columns]))


def load_prelim_statements(cik: str, start: date = None, end: date = None, reload: bool = False,
                           items: List[PrelimItem] = None, conn: Connection = prelim_engine,
                           fail_on_exception: bool = True) -> bool:
    logger.info(f"Loading preliminary statements for {cik}.")

    if reload:
        delete_start = start if start else PRELIM_START
        logger.info(f"Deleting old preliminary statements for {cik}.")
        conn.execute(prelim_statement_table.delete().where(and_(
            prelim_statement_table.c.cik == cik,
            prelim_statement_table.c.is_overridden == False,
            between(prelim_statement_table.c.filing_date, delete_start, end))))

    if start is None:
        start = prelim_last_updated(conn, cik)

    if end and start >= end:
        return False

    filings = query_edgar_for_filings(cik, "8-K", start=start, end=end, require_xbrl=False)
    if not filings:
        return False

    filing_table = FilingTable.from_query(cik, start, end, conn)

    loaded = False
    for filing in sorted(filings, key=attrgetter('date')):
        if filing_table.contains(cik, filing) and not filing_table.is_prelim(cik, filing):
            continue

        with conn.begin() as c:
            if not is_prelim_statement_loaded(c, cik=cik, filing=filing):
                try:
                    item_df = extract_prelim_statement(cik, filing, items)
                except Exception as e:
                    logger.error("Failure loading", filing, str(e))
                    if fail_on_exception:
                        raise e
                    else:
                        item_df = pd.DataFrame()

                is_prelim = not item_df.empty
                if is_prelim:
                    logger.info(f"Loading filing: {filing}.")
                    item_df.to_sql(prelim_statement_table.name, c, if_exists='append', index=False)
                    loaded = True

                filing_table.insert(cik, filing, is_prelim, conn)
    return loaded


def save_overrides(filing_df: pd.DataFrame, conn: Connection = prelim_engine):
    if filing_df.empty:
        return

    key_columns = [c.name for c in prelim_statement_table.columns if c.primary_key]

    with conn.begin() as c:
        logger.info("Deleting overridden filings")
        for key_values, _ in filing_df.groupby(key_columns):
            conn.execute(prelim_statement_table.delete().where(and_(
                prelim_statement_table.columns[k] == translate_to_persistable(v) for k, v in
                zip(key_columns, key_values))
            ))

        logger.info("Saving overrides")
        filing_df. \
            assign(is_overridden=True). \
            to_sql(prelim_statement_table.name, c, if_exists='append', index=False)


def discard_prelim(cik: str, filing_date: date, conn: Connection = prelim_engine):
    with conn.begin() as c:
        c.execute(prelim_statement_table.delete().where(and_(
            prelim_statement_table.c.cik == cik,
            prelim_statement_table.c.filing_date == filing_date)))

        c.execute(prelim_filing_table.update().values(is_prelim=False).where(and_(
            prelim_filing_table.c.cik == cik,
            prelim_filing_table.c.filing_date == filing_date)))


def force_reload_prelim(cik: str, filing_date: date, delete_filings=False, conn: Connection = prelim_engine):
    if delete_filings:
        with conn.begin() as c:
            c.execute(prelim_filing_table.delete().where(and_(
                prelim_filing_table.c.cik == cik,
                prelim_filing_table.c.filing_date == filing_date)))

    load_prelim_statements(cik, start=filing_date - timedelta(days=1), end=filing_date, reload=True)


def force_reload_prelim_between(cik: str, start: date, end: date, delete_filings=False,
                                conn: Connection = prelim_engine):
    if delete_filings:
        with conn.begin() as c:
            c.execute(prelim_filing_table.delete().where(and_(
                prelim_filing_table.c.cik == cik,
                between(prelim_filing_table.c.filing_date, start, end))))

    load_prelim_statements(cik, start=start - timedelta(days=1), end=end, reload=True)


def run_quality_report(cik: str, regen: bool = False, convert_to_html: bool = False):
    nb_file = f'../out/notebooks/{cik}.ipynb'
    if not regen and Path(nb_file).exists():
        logger.info(f"Notebook exists for {cik}. Skipping.")
        return

    pm.execute_notebook(
        'resources/edgar_prelim_quality.ipynb',
        nb_file,
        parameters={'cik': cik}
    )

    if convert_to_html:
        args = [
            "--Application.log_level=ERROR",
            "--TemplateExporter.exclude_input=True",
            "--output-dir=static/quality/",
            nb_file
        ]
        NbConvertApp.launch_instance(args)


def query_ciks_with_statements(conn: Connection = prelim_engine):
    return pd.read_sql(
        """select * from cik c 
        where exists (select 1 from prelim_statement s where s.cik = c.cik) 
        order by c.cik asc""", conn)


def generate_quality_reports(conn: Connection = prelim_engine, regen: bool = False):
    cik_df = query_ciks_with_statements(conn)
    for i, row in enumerate(cik_df.itertuples(index=False), start=1):
        logger.info(f'Generating report for {row.cik} ({i}/{len(cik_df)})')
        run_quality_report(row.cik, regen=regen, convert_to_html=True)


def update_database(to: date = datetime.now().date(),
                    num_to_load=None,
                    conn: Connection = prelim_engine):
    cik_df = pd.read_sql("select * from cik c order by c.cik desc", conn)

    loaded = 0
    for i, c in enumerate(cik_df.itertuples(index=False), start=1):
        logger.info(c)
        if load_prelim_statements(c.cik, start=PRELIM_START, end=to, fail_on_exception=False, reload=False):
            run_quality_report(c.cik)
            loaded += 1
            logger.info(f"{loaded} names loaded")
            if loaded == num_to_load:
                return


if __name__ == '__main__':
    # update_database()
    generate_quality_reports()

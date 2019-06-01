import os
from datetime import date

import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, String, Date, Numeric, text, Boolean
# noinspection PyProtectedMember
from sqlalchemy.engine import Connection

PRELIM_START = date(2002, 6, 1)
EOT = date(2100, 1, 1)

connection_string = os.environ.get("DB_URL", 'postgresql+pg8000://postgres:admin@localhost/edgar_prelim')
prelim_engine = create_engine(connection_string, echo=False)
prelim_metadata = MetaData()

# The core key columns of the filing and statement table. Uniquely identifies a filing.
prelim_core_columns = [
    Column('cik', String(255), primary_key=True),
    Column('filing_date', Date, primary_key=True),
    Column('filing_type', String(255), primary_key=True),
    Column('filing_href', String(255), primary_key=True)
]

# The table of CIKs for companies whose prelims we're loading.
prelim_cik_table = Table(
    'cik', prelim_metadata,
    Column('cik', String(255), primary_key=True),
    Column('sic', String(255)),
    Column('sic_description', String(255)),
    Column('company_name', String(255)),
    Column('ticker', String(255), nullable=True)
)

# Table that records the filings that we have visited and whether they were identified as a prelim.
prelim_filing_table = Table(
    'prelim_filing', prelim_metadata,
    *([
          Column(c.name, c.type, primary_key=c.primary_key) for c in prelim_core_columns
      ] + [
          Column('is_prelim', Boolean),
      ])
)

# Table that records to most recent item value for each preliminary financial statement.
prelim_statement_table = Table(
    'prelim_statement', prelim_metadata,
    *([
          Column(c.name, c.type, primary_key=c.primary_key) for c in prelim_core_columns
      ] + [
          Column('fpe_date', Date),
          Column('fiscal_year', Numeric(4, 0)),
          Column('fiscal_quarter', Numeric(1, 0)),
          Column('fiscal_period', String(10)),
          Column('item', String(50), primary_key=True),
          Column('item_value', Numeric(20, 5)),
          Column('item_rank', Numeric(2, 0)),
          Column('table_rank', Numeric(2, 0)),
          Column('src_table', String(1024)),
          Column('src_row', String(1024)),
          Column('src_column', String(1024)),
          Column('src_value', String(1024)),
          Column('src_units', String(1024)),
          Column('is_overridden', Boolean),
      ])
)


def translate_to_persistable(value):
    """Translates a pd.DataFrame value into a value friendly to SQLAlchemy."""
    if type(value) is pd.Timestamp:
        return value.date()
    elif pd.isna(value):
        return None
    else:
        return value


def query_cik(cik: str, conn: Connection = prelim_engine) -> pd.DataFrame:
    return pd.read_sql(text("select * from cik where cik = :cik").bindparams(cik=cik), conn)


def save_ciks(conn: Connection = prelim_engine):
    """Loads the cik table from the csv file in the resources directory."""
    df = pd.read_csv("resources/cik.csv", converters={col.name: str for col in prelim_cik_table.columns})
    with conn.begin() as c:
        c.execute('truncate table cik')
        df.to_sql(prelim_cik_table.name, c, if_exists='append', index=False)


if __name__ == '__main__':
    prelim_metadata.create_all(prelim_engine, checkfirst=True)
    save_ciks()


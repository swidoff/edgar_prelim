import pytest

from edgar_query import *


# noinspection PyPep8Naming
@pytest.fixture()
def IBM_10K_Filings():
    return [
        Filing(date=date(2018, 2, 27),
               href='https://www.sec.gov/Archives/edgar/data/51143/000104746918001117/0001047469-18-001117-index.htm',
               type='10-K'),
        Filing(date=date(2017, 2, 28),
               href='https://www.sec.gov/Archives/edgar/data/51143/000104746917001061/0001047469-17-001061-index.htm',
               type='10-K'),
        Filing(date=date(2016, 2, 23),
               href='https://www.sec.gov/Archives/edgar/data/51143/000104746916010329/0001047469-16-010329-index.htm',
               type='10-K'),
        Filing(date=date(2015, 2, 24),
               href='https://www.sec.gov/Archives/edgar/data/51143/000104746915001106/0001047469-15-001106-index.htm',
               type='10-K'),
        Filing(date=date(2014, 2, 25),
               href='https://www.sec.gov/Archives/edgar/data/51143/000104746914001302/0001047469-14-001302-index.htm',
               type='10-K'),
        Filing(date=date(2013, 2, 26),
               href='https://www.sec.gov/Archives/edgar/data/51143/000104746913001698/0001047469-13-001698-index.htm',
               type='10-K'),
        Filing(date=date(2012, 2, 28),
               href='https://www.sec.gov/Archives/edgar/data/51143/000104746912001742/0001047469-12-001742-index.htm',
               type='10-K'),
        Filing(date=date(2011, 2, 22),
               href='https://www.sec.gov/Archives/edgar/data/51143/000104746911001117/0001047469-11-001117-index.htm',
               type='10-K'),
        Filing(date=date(2010, 2, 23),
               href='https://www.sec.gov/Archives/edgar/data/51143/000104746910001151/0001047469-10-001151-index.htm',
               type='10-K')
    ]


def test_query_for_company_info_positive():
    expected = CompanyInfo(cik='0000051143', sic='3570', sic_description='COMPUTER & OFFICE EQUIPMENT',
                           company_name='INTERNATIONAL BUSINESS MACHINES CORP')
    assert next(query_edgar_for_company_info('IBM')) == expected
    assert next(query_edgar_for_company_info('0000051143')) == expected


def test_query_for_company_info_negative():
    with pytest.raises(StopIteration):
        next(query_edgar_for_company_info('NOR'))

    with pytest.raises(StopIteration):
        next(query_edgar_for_company_info('9999999999'))


# noinspection PyPep8Naming
def test_collect_filings_single_page(IBM_10K_Filings):
    res = list(query_edgar_for_filings("IBM", "10-K", require_xbrl=True, end=date(2019, 1, 31)))
    assert res == IBM_10K_Filings


def test_query_edgar_for_filing_xbrl():
    # 1231 fiscal period: AMZN
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/1018724/000101872419000004/0001018724-19-000004-index.htm")
    assert Report(fpe_date=date(2018, 12, 31), fye_date=date(2018, 12, 31),
                  fiscal_period=FiscalPeriod(2018, 4),
                  href="https://www.sec.gov/Archives/edgar/data/1018724/000101872419000004/amzn-20181231.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/1018724/000101872418000159/0001018724-18-000159-index.htm")
    assert Report(fpe_date=date(2018, 9, 30), fye_date=date(2018, 12, 31),
                  fiscal_period=FiscalPeriod(2018, 3),
                  href="https://www.sec.gov/Archives/edgar/data/1018724/000101872418000159/amzn-20180930.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/1018724/000101872418000108/0001018724-18-000108-index.htm")
    assert Report(fpe_date=date(2018, 6, 30), fye_date=date(2018, 12, 31),
                  fiscal_period=FiscalPeriod(2018, 2),
                  href="https://www.sec.gov/Archives/edgar/data/1018724/000101872418000108/amzn-20180630.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/1018724/000101872418000072/0001018724-18-000072-index.htm")
    assert Report(fpe_date=date(2018, 3, 31), fye_date=date(2018, 12, 31),
                  fiscal_period=FiscalPeriod(2018, 1),
                  href="https://www.sec.gov/Archives/edgar/data/1018724/000101872418000072/amzn-20180331.xml") == e

    # 10128 fiscal period: FiscalPeriod(AMAT, edgar),
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/6951/000000695119000008/0000006951-19-000008-index.htm")
    assert Report(fpe_date=date(2019, 1, 27), fye_date=date(2019, 10, 28),
                  fiscal_period=FiscalPeriod(2019, 1),
                  href="https://www.sec.gov/Archives/edgar/data/6951/000000695119000008/amat-20190127.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/6951/000000695118000041/0000006951-18-000041-index.htm")
    assert Report(fpe_date=date(2018, 10, 28), fye_date=date(2018, 10, 28),
                  fiscal_period=FiscalPeriod(2018, 4),
                  href="https://www.sec.gov/Archives/edgar/data/6951/000000695118000041/amat-20181028.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/6951/000000695118000029/0000006951-18-000029-index.htm")
    assert Report(fpe_date=date(2018, 7, 29), fye_date=date(2018, 10, 30),
                  fiscal_period=FiscalPeriod(2018, 3),
                  href="https://www.sec.gov/Archives/edgar/data/6951/000000695118000029/amat-20180729.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/6951/000000695118000017/0000006951-18-000017-index.htm")
    assert Report(fpe_date=date(2018, 4, 29), fye_date=date(2018, 10, 30),
                  fiscal_period=FiscalPeriod(2018, 2),
                  href="https://www.sec.gov/Archives/edgar/data/6951/000000695118000017/amat-20180429.xml") == e

    # 0930 fiscal period: FiscalPeriod(AAPL, edgar),
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/320193/000032019319000010/0000320193-19-000010-index.htm")
    assert Report(fpe_date=date(2018, 12, 29), fye_date=date(2019, 9, 30),
                  fiscal_period=FiscalPeriod(2019, 1),
                  href="https://www.sec.gov/Archives/edgar/data/320193/000032019319000010/aapl-20181229.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/320193/000032019318000145/0000320193-18-000145-index.htm")
    assert Report(fpe_date=date(2018, 9, 29), fye_date=date(2018, 9, 29),
                  fiscal_period=FiscalPeriod(2018, 4),
                  href="https://www.sec.gov/Archives/edgar/data/320193/000032019318000145/aapl-20180929.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/320193/000032019318000100/0000320193-18-000100-index.htm")
    assert Report(fpe_date=date(2018, 6, 30), fye_date=date(2018, 9, 30),
                  fiscal_period=FiscalPeriod(2018, 3),
                  href="https://www.sec.gov/Archives/edgar/data/320193/000032019318000100/aapl-20180630.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/320193/000032019318000070/0000320193-18-000070-index.htm")
    assert Report(fpe_date=date(2018, 3, 31), fye_date=date(2018, 9, 30),
                  fiscal_period=FiscalPeriod(2018, 2),
                  href="https://www.sec.gov/Archives/edgar/data/320193/000032019318000070/aapl-20180331.xml") == e

    # 0630 fiscal period: FiscalPeriod(MSFT, edgar),
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/789019/000156459019001392/0001564590-19-001392-index.htm")
    assert Report(fpe_date=date(2018, 12, 31), fye_date=date(2019, 6, 30),
                  fiscal_period=FiscalPeriod(2019, 2),
                  href="https://www.sec.gov/Archives/edgar/data/789019/000156459019001392/msft-20181231.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/789019/000156459018024893/0001564590-18-024893-index.htm")
    assert Report(fpe_date=date(2018, 9, 30), fye_date=date(2019, 6, 30),
                  fiscal_period=FiscalPeriod(2019, 1),
                  href="https://www.sec.gov/Archives/edgar/data/789019/000156459018024893/msft-20180930.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/789019/000156459018019062/0001564590-18-019062-index.htm")
    assert Report(fpe_date=date(2018, 6, 30), fye_date=date(2018, 6, 30),
                  fiscal_period=FiscalPeriod(2018, 4),
                  href="https://www.sec.gov/Archives/edgar/data/789019/000156459018019062/msft-20180630.xml") == e
    e = query_edgar_for_filing_xbrl(

        "https://www.sec.gov/Archives/edgar/data/789019/000156459018009307/0001564590-18-009307-index.htm")
    assert Report(fpe_date=date(2018, 3, 31), fye_date=date(2018, 6, 30),
                  fiscal_period=FiscalPeriod(2018, 3),
                  href="https://www.sec.gov/Archives/edgar/data/789019/000156459018009307/msft-20180331.xml") == e

    # 0131 fiscal period: FiscalPeriod(TGT, edgar),
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/27419/000002741919000006/0000027419-19-000006-index.htm")
    assert Report(fpe_date=date(2019, 2, 2), fye_date=date(2019, 2, 2),
                  fiscal_period=FiscalPeriod(2018, 4),
                  href="https://www.sec.gov/Archives/edgar/data/27419/000002741919000006/tgt-20190202.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/27419/000002741918000036/0000027419-18-000036-index.htm")
    assert Report(fpe_date=date(2018, 11, 3), fye_date=date(2019, 1, 31),
                  fiscal_period=FiscalPeriod(2018, 3),
                  href="https://www.sec.gov/Archives/edgar/data/27419/000002741918000036/tgt-20181103.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/27419/000002741918000027/0000027419-18-000027-index.htm")
    assert Report(fpe_date=date(2018, 8, 4), fye_date=date(2019, 1, 31),
                  fiscal_period=FiscalPeriod(2018, 2),
                  href="https://www.sec.gov/Archives/edgar/data/27419/000002741918000027/tgt-20180804.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/27419/000002741918000018/0000027419-18-000018-index.htm")
    assert Report(fpe_date=date(2018, 5, 5), fye_date=date(2019, 1, 31),
                  fiscal_period=FiscalPeriod(2018, 1),
                  href="https://www.sec.gov/Archives/edgar/data/27419/000002741918000018/tgt-20180505.xml") == e

    # Missing INSTANCE
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/22356/000002235612000015/0000022356-12-000015-index.htm")
    assert Report(fpe_date=date(2011, 12, 31), fye_date=date(2011, 12, 31),
                  fiscal_period=FiscalPeriod(2011, 4),
                  href="https://www.sec.gov/Archives/edgar/data/22356/000002235612000015/cbsh-20111231.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/70858/000007085819000012/0000070858-19-000012-index.htm")
    assert Report(fpe_date=date(2018, 12, 31), fye_date=date(2018, 12, 31),
                  fiscal_period=FiscalPeriod(2018, 4),
                  href="https://www.sec.gov/Archives/edgar/data/70858/000007085819000012/bac-1231201810xk_htm.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/1028918/000102891816000161/0001028918-16-000161-index.htm")
    assert Report(fpe_date=date(2015, 12, 31), fye_date=date(2015, 12, 31),
                  fiscal_period=FiscalPeriod(2015, 4),
                  href="https://www.sec.gov/Archives/edgar/data/1028918/000102891816000161/ppbi-20151231.xml") == e
    e = query_edgar_for_filing_xbrl(
        "https://www.sec.gov/Archives/edgar/data/1028918/000102891816000183/0001028918-16-000183-index.htm")
    assert Report(fpe_date=date(2016, 3, 31), fye_date=date(2017, 2, 28),
                  fiscal_period=FiscalPeriod(2016, 1),
                  href="https://www.sec.gov/Archives/edgar/data/1028918/000102891816000183/ppbi-20160331.xml") == e


def test_fiscal_year_and_quarter_for_past_fiscal_year():
    assert FiscalPeriod.from_fpe_date(fye_date=date(2009, 12, 31), fpe_date=date(2008, 12, 31)) == FiscalPeriod(2008, 4)


def test_fiscal_period_math():
    assert (FiscalPeriod(2018, 1) - 0) == FiscalPeriod(2018, 1)
    assert (FiscalPeriod(2018, 1) - 1) == FiscalPeriod(2017, 4)
    assert (FiscalPeriod(2018, 1) - 2) == FiscalPeriod(2017, 3)
    assert (FiscalPeriod(2018, 1) - 3) == FiscalPeriod(2017, 2)
    assert (FiscalPeriod(2018, 1) - 4) == FiscalPeriod(2017, 1)
    assert (FiscalPeriod(2018, 1) - 5) == FiscalPeriod(2016, 4)
    assert (FiscalPeriod(2018, 1) + 5) == FiscalPeriod(2019, 2)
    assert (FiscalPeriod(2018, 1) + 4) == FiscalPeriod(2019, 1)
    assert (FiscalPeriod(2018, 1) + 3) == FiscalPeriod(2018, 4)
    assert (FiscalPeriod(2018, 1) + 2) == FiscalPeriod(2018, 3)
    assert (FiscalPeriod(2018, 1) + 1) == FiscalPeriod(2018, 2)
    assert (FiscalPeriod(2018, 1) + 0) == FiscalPeriod(2018, 1)

    assert (FiscalPeriod(2018, 2) - 0) == FiscalPeriod(2018, 2)
    assert (FiscalPeriod(2018, 2) - 1) == FiscalPeriod(2018, 1)
    assert (FiscalPeriod(2018, 2) - 2) == FiscalPeriod(2017, 4)
    assert (FiscalPeriod(2018, 2) - 3) == FiscalPeriod(2017, 3)
    assert (FiscalPeriod(2018, 2) - 4) == FiscalPeriod(2017, 2)
    assert (FiscalPeriod(2018, 2) - 5) == FiscalPeriod(2017, 1)
    assert (FiscalPeriod(2018, 2) + 5) == FiscalPeriod(2019, 3)
    assert (FiscalPeriod(2018, 2) + 4) == FiscalPeriod(2019, 2)
    assert (FiscalPeriod(2018, 2) + 3) == FiscalPeriod(2019, 1)
    assert (FiscalPeriod(2018, 2) + 2) == FiscalPeriod(2018, 4)
    assert (FiscalPeriod(2018, 2) + 1) == FiscalPeriod(2018, 3)
    assert (FiscalPeriod(2018, 2) + 0) == FiscalPeriod(2018, 2)

    assert (FiscalPeriod(2018, 3) - 0) == FiscalPeriod(2018, 3)
    assert (FiscalPeriod(2018, 3) - 1) == FiscalPeriod(2018, 2)
    assert (FiscalPeriod(2018, 3) - 2) == FiscalPeriod(2018, 1)
    assert (FiscalPeriod(2018, 3) - 3) == FiscalPeriod(2017, 4)
    assert (FiscalPeriod(2018, 3) - 4) == FiscalPeriod(2017, 3)
    assert (FiscalPeriod(2018, 3) - 5) == FiscalPeriod(2017, 2)
    assert (FiscalPeriod(2018, 3) + 5) == FiscalPeriod(2019, 4)
    assert (FiscalPeriod(2018, 3) + 4) == FiscalPeriod(2019, 3)
    assert (FiscalPeriod(2018, 3) + 3) == FiscalPeriod(2019, 2)
    assert (FiscalPeriod(2018, 3) + 2) == FiscalPeriod(2019, 1)
    assert (FiscalPeriod(2018, 3) + 1) == FiscalPeriod(2018, 4)
    assert (FiscalPeriod(2018, 3) + 0) == FiscalPeriod(2018, 3)

    assert (FiscalPeriod(2018, 4) - 0) == FiscalPeriod(2018, 4)
    assert (FiscalPeriod(2018, 4) - 1) == FiscalPeriod(2018, 3)
    assert (FiscalPeriod(2018, 4) - 2) == FiscalPeriod(2018, 2)
    assert (FiscalPeriod(2018, 4) - 3) == FiscalPeriod(2018, 1)
    assert (FiscalPeriod(2018, 4) - 4) == FiscalPeriod(2017, 4)
    assert (FiscalPeriod(2018, 4) - 5) == FiscalPeriod(2017, 3)
    assert (FiscalPeriod(2018, 4) + 5) == FiscalPeriod(2020, 1)
    assert (FiscalPeriod(2018, 4) + 4) == FiscalPeriod(2019, 4)
    assert (FiscalPeriod(2018, 4) + 3) == FiscalPeriod(2019, 3)
    assert (FiscalPeriod(2018, 4) + 2) == FiscalPeriod(2019, 2)
    assert (FiscalPeriod(2018, 4) + 1) == FiscalPeriod(2019, 1)
    assert (FiscalPeriod(2018, 4) + 0) == FiscalPeriod(2018, 4)

    assert FiscalPeriod(2018, 4) - FiscalPeriod(2018, 4) == 0
    assert FiscalPeriod(2018, 4) - FiscalPeriod(2018, 3) == 1
    assert FiscalPeriod(2018, 4) - FiscalPeriod(2018, 2) == 2
    assert FiscalPeriod(2018, 4) - FiscalPeriod(2018, 1) == 3
    assert FiscalPeriod(2018, 4) - FiscalPeriod(2017, 4) == 4
    assert FiscalPeriod(2018, 4) - FiscalPeriod(2017, 3) == 5

    assert FiscalPeriod(2018, 4) - FiscalPeriod(2020, 1) == -5
    assert FiscalPeriod(2018, 4) - FiscalPeriod(2019, 4) == -4
    assert FiscalPeriod(2018, 4) - FiscalPeriod(2019, 3) == -3
    assert FiscalPeriod(2018, 4) - FiscalPeriod(2019, 2) == -2
    assert FiscalPeriod(2018, 4) - FiscalPeriod(2019, 1) == -1
    assert FiscalPeriod(2018, 4) - FiscalPeriod(2018, 4) == 0

    assert FiscalPeriod(2019, 1) - FiscalPeriod(2018, 4) == 1

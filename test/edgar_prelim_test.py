from edgar_prelim.edgar_load import *
from edgar_query import *
from edgar_submission import *
# noinspection PyProtectedMember
from edgar_validate import _compress_consecutive_periods, _find_missing_periods, _find_duplicate_periods


def compare(cik: str, filing_date: date, items: list, values: list, fiscal_period: str):
    expected = pd.DataFrame({'item': items, 'item_value': values, 'fiscal_period': [fiscal_period] * len(items)}) \
        .set_index(['item']) \
        .sort_index()

    stmt_df = choose_item_by_rank(extract_prelim_statements(cik, start=filing_date, end=filing_date))
    actual = stmt_df.loc[:, ['item', 'item_value', 'fiscal_period']].set_index(['item']).sort_index()

    print(actual)
    pd.testing.assert_frame_equal(actual[actual.fiscal_period == fiscal_period], expected, check_names=False)


def test_parse_items_STI_20070719():
    compare('0000750556', date(2007, 7, 19),
            items=['net income', 'provision for loan losses', 'total revenue', 'net interest income',
                   'interest income', 'book value per share'],
            values=[6.814310e+08, 1.046800e+08, 2.374600e+09, 1.195284e+09, 2.543870e+09, 4.833000e+01],
            fiscal_period='2007Q2')


def test_parse_items_STI_20111021():
    compare('0000750556', date(2011, 10, 21),
            items=['net income', 'provision for loan losses', 'total revenue', 'net interest income',
                   'interest income', 'book value per share'],
            values=[2.150000e+08, 3.470000e+08, 2.196000e+09, 1.263000e+09, 1.538000e+09, 3.729000e+01],
            fiscal_period='2011Q3')


def test_parse_items_STI_20090122():
    compare('0000750556', date(2009, 1, 22),
            items=['net income', 'provision for loan losses', 'total revenue', 'net interest income',
                   'interest income', 'book value per share'],
            values=[-3.47587e+08, 9.624940e+08, 1.926400e+09, 1.176860e+09, 1.985371e+09, 4.842000e+01],
            fiscal_period='2008Q4')


def test_parse_items_STI_20111027():
    compare('0000750556', date(2011, 10, 27),
            items=['net income', 'provision for loan losses', 'total revenue', 'net interest income',
                   'interest income', 'book value per share'],
            values=[2.150000e+08, 3.470000e+08, 2.196000e+09, 1.263000e+09, 1.538000e+09, 3.729000e+01],
            fiscal_period='2011Q3')


def test_parse_items_STI_20190418():
    compare('0000750556', date(2019, 4, 18),
            items=['net income', 'provision for loan losses', 'total revenue', 'net interest income',
                   'interest income', 'book value per share'],
            values=[5.800000e+08, 1.530000e+08, 2.328000e+09, 1.544000e+09, 1.987000e+09, 5.115000e+01],
            fiscal_period='2019Q1')


def test_parse_items_STI_20100421():
    compare('0000750556', date(2010, 4, 21),
            items=['net income', 'provision for loan losses', 'total revenue', 'net interest income',
                   'interest income', 'book value per share'],
            values=[-160814000.0, 8.616090e+08, 1.900000e+09, 1.171437e+09, 1.573686e+09, 3.540000e+01],
            fiscal_period='2010Q1')


def test_parse_items_C_20190415():
    compare('0000831001', date(2019, 4, 15),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'interest income', 'net interest income'],
            values=[4.710000e+09, 1.944000e+09, 1.857600e+10, 7.709000e+01, 1.907600e+10, 1.175900e+10],
            fiscal_period='2019Q1')


def test_parse_items_C_20190114():
    compare('0000831001', date(2019, 1, 14),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'interest income', 'net interest income'],
            values=[4.313000e+09, 1.850000e+09, 1.712400e+10, 7.505000e+01, 1.877600e+10, 1.192300e+10],
            fiscal_period='2018Q4')


def test_parse_items_C_20071015():
    compare('0000831001', date(2007, 10, 15),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'interest income', 'net interest income'],
            values=[2.378000e+09, 4.776000e+09, 2.266300e+10, 2.554000e+01, 3.296100e+10, 1.215700e+10],
            fiscal_period='2007Q3')


def test_parse_items_C_20070119():
    compare('0000831001', date(2007, 1, 19),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'interest income', 'net interest income'],
            values=[5.129000e+09, 2.113000e+09, 2.382800e+10, 2.418000e+01, 2.625700e+10, 1.003900e+10],
            fiscal_period='2006Q4')


def test_parse_items_C_20050415():
    compare('0000831001', date(2005, 4, 15),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'interest income'],
            values=[5.441000e+09, 1.813000e+09, 2.896100e+10, 2.103000e+01, 6.262000e+09],
            fiscal_period='2005Q1')


def test_parse_items_C_20080115():
    compare('0000831001', date(2008, 1, 15),

            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'interest income', 'net interest income'],
            values=[-9.833000e+09, 7.422000e+09, 7.216000e+09, 2.274000e+01, 3.261800e+10, 1.262500e+10],
            fiscal_period='2007Q4')


def test_parse_items_BAC_20190416():
    compare('0000070858', date(2019, 4, 16),
            items=['net income', 'net interest income', 'provision for loan losses', 'total revenue',
                   'book value per share', 'interest income'],
            values=[7.311000e+09, 1.237500e+10, 1.013000e+09, 2.300400e+10, 2.557000e+01, 1.817000e+10],
            fiscal_period='2019Q1')


def test_parse_items_BAC_20190116():
    compare('0000070858', date(2019, 1, 16),
            items=['net income', 'net interest income', 'provision for loan losses', 'total revenue',
                   'book value per share', 'interest income'],
            values=[7.278000e+09, 1.230400e+10, 9.050000e+08, 2.273600e+10, 2.513000e+01, 1.783600e+10],
            fiscal_period='2018Q4')


# Re-classification
# def test_parse_items_BAC_20161101():
#     compare('0000070858', date(2016, 11, 1),
#             items=['net income', 'net interest income', 'provision for loan losses', 'total revenue',
#                    'interest income'],
#             values=[1.583600e+10, 3.984700e+10, 3.161000e+09, 8.385400e+10, 4.950700e+10],
#             fiscal_period='2015Q4')


# Re-assignment
# def test_parse_items_BAC_20160712():
#     compare('0000070858', date(2016, 7, 12),
#             items=['net income', 'net interest income', 'provision for loan losses', 'total revenue'],
#             values=[2.680000e+09, 9.386000e+09, 9.970000e+08, 1.972700e+10],
#             fiscal_period='2016Q1')


def test_parse_items_BAC_20160119():
    compare('0000070858', date(2016, 1, 19),
            items=['net income', 'net interest income', 'provision for loan losses',
                   'total revenue', 'book value per share', 'interest income'],
            values=[3.336000e+09, 9.801000e+09, 8.100000e+08, 1.952800e+10, 2.254000e+01, 1.269800e+10],
            fiscal_period='2015Q4')


def test_parse_items_BAC_20151014():
    compare('0000070858', date(2015, 10, 14),
            items=['net income', 'net interest income', 'provision for loan losses',
                   'total revenue', 'book value per share', 'interest income'],
            values=[4.508000e+09, 9.511000e+09, 8.060000e+08, 2.068200e+10, 2.241000e+01, 1.200700e+10],
            fiscal_period='2015Q3')


# Reclassification -- Exclude
# def test_parse_items_BAC_20060525():
#     compare('0000070858', date(2006, 5, 25),
#             items=['net income', 'net interest income', 'provision for loan losses',
#                    'total revenue', 'interest income'],
#             values=[1.646500e+10, 3.073700e+10, 4.014000e+09, 5.609100e+10, 5.862600e+10],
#             fiscal_period='2015Q3')


def test_parse_items_BAC_20100120():
    # Ordering of tables is messed up. Business segments come first.
    compare('0000070858', date(2010, 1, 20),
            items=['net income', 'net interest income', 'provision for loan losses',
                   'total revenue', 'book value per share', 'interest income'],
            values=[-1.940000e+08, 1.155900e+10, 1.011000e+10, 2.507600e+10, 2.148000e+01, 1.764500e+10],
            fiscal_period='2009Q4')


def test_parse_items_BAC_20021015():
    # Units not in table, but text above it.
    compare('0000070858', date(2002, 10, 15),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[2.235000e+09, 8.040000e+08, 8.522000e+09, 3.207000e+01, 5.302000e+09, 8.185000e+09],
            fiscal_period='2002Q3')


def test_parse_items_BAC_20040115():
    # Billions appears in text above table, confusing units
    compare('0000070858', date(2004, 1, 15),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[2.726000e+09, 5.830000e+08, 9.629000e+09, 3.326000e+01, 5.586000e+09, 8.068000e+09],
            fiscal_period='2003Q4')


def test_parse_items_JPM_20020719():
    compare('0000019617', date(2002, 7, 19),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[1.028000e+09, 8.210000e+08, 6.753000e+09, 2.093000e+01, 2.882000e+09, 6.498000e+09],
            fiscal_period='2002Q2')


def test_parse_items_JPM_20030124():
    compare('0000019617', date(2003, 1, 24),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[-3.870000e+08, 921000000.0, 6.574000e+09, 2.066000e+01, 2.981000e+09, 6.184000e+09],
            fiscal_period='2002Q4')


def test_parse_items_JPM_20111013():
    compare('0000019617', date(2011, 10, 13),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[4.262000e+09, 2.411000e+09, 2.376300e+10, 4.593000e+01, 1.181700e+10, 1.516000e+10],
            fiscal_period='2011Q3')


def test_parse_items_JPM_20090115():
    compare('0000019617', date(2009, 1, 15),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[7.020000e+08, 7.313000e+09, 1.722600e+10, 3.615000e+01, 1.383200e+10, 2.163100e+10],
            fiscal_period='2008Q4')


def test_parse_items_JPM_20190412():
    compare('0000019617', date(2019, 4, 12),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[9.179000e+09, 1.495000e+09, 2.912300e+10, 7.178000e+01, 1.445300e+10, 2.189400e+10],
            fiscal_period='2019Q1')


def test_parse_items_JPM_20190115():
    compare('0000019617', date(2019, 1, 15),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[7.066000e+09, 1.548000e+09, 2.610900e+10, 7.035000e+01, 1.435400e+10, 2.103800e+10],
            fiscal_period='2018Q4')


def test_parse_items_JPM_20120113():
    compare('0000019617', date(2012, 1, 13),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[3.728000e+09, 2.184000e+09, 2.147100e+10, 4.659000e+01, 1.213100e+10, 1.505400e+10],
            fiscal_period='2011Q4')


def test_parse_items_WFC_20190412():
    compare('0000072971', date(2019, 4, 12),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[5.860000e+09, 8.450000e+08, 2.160900e+10, 3.901000e+01, 1.231100e+10, 1.700300e+10],
            fiscal_period='2019Q1')


def test_parse_items_WFC_20190115():
    compare('0000072971', date(2019, 1, 15),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[6.064000e+09, 5.210000e+08, 2.098000e+10, 3.806000e+01, 1.264400e+10, 1.692100e+10],
            fiscal_period='2018Q4')


def test_parse_items_WFC_2014014():
    compare('0000072971', date(2014, 10, 14),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[5.729000e+09, 3.680000e+08, 2.121300e+10, 3.155000e+01, 1.094100e+10, 1.196400e+10],
            fiscal_period='2014Q3')


def test_parse_items_WFC_20180112():
    compare('0000072971', date(2018, 1, 12),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[6.151000e+09, 6.510000e+08, 2.205000e+10, 3.744000e+01, 1.231300e+10, 1.495800e+10],
            fiscal_period='2017Q4')


def test_parse_items_GS_20190415():
    compare('0000886982', date(2019, 4, 15),
            items=['net income', 'provision for loan losses', 'total revenue', 'book value per share',
                   'net interest income', 'interest income'],
            values=[2251000000.0, 2.240000e+08, 8.807000e+09, 2.090700e+02, 1.218000e+09, 5.597000e+09],
            fiscal_period='2019Q1')


def test_parse_items_GS_20190116():
    compare('0000886982', date(2019, 1, 16),
            items=['net income', 'provision for loan losses', 'total revenue', 'net interest income',
                   'interest income'],
            values=[2.538000e+09, 2.220000e+08, 8.080000e+09, 9.910000e+08, 5.468000e+09],
            fiscal_period='2018Q4')


def test_parse_items_GS_20180717():
    compare('0000886982', date(2018, 7, 17),
            items=['net income', 'net interest income', 'interest income', 'total revenue'],
            values=[2.565000e+09, 1.002000e+09, 4.920000e+09, 9.402000e+09],
            fiscal_period='2018Q2')


def test_parse_items_COF_20190122():
    compare('0000927628', date(2019, 1, 22),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'total revenue'],
            values=[1.261000e+09, 5.820000e+09, 7.048000e+09, 1.638000e+09, 7.013000e+09],
            fiscal_period='2018Q4')


def test_parse_items_COF_20111020():
    compare('0000927628', date(2011, 10, 20),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'total revenue'],
            values=[8.130000e+08, 3.283000e+09, 3.835000e+09, 6.220000e+08, 4.154000e+09],
            fiscal_period='2011Q3')


def test_parse_items_COF_20071018():
    compare('0000927628', date(2007, 10, 18),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'total revenue'],
            values=[-8.165800e+07, 1.624474e+09, 2.766967e+09, 5.955340e+08, 3.774200e+09],
            fiscal_period='2007Q3')


def test_parse_items_COF_20090421():
    compare('0000927628', date(2009, 4, 21),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'total revenue'],
            values=[-1.118790e+08, 1.786751e+09, 2.648228e+09, 1.279137e+09, 2.877100e+09],
            fiscal_period='2009Q1')


def test_parse_items_COF_20060420():
    compare('0000927628', date(2006, 4, 20),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'total revenue', 'book value per share'],
            values=[8.833390e+08, 1.206877e+09, 1.878582e+09, 1.702700e+08, 3.065200e+09, 5.006000e+01],
            fiscal_period='2006Q1')


def test_parse_items_MS_20190417():
    compare('0000895421', date(2019, 4, 17),
            items=['net income', 'net interest income', 'interest income', 'total revenue', 'book value per share'],
            values=[2.468000e+09, 1.014000e+09, 4.290000e+09, 1.028600e+10, 4.283000e+01],
            fiscal_period='2019Q1')


def test_parse_items_MS_20150720():
    compare('0000895421', date(2015, 7, 20),
            items=['net income', 'net interest income', 'interest income', 'total revenue', 'book value per share'],
            values=[1.831000e+09, 6.980000e+08, 1.386000e+09, 9.743000e+09, 3.452000e+01],
            fiscal_period='2015Q2')


def test_parse_items_MS_20100120():
    compare('0000895421', date(2010, 1, 20),
            items=['net income', 'net interest income', 'interest income', 'total revenue', 'book value per share'],
            values=[7.700000e+08, 6.120000e+08, 1.802000e+09, 6.842000e+09, 2.726000e+01],
            fiscal_period='2009Q4')


def test_parse_items_USB_20190417():
    compare('0000036104', date(2019, 4, 17),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses', 'total revenue',
                   'book value per share'],
            values=[1.708000e+09, 3.259000e+09, 4.351000e+09, 3.770000e+08, 5.577000e+09, 2.881000e+01],
            fiscal_period='2019Q1')


def test_parse_items_USB_20180117():
    compare('0000036104', date(2018, 1, 17),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses', 'total revenue',
                   'book value per share'],
            values=[1.686000e+09, 3.144000e+09, 3.740000e+09, 3.350000e+08, 5.638000e+09, 2.634000e+01],
            fiscal_period='2017Q4')


def test_parse_items_USB_20110119():
    compare('0000036104', date(2011, 1, 19),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses', 'total revenue',
                   'book value per share'],
            values=[9.560000e+08, 2.446000e+09, 3.093000e+09, 9.120000e+08, 4.721000e+09, 1.436000e+01],
            fiscal_period='2010Q4')


def test_parse_items_USB_20050719():
    compare('0000036104', date(2005, 7, 19),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses', 'total revenue',
                   'book value per share'],
            values=[1.121000e+09, 1.754000e+09, 2.565000e+09, 1.440000e+08, 3.302000e+09, 1.088000e+01],
            fiscal_period='2005Q2')


def test_parse_items_PNC_20120118():
    compare('0000713676', date(2012, 1, 18),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses', 'total revenue',
                   'book value per share'],
            values=[4.930000e+08, 2.199000e+09, 2.534000e+09, 1.900000e+08, 3.549000e+09, 6.152000e+01],
            fiscal_period='2011Q4')


def test_parse_items_PNC_20070719():
    compare('0000713676', date(2007, 7, 19),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses', 'total revenue',
                   'book value per share'],
            values=[4.230000e+08, 7.380000e+08, 1.554000e+09, 5.400000e+07, 1.721000e+09, 4.236000e+01],
            fiscal_period='2007Q2')


def test_parse_items_BK_20190417():
    compare('0001390777', date(2019, 4, 17),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses', 'total revenue',
                   'book value per share'],
            values=[9.560000e+08, 8.410000e+08, 1.920000e+09, 7.000000e+06, 3.899000e+09, 3.936000e+01],
            fiscal_period='2019Q1')


def test_parse_items_BK_20150721():
    compare('0001390777', date(2015, 7, 21),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses', 'total revenue',
                   'book value per share'],
            values=[8.890000e+08, 7.790000e+08, 8.470000e+08, -6.000000e+06, 3.886000e+09, 3.228000e+01],
            fiscal_period='2015Q2')


def test_parse_items_BK_20140422():
    compare('0001390777', date(2014, 4, 22),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses', 'total revenue',
                   'book value per share'],
            values=[6.940000e+08, 7.280000e+08, 8.120000e+08, -1.800000e+07, 3.647000e+09, 3.194000e+01],
            fiscal_period='2014Q1')


def test_parse_items_BK_20101019():
    compare('0001390777', date(2010, 10, 19),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses', 'total revenue',
                   'book value per share'],
            values=[6.110000e+08, 7.180000e+08, 8.750000e+08, -2.200000e+07, 3.429000e+09, 2.592000e+01],
            fiscal_period='2010Q3')


def test_parse_items_SCHW_20190415():
    compare('0000316709', date(2019, 4, 15),
            items=['net income', 'net interest income', 'interest income', 'total revenue'],
            values=[9.640000e+08, 1.681000e+09, 1.998000e+09, 2.723000e+09],
            fiscal_period='2019Q1')


def test_parse_items_SCHW_20160415():
    compare('0000316709', date(2016, 4, 15),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'total revenue'],
            values=[4.120000e+08, 7.720000e+08, 8.100000e+08, -2.000000e+06, 1.764000e+09],
            fiscal_period='2016Q1')


def test_parse_items_STT_20030415():
    compare('0000093751', date(2003, 4, 15),
            items=['net income', 'net interest income', 'interest income', 'total revenue'],
            values=[9.600000e+07, 2.040000e+08, 3.970000e+08, 1.020000e+09],
            fiscal_period='2003Q1')


def test_parse_items_STT_20160127():
    compare('0000093751', date(2016, 1, 27),
            items=['net income', 'net interest income', 'interest income', 'total revenue',
                   'provision for loan losses'],
            values=[5.760000e+08, 4.940000e+08, 6.030000e+08, 2.538000e+09, 1.000000e+06],
            fiscal_period='2015Q4')


def test_parse_items_STT_20140124():
    compare('0000093751', date(2014, 1, 24),
            items=['net income', 'net interest income', 'interest income', 'total revenue',
                   'provision for loan losses'],
            values=[5.530000e+08, 5.850000e+08, 6.840000e+08, 2.464000e+09, 6.000000e+06],
            fiscal_period='2013Q4')


def test_parse_items_STT_20121016():
    compare('0000093751', date(2012, 10, 16),
            items=['net income', 'net interest income', 'interest income', 'total revenue',
                   'provision for loan losses'],
            values=[6.740000e+08, 6.190000e+08, 7.300000e+08, 2.356000e+09, 0],
            fiscal_period='2012Q3')


def test_parse_items_STT_20120717():
    compare('0000093751', date(2012, 7, 17),
            items=['net income', 'net interest income', 'interest income', 'total revenue',
                   'provision for loan losses'],
            values=[4.900000e+08, 6.720000e+08, 7.860000e+08, 2.423000e+09, -1.000000e+06],
            fiscal_period='2012Q2')


def test_parse_items_STT_20081015():
    compare('0000093751', date(2008, 10, 15),
            items=['net income', 'net interest income', 'interest income', 'total revenue',
                   'provision for loan losses'],
            values=[4.770000e+08, 5.250000e+08, 1.027000e+09, 2.771000e+09, -0],
            fiscal_period='2008Q3')


def test_parse_items_STT_20080415():
    compare('0000093751', date(2008, 4, 15),
            items=['net income', 'net interest income', 'interest income', 'total revenue',
                   'provision for loan losses'],
            values=[5.300000e+08, 6.250000e+08, 1.288000e+09, 2.577000e+09, 0],
            fiscal_period='2008Q1')


def test_parse_items_USBH_20190424():
    compare('0000883948', date(2019, 4, 24),
            items=['net income', 'net interest income', 'interest income',
                   'provision for loan losses', 'book value per share'],
            values=[3.563100e+07, 1.275470e+08, 1.656520e+08, 3.792000e+06, 3.016000e+01],
            fiscal_period='2019Q1')


def test_parse_items_FBNK_20140130():
    compare('0001511198', date(2014, 1, 30),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses'],
            values=[1064000.0, 14222000.0, 16697000.0, 660000.0],
            fiscal_period='2013Q4')


def test_parse_items_BKU_20190424():
    compare('0001504008', date(2019, 4, 24),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses'],
            values=[65972000.0, 180620000.0, 321829000.0, 10281000.0],
            fiscal_period='2019Q1')


def test_parse_items_BKU_20120125():
    compare('0001504008', date(2012, 1, 25),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses'],
            values=[41280000.0, 136701000.0, 174639000.0, 4012000.0],
            fiscal_period='2011Q4')


def test_parse_items_UBNK_20190416():
    compare('0001501364', date(2019, 4, 16),
            items=['net income', 'net interest income', 'interest income', 'total revenue',
                   'provision for loan losses'],
            values=[12657000.0, 46937000.0, 73214000.0, 55917000.0, 2043000.0],
            fiscal_period='2019Q1')


def test_parse_items_STBZ_20130425():
    compare('0001497275', date(2013, 4, 25),
            items=['net income', 'net interest income', 'book value per share', 'provision for loan losses'],
            values=[-1156000.00, 35461000.00, 13.38, 350000.00],
            fiscal_period='2013Q1')


def test_parse_items_LTXB_20190423():
    compare('0001487052', date(2019, 4, 23),
            items=['net income', 'net interest income', 'book value per share', 'provision for loan losses',
                   'interest income'],
            values=[29080000.00, 81164000.00, 23.02, 9800000.00, 1.061040e+08],
            fiscal_period='2019Q1')


def test_parse_items_ANCB_21081029():
    compare('0001448301', date(2018, 10, 29),
            items=['net income', 'net interest income', 'interest income', 'book value per share',
                   'provision for loan losses'],
            values=[1287000.00, 4673000.00, 5816000.00, 27.65, 50000.00],
            fiscal_period='2018Q3')


def test_parse_items_OVLY_20190422():
    compare('0001431567', date(2019, 4, 22),
            items=['net income', 'net interest income', 'book value per share', 'provision for loan losses'],
            values=[3104000.00, 10111000.00, 12.45, 0.00],
            fiscal_period='2019Q1')


def test_parse_items_0001413440_20100129():
    compare('0001413440', date(2010, 1, 29),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share', 'total revenue'],
            values=[-309000.0, 6381000.0, 8886000.0, 700000.0, 12.48, 9256000.00],
            fiscal_period='2009Q4')


def test_parse_items_BMRC_20180122():
    compare('0001403475', date(2018, 1, 22),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[1110000.00, 20139000.00, 20650000.00, 500000.00, 42.91],
            fiscal_period='2017Q4')


def test_parse_items_BMRC_20120120():
    compare('0001403475', date(2012, 1, 20),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[3383000.0, 15718000.0, 16666000.0, 2500000.0, 25.4],
            fiscal_period='2011Q4')


def test_parse_items_BMRC_20160125():
    compare('0001403475', date(2016, 1, 25),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[4925000.0, 17243000.00, 17795000.00, 500000.00, 35.34],
            fiscal_period='2015Q4')


def test_parse_items_BMRC_20090420():
    compare('0001403475', date(2009, 4, 20),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[3229000.00, 12808000.00, 14577000.00, 1185000.00, 19.46],
            fiscal_period='2009Q1')


def test_parse_items_DFS_20070620():
    compare('0001393612', date(2007, 6, 20),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses'],
            values=[2.092420e+08, 367112000.0, 703365000.0, 203287000.0],
            fiscal_period='2007Q2')


def test_parse_items_DFS_20071220():
    compare('0001393612', date(2007, 12, 20),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[-8.406700e+07, 3.481550e+08, 7.488890e+08, 3.399160e+08, 1.166000e+01],
            fiscal_period='2007Q4')


def test_parse_items_HBNK_20140805():
    compare('0001375320', date(2014, 8, 5),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[1266000.00, 5215000.00, 6501000.00, 150000.00, 15.43],
            fiscal_period='2014Q2')


def test_parse_items_MNRK_20120130():
    compare('0001364856', date(2012, 1, 30),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses'],
            values=[2073874.0, 9483792.0, 10968641.0, 2479916.0],
            fiscal_period='2011Q4')


def test_parse_items_0001358356_20120130():
    compare('0001358356', date(2019, 4, 24),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[2839000.00, 8959000.00, 12186000.00, 0.00, 12.91],
            fiscal_period='2019Q1')


def test_parse_items_0001343034_20140721():
    compare('0001343034', date(2014, 7, 21),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[1420000.00, 6686000.00, 7552000.00, 238000.00, 10.75],
            fiscal_period='2014Q2')


def test_parse_items_0001343034_20110127():
    compare('0001343034', date(2011, 1, 27),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses'],
            values=[1049000.00, 6465000.00, 7846000.00, 750000.00],
            fiscal_period='2010Q4')


def test_parse_items_0001323648_20110127():
    compare('0001323648', date(2019, 4, 26),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses'],
            values=[3503000.0, 12125000.0, 15806000.0, 0.0],
            fiscal_period='2019Q1')


def test_parse_items_0001323648_20100805():
    compare('0001323648', date(2010, 8, 5),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses'],
            values=[-19616000.0, 10113000.0, 14933000.0, 21282000.0],
            fiscal_period='2010Q2')


def test_parse_items_0001265131_20130805():
    compare('0001265131', date(2013, 8, 5),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses'],
            values=[22660000.0, 68425000.0, 76168000.0, 11289000.0],
            fiscal_period='2013Q2')


def test_parse_items_HTH_20151102():
    compare('0001265131', date(2015, 11, 2),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[4.724700e+07, 1.152110e+08, 1.305450e+08, 5.593000e+06, 1.735000e+01],
            fiscal_period='2015Q3')


def test_parse_items_HTH_20190124():
    compare('0001265131', date(2019, 1, 24),
            items=['net income', 'net interest income', 'interest income', 'total revenue', 'book value per share'],
            values=[2.955800e+07, 1.177150e+08, 1.577020e+08, 8.975000e+07, 2.083000e+01],
            fiscal_period='2018Q4')


def test_parse_items_BCBP_20170428():
    compare('0001228454', date(2017, 4, 28),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses'],
            values=[2913000.0, 14605000.0, 18455000.0, 498000.0],
            fiscal_period='2017Q1')


def test_parse_items_PFS_20190201():
    compare('0001178970', date(2019, 2, 1),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[35763000.00, 77333000.00, 93922000.00, 1800000.00, 20.49],
            fiscal_period='2018Q4')


def test_parse_items_PFS_20130726():
    compare('0001178970', date(2013, 7, 26),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses'],
            values=[19228000.0, 53411000.0, 62413000.0, 1000000.0],
            fiscal_period='2013Q2')


def test_parse_items_CIT_20100427():
    compare('0001171825', date(2010, 4, 27),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[9.730000e+07, 2.112000e+08, 1.049000e+09, -1.866000e+08, 4.263000e+01],
            fiscal_period='2010Q1')


def test_parse_items_PLBC_20170418():
    compare('0001168455', date(2017, 4, 18),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[2064000.00, 6307000.00, 6765000.00, 200000.00, 10.26],
            fiscal_period='2017Q1')


def test_parse_items_PLBC_20150127():
    compare('0001168455', date(2015, 1, 27),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[1344000.00, 4913000.00, 5668000.00, 350000.00, 7.61],
            fiscal_period='2014Q4')


def test_parse_items_MBFI_20121025():
    compare('0001139812', date(2012, 10, 25),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[23133000.00, 72075000.00, 82663000.00, -13000000.00, 23.01],
            fiscal_period='2012Q3')


def test_parse_items_UBFO_20181017():
    compare('0001137547', date(2018, 10, 17),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[3518000.00, 8863000.00, 9554000.00, -373000.00, 6.33],
            fiscal_period='2018Q3')


def test_parse_items_ANCX_20100128():
    compare('0001176316', date(2010, 1, 28),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[2047000.00, 5865000.00, 8943000.00, 1248000.00, 6.43],
            fiscal_period='2009Q4')


def test_parse_items_NRIM_20070124():
    compare('0001163370', date(2007, 1, 24),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[3689000.0, 12760000.0, 18653000.0, 800000.0, 15.61],
            fiscal_period='2006Q4')


def test_parse_items_MBTF_20101028():
    compare('0001118237', date(2010, 10, 28),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[-4338000.00, 9421000.00, 13789000.00, 6500000.00, 4.94],
            fiscal_period='2010Q3')


def test_parse_items_HAFC_20141107():
    compare('0001109242', date(2014, 11, 7),
            items=['net income', 'net interest income', 'interest income'],
            values=[13264000.0, 30674000.0, 34149000.0],
            fiscal_period='2014Q3')


def test_parse_items_SFST_20180724():
    compare('0001090009', date(2018, 7, 24),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share', 'total revenue'],
            values=[5510000.00, 14612000.00, 18535000.00, 400000.00, 21.66, 17383000.00],
            fiscal_period='2018Q2')


def test_parse_items_TOFC_20100722():
    compare('0001072847', date(2010, 7, 22),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[628697.00, 5597262.00, 7751070.00, 1100000.00, 11.56],
            fiscal_period='2010Q2')


def test_parse_items_EWBC_20160127():
    compare('0001069157', date(2016, 1, 27),
            items=['net income', 'net interest income', 'interest income', 'book value per share',
                   'provision for loan losses'],
            values=[91805000.0, 246940000.0, 270477000.0, 21.7, -3135000.0],
            fiscal_period='2015Q4')


def test_parse_items_ECBE_20060719():
    compare('0001066254', date(2006, 7, 19),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[1415000.00, 5262000.00, 8929000.00, 200000.00, 20.45],
            fiscal_period='2006Q2')


def test_parse_items_PPBI_20100128():
    compare('0001028918', date(2010, 1, 28),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[-277000.00, 3966000.00, 10435000.0, 2200000.00, 7.33],
            fiscal_period='2009Q4')


def test_parse_items_NWFL_20090423():
    compare('0001013272', date(2009, 4, 23),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[1737000.00, 4681000.00, 6690000.00, 225000.00, 21.99],
            fiscal_period='2009Q1')


def test_parse_items_UB_20171020():
    compare('0001011659', date(2017, 10, 20),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'total revenue'],
            values=[2.320000e+08, 8.160000e+08, 1.083000e+09, 1.800000e+07, 1.331000e+09],
            fiscal_period='2017Q3')


def test_parse_items_SMBC_20030417():
    compare('0000916907', date(2003, 4, 17),
            items=['net income', 'net interest income', 'provision for loan losses', 'book value per share'],
            values=[689000.00, 2281000.00, 60000.00, 21.38],
            fiscal_period='2003Q1')


def test_parse_items_OKSB_20170725():
    compare('0000914374', date(2017, 7, 25),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[5818000.00, 21370000.00, 24708000.00, 1729000.00, 15.82],
            fiscal_period='2017Q2')


def test_parse_items_NYB_20170426():
    compare('0000910073', date(2017, 4, 26),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[1.039570e+08, 2.949170e+08, 3.991190e+08, 1.787000e+06, 1.257000e+01],
            fiscal_period='2017Q1')


def test_parse_items_CCNE_20160419():
    compare('0000736772', date(2016, 4, 19),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[5.019e+06, 1.8942e+07, 2.2066e+07, 1.196e+06, 14.4],
            fiscal_period='2016Q1')


def test_parse_items_CCNE_20140203():
    compare('0000736772', date(2014, 2, 3),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[4728000.00, 17279000.00, 20489000.00, 1247000.00, 11.43],
            fiscal_period='2013Q4')


def test_parse_items_CCNE_20190128():
    compare('0000736772', date(2019, 1, 28),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[8945000.00, 28116000.00, 36344000.00, 1441000.00, 17.28],
            fiscal_period='2018Q4')


def test_parse_items_CCNE_20190416():
    compare('0000736772', date(2019, 4, 16),
            items=['net income', 'net interest income', 'interest income', 'provision for loan losses',
                   'book value per share'],
            values=[9473000.00, 27758000.00, 36753000.00, 1306000.00, 18.04],
            fiscal_period='2019Q1')


def test_find_missing_periods():
    df = pd.DataFrame({
        'fiscal_period': ['2018Q1', '2018Q2', '2018Q4', '2018Q4', '2019Q3']
    })
    assert _find_missing_periods(df, start_period='2018Q1') == ['2018Q3', '2019Q1', '2019Q2']


def test_find_duplicate_periods():
    df = pd.DataFrame({
        'fiscal_period': ['2018Q2', '2018Q2', '2018Q4', '2018Q4', '2019Q3'],
        'item_value': [1, 1.1, 2, 2.5, 3]
    })
    assert _find_duplicate_periods(df) == ['2018Q4']


def test_compress_consecutive_periods():
    periods = ['2009Q1', '2009Q3', '2009Q4', '2010Q2', '2010Q3', '2010Q4', '2011Q2']
    expected = ['2009Q1', '2 periods between 2009Q3 and 2009Q4', '3 periods between 2010Q2 and 2010Q4', '2011Q2']
    actual = list(_compress_consecutive_periods(periods))
    print(actual)
    assert list(actual) == expected

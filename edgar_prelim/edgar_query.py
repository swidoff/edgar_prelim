import logging
from collections import namedtuple
from datetime import date, datetime
from types import FunctionType
from typing import Iterator, List
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError

import requests
from requests_html import HTMLSession
from retrying import retry

logger = logging.getLogger(__name__)


# noinspection SpellCheckingInspection
@retry(stop_max_attempt_number=7, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def _query_edgar_for_xml(cik_or_ticker: str,
                         filing_type: str = "",
                         before: date = None,
                         num: int = 100,
                         start: int = 0) -> ElementTree:
    """
    Low-level interface to query the edgar system for an XML listing of filings.
    :param cik_or_ticker: The CIK or ticker to form the basis of the search.
    :param filing_type: The type of prefix of a type of filing, for example, 8-K or 10-
    :param before: Sets the end point of the dates searched.
    :param num: The number of elements to return.
    :param start: Starts the search this number of rows into the dataset.
    :return:
    """
    url = "https://www.sec.gov/cgi-bin/browse-edgar"
    payload = {
        'action': 'getcompany',
        "CIK": cik_or_ticker,
        "type": filing_type,
        "dateb": before.strftime('%Y%m%d') if before else "",
        "owner": "exclude",
        "count": str(num),
        "start": str(start),
        "output": "xml",
    }
    result = requests.get(url, params=payload)
    if result.status_code != requests.codes.ok:
        result.raise_for_status()
    else:
        try:
            return ElementTree.fromstring(result.content)
        except ParseError:
            return ElementTree.Element("")


Filing = namedtuple("Filing", ['date', 'type', 'href'])


# noinspection SpellCheckingInspection
def query_edgar_for_filings(cik: str,
                            filing_type: str = '10-',
                            require_xbrl: bool = True,
                            start: date = None,
                            end: date = None,
                            num: int = 100) -> List[Filing]:
    """
    Returns the results of quertying edgar for filings satisfying the below criteria.
    :param cik: The cik (or ticker) to search.
    :param filing_type: The type of filing or prefix of a filing type.
    :param require_xbrl: If True, limits the results to those containing XBRL.
    :param start: the start date of the search
    :param end: the end date of the search
    :param num: the maximum number of results to return
    :return: a list of Filings matching the criteria
    """
    start_idx = 0
    res = []

    while True:
        res_xml = _query_edgar_for_xml(cik, filing_type, before=end, num=num, start=start_idx)
        filings = res_xml.findall(".//filing")
        if not filings:
            break

        for x in filings:
            if not require_xbrl or x.find("./XBRLREF") is not None:
                filing = Filing(date=datetime.strptime(x.find("./dateFiled").text, '%Y-%m-%d').date(),
                                type=x.find("./type").text,
                                href=x.find("./filingHREF").text)
                if start and filing.date < start:
                    return res
                else:
                    res.append(filing)

        start_idx += num

    return res


# Edgar information about a particular company.
CompanyInfo = namedtuple('CompanyInfo', ['cik', 'sic', 'sic_description', 'company_name'])


def query_edgar_for_company_info(cik_or_ticker: str) -> Iterator[CompanyInfo]:
    """
    Return the company info for a particular cik or ticker.
    """

    class Unknown:

        def __init__(self) -> None:
            self.text = "Unknown"

    def optional(e):
        return [e] if e is not None else [Unknown()]

    def required(e):
        return [e] if e is not None else []

    res_xml = _query_edgar_for_xml(cik_or_ticker)
    yield from [
        CompanyInfo(cik.text, sic.text, sic_desc.text, name.text)
        for x in res_xml.findall(".//companyInfo")
        for name in required(x.find("./name"))
        for cik in required(x.find("./CIK"))
        for sic in optional(x.find("./SIC"))
        for sic_desc in optional(x.find("./SICDescription"))
    ]


class FiscalPeriod(object):
    """Encapsulates a year and a quarter, allowing simple match to be performed."""

    def __init__(self, year: int, quarter: int) -> None:
        self.year = year
        self.quarter = quarter

    def __repr__(self) -> str:
        return f"FiscalPeriod({self.year}, {self.quarter})"

    def __str__(self) -> str:
        return f"{self.year}Q{self.quarter}"

    def __eq__(self, o) -> bool:
        return type(o) is FiscalPeriod and self.year == o.year and self.quarter == o.quarter

    def __add__(self, other):
        """
        Can add a number of quarters, resulting in a new FiscalPeriod.
        """
        if type(other) is int:
            if other < 0:
                return self - abs(other)
            else:
                new_year = self.year + other // 4
                new_qtr = self.quarter + other % 4
                if new_qtr > 4:
                    new_qtr = new_qtr - 4
                    new_year += 1
                return FiscalPeriod(new_year, new_qtr)
        else:
            raise TypeError("Can only add an int to a fiscal period")

    def __sub__(self, other):
        """
        Can subtract an integer number of quarters, resulting in a new FiscalPeriod, or another FiscalPeriod resulting
        in a number of quarters.
        """
        if type(other) is int:
            if other < 0:
                return self + abs(other)
            else:
                new_year = self.year - other // 4
                new_qtr = self.quarter - other % 4
                if new_qtr <= 0:
                    new_qtr = 4 + new_qtr
                    new_year -= 1
                return FiscalPeriod(new_year, new_qtr)
        elif type(other) is FiscalPeriod:
            year_diff = self.year - other.year
            qtr_diff = self.quarter - other.quarter
            return year_diff * 4 + qtr_diff
        else:
            raise TypeError("Can only sub an int or FiscalPeriod from a FiscalPeriod")

    @staticmethod
    def from_str(fp: str):
        """Returns a new fiscal period from a string in the form YYYYqQ, where YYYY is the four digit year
        and Q is the integer quarter."""
        return FiscalPeriod(int(fp[:4]), int(fp[5:]))

    @staticmethod
    def from_fpe_date(fye_date: date, fpe_date: date):
        """From a fiscal year end date and a fiscal period date, deduces the fiscal period for the fpe_date relative
        to the fye_date."""
        if fpe_date > fye_date:
            raise ValueError(f"fpe_date {fpe_date} must not be after fye_date {fye_date}.")

        if fpe_date.day < 7:
            fpe_date = fpe_date.replace(month=fpe_date.month - 1 if fpe_date.month > 1 else 12)

        year_diff = fye_date.year - fpe_date.year
        month_diff = year_diff * 12 + fye_date.month - fpe_date.month
        quarter_diff = month_diff // 3

        if quarter_diff >= 4:
            fye_date = fye_date.replace(year=fye_date.year - quarter_diff // 4)
            quarter_diff = quarter_diff % 4

        fiscal_quarter = max(4 - quarter_diff, 1)
        fiscal_year = fye_date.year if fye_date.month >= 6 else fye_date.year - 1
        return FiscalPeriod(fiscal_year, fiscal_quarter)


# The underlying report document href for a particular filing.
Report = namedtuple("Report", ['fpe_date', 'fye_date', 'fiscal_period', 'href'])


# noinspection PyUnresolvedReferences
@retry(stop_max_attempt_number=7, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def _query_edgar_for_filing_document(filing_href: str, extract_href_from_html: FunctionType) -> Report:
    """
    Extracts a report from a filing page. The supplied function selects the relevant link from the page.
    """
    session = HTMLSession()
    result = session.get(filing_href)
    if result.status_code != requests.codes.ok:
        result.raise_for_status()
    else:
        html = result.html
        fpe_date = _fiscal_period_end_from_filing_html(html)
        fye_date = _fiscal_year_end_from_filing_html(html, fpe_date)
        return Report(
            fpe_date=fpe_date,
            fye_date=fye_date,
            fiscal_period=FiscalPeriod.from_fpe_date(fye_date, fpe_date),
            href=extract_href_from_html(html))


def _extract_href_from_filing_html(html, label, *paths):
    links = None
    for path in paths:
        hrefs = html.xpath(path)
        links = [link for link in html.absolute_links if any(link.endswith(href) for href in hrefs)]
        if links and len(links) == 1:
            break

    if not links:
        raise Exception(f"No {label} found for: {html.url}")
    elif len(links) > 1:
        raise Exception(f"More than one {label} link in: {html.url}")
    else:
        return links[0]


def query_edgar_for_filing_xbrl(filing_href: str) -> Report:
    """Pulls a link to the XBRL report on the filing page."""

    def _xbrl_href_from_filing_html(html) -> str:
        path1 = (
            "//table[@summary = 'Data Files']"
            "//td[contains(text(), 'INSTANCE')]"
            "//following-sibling::td"
            "/a[contains(@href, '.xml')]/@href"
        )
        path2 = (
            "//table[@summary = 'Data Files']"
            "//td[contains(text(), 'EX-101.INS')]"
            "//preceding-sibling::td"
            "/a[contains(@href, '.xml')]/@href"
        )
        return _extract_href_from_filing_html(html, "XBRL", path1, path2)

    return _query_edgar_for_filing_document(filing_href, _xbrl_href_from_filing_html)


def query_edgar_for_submission_text(filing_href: str) -> Report:
    """Pulls a link to the submission text on the filing page."""

    def _submission_text_href_from_filing_html(html) -> str:
        path1 = (
            "//table[@summary = 'Document Format Files']"
            "//td[contains(text(), 'submission')]"
            "//following-sibling::td"
            "/a[contains(@href, '.txt')]/@href"
        )
        return _extract_href_from_filing_html(html, "submission txt", path1)

    return _query_edgar_for_filing_document(filing_href, _submission_text_href_from_filing_html)


def _fiscal_period_end_from_filing_html(html) -> date:
    """From the filing html page, parses the date link."""
    return datetime.strptime(html.xpath(
        "//div[text() = 'Period of Report']"
        "//following-sibling::div"
        "//text()"
    )[0], '%Y-%m-%d').date()


def _fiscal_year_end_from_filing_html(html, fpe_date: date) -> date:
    """From the filing html page and the fpe_date, returns the fiscal year end date."""
    form_name = html.xpath(
        "//div[@id = 'formName']"
        "/strong"
        "/text()"
    )[0]

    if form_name.endswith('10-K'):
        return fpe_date

    fye = html.xpath(
        "//p[@class = 'identInfo']"
        "/br[1]"
        "/preceding-sibling::strong[1]"
        "/text()"
    )[0]

    if len(fye) < 3 or len(fye) > 4:
        return fpe_date

    fye_month = int(fye[:2])
    fye_day = int(fye[2:])

    fpe_month = fpe_date.month if fpe_date.day > 7 else fpe_date.month - 1
    fye_year = fpe_date.year + 1 if fpe_month > fye_month else fpe_date.year

    while fye_day > 0:
        try:
            return date(fye_year, fye_month, fye_day)
        except ValueError as e:
            if str(e) == 'day is out of range for month':
                fye_day -= 1
            else:
                raise e
    else:
        raise ValueError(f"Can't deal with Fiscal Year End {fye}.")

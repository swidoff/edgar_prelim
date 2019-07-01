from functools import partial
from re import Pattern
from types import FunctionType
from typing import Optional, Tuple, List, Sequence

import pandas as pd

from edgar_prelim.edgar_re import *


def ordinal_to_number(word):
    w = re.sub(r'\s+', '', word)
    if w == 'first' or w == '1st':
        return 1
    elif w == 'second' or w == '2nd':
        return 2
    elif w == 'third' or w == '3rd':
        return 3
    elif w == 'fourth' or w == '4th':
        return 4
    else:
        return None


def number_to_quarter(raw_word):
    word = re.sub(r'\s+', '', raw_word)
    if word == 'three' or word == '3' or word == '03':
        return 1
    elif word == 'six' or word == '6' or word == '06':
        return 2
    elif word == 'nine' or word == '9' or word == '09':
        return 3
    elif word == 'twelve' or word == '12':
        return 4
    else:
        return None


def year_from_str(raw_digits: str) -> str:
    digits = re.sub(r"['\s]+", '', raw_digits)
    if len(digits) == 4:
        return digits
    elif int(digits) < 50:
        return '20' + digits
    else:
        return '19' + digits


def month_to_quarter(raw_month: str) -> int:
    month = re.sub(r'\s+', '', raw_month)
    if month.startswith('mar') or month.startswith('feb'):
        return 1
    elif month.startswith('jun') or month.startswith('may'):
        return 2
    elif month.startswith('sep') or month.startswith('aug'):
        return 3
    elif month.startswith('dec') or month.startswith('nov'):
        return 4
    else:
        raise ValueError("Unknown quarter month: " + month)


QTR = r'[1-4]'
YEAR = r"(?:20|')?\s*\d\s*\d"
SHORT_YEAR = r"'?\d\s*\d"
STRICT_YEAR = r'20\s*\d\s*\d'
MONTH = r'feb(?:ruary)?\.?|mar(?:ch)?\.?|may|jun(?:e)?\.?|aug(?:ust)?\.?|' \
        r'sep(?:tember|t)?\.?|nov(?:ember)?\.?|dec(?:ember)?\.?'
VERBOSE_QTR_PREFIX = fr'(?:for\s+)?(?:the\s+)?(?:three\s+months|quarters?)\s+end(?:ed|ing)[,:]?\s+(?:\(\w+\)\s*)?'
VERBOSE_DATE_QTR = fr'{VERBOSE_QTR_PREFIX}({MONTH})'
ORDINAL = r'first|1\s*st|second|2\s*nd|third|3\s*rd|fourth|4\s*th'
ORDINAL_QTR = fr'({ORDINAL})(?:(?:\s+|-)(?:quarter|qtr\.?|q))?'
DAY_OF_MONTH = r'(?:\d\s*)+(?:st|nd|rd|th)?\s*[,:]?\s*'

# Patterns for legal fiscal period strings paired with the function that will turn a match object into a fiscal period
# string using the group parts of the match.
fiscal_period_patterns = tuple(
    (re_compile(rf'{pattern}\s*,?{FOOTNOTE}$'), parser)
    for pattern, parser in [
        (fr'({QTR})\s*q(?:tr)?\s*({YEAR})',
         lambda m: f'{year_from_str(m.group(2))}Q{m.group(1)}'),

        (fr'q(?:tr)?\s*({QTR})\s*({YEAR})',
         lambda m: f'{year_from_str(m.group(2))}Q{m.group(1)}'),

        (fr'({YEAR})\s*q({QTR})',
         lambda m: f'{year_from_str(m.group(1))}Q{m.group(2)}'),

        (fr'({YEAR})\s+{ORDINAL_QTR}',
         lambda m: f'{year_from_str(m.group(1))}Q{ordinal_to_number(m.group(2))}'),

        (fr'{ORDINAL_QTR}\s+({YEAR})',
         lambda m: f'{year_from_str(m.group(2))}Q{ordinal_to_number(m.group(1))}'),

        (fr'(?:quarter|qtr\.?|q)\s+({YEAR})\s+({ORDINAL})',
         lambda m: f'{year_from_str(m.group(1))}Q{ordinal_to_number(m.group(2))}'),

        (fr'{VERBOSE_DATE_QTR}\s*{DAY_OF_MONTH}({STRICT_YEAR})',
         lambda m: f'{year_from_str(m.group(2))}Q{month_to_quarter(m.group(1))}'),

        (fr'{VERBOSE_DATE_QTR}\s*{DAY_OF_MONTH}({YEAR})',
         lambda m: f'{year_from_str(m.group(2))}Q{month_to_quarter(m.group(1))}'),

        (fr'(?!\s)({MONTH})\s*{DAY_OF_MONTH}({YEAR})',
         lambda m: f'{year_from_str(m.group(2))}Q{month_to_quarter(m.group(1))}'),

        (fr'{VERBOSE_QTR_PREFIX}([\d\s]+)/[\d\s]+/({YEAR})',
         lambda m: f'{year_from_str(m.group(2))}Q{number_to_quarter(m.group(1))}'),

        (fr'{VERBOSE_QTR_PREFIX}(?:28|29|30|31)(?:\s+|-)({MONTH})\s+({STRICT_YEAR})?',
         lambda m: f'{year_from_str(m.group(2))}Q{month_to_quarter(m.group(1))}'),

        (fr'{VERBOSE_QTR_PREFIX}({YEAR})\s+({MONTH})(?:\s+\d+)?',
         lambda m: f'{year_from_str(m.group(1))}Q{month_to_quarter(m.group(2))}'),

        (fr'\d+-({MONTH})-({YEAR})',
         lambda m: f'{year_from_str(m.group(2))}Q{month_to_quarter(m.group(1))}'),

        (fr'(\d+)/\d+/({YEAR})',
         lambda m: f'{year_from_str(m.group(2))}Q{number_to_quarter(m.group(1))}'),

        (fr'q({QTR})\s+({YEAR})',
         lambda m: f'{year_from_str(m.group(2))}Q{m.group(1)}'),

        (fr'({YEAR})\s*qt(?:d|r)',
         lambda m: f'{year_from_str(m.group(1))}QTD'),

        (fr'qt(?:d|r)\s*({YEAR})',
         lambda m: f'{year_from_str(m.group(1))}QTD'),

        (fr'({STRICT_YEAR})\s+({MONTH})\s+(?:28|29|30|31)',
         lambda m: f'{year_from_str(m.group(1))}Q{month_to_quarter(m.group(2))}')
    ]
)

NOT_QUARTER = \
    r'(?:at\s+or\s+)?(?:for\s+(?:the\s+)?)?' \
    r'(?:(?:six|6)\s+months?|(?:nine|9)\s+months?|(?:twelve|12)\s+months?|(?:full\s+|fiscal\s+|\s*)?years?)' \
    r'(?:\s+periods?)?(?:\s+|-)end(?:ed|ing),?'

# Since currently we only support quarterly income statement items, exclude from the matches any periods for
# longer than a quarter (or that don't otherwise represent a single quarter.
fiscal_period_exclusions = (
    re_compile(r'vs'),
    re_compile(r'%\s+change'),
    re_compile(fr'year\s*{HYPHEN}*\s*to\s*{HYPHEN}*\s*date'),
    re_compile(rf'^{NOT_QUARTER}'),
    re_compile(rf'{NOT_QUARTER}\s+(?:{MONTH})\s*{DAY_OF_MONTH}{YEAR}{FOOTNOTE}$'),
    re_compile(rf'{NOT_QUARTER}\s+\d+/\d+/{YEAR}{FOOTNOTE}$'),
)


def parse_fiscal_period(period: str, prefix: str = None,
                        patterns: Sequence[Tuple[Pattern, FunctionType]] = fiscal_period_patterns,
                        exclusions: Sequence[Pattern] = fiscal_period_exclusions) -> Optional[Tuple[str, int]]:
    """
    Matches a period string against a collection of inclusions and exclusion patterns.
    :param period: A possible fiscal period string
    :param prefix: An optional prefix to be prended if 'period' doesn't match alone.
    :param patterns: A sequence of inclusion patterns paired with a function to translate a match to an FP string.
    :param exclusions: A sequence of patterns where a successful match means the period must not be an FP.
    :return: if period (or prefix + ' ' + period) doesn't match an exclusion or matches an inclusion, a tuple
    of the FP string and the index of the matching pattern is returned, otherwise None.
    """

    def _prep_fiscal_period_str(p):
        prepped = str(p).strip().lower()
        return re.sub(UNAUDITED_EXACT, '', prepped).strip()

    prepped_period = _prep_fiscal_period_str(period)
    if any(re.search(p, prepped_period) is not None for p in exclusions):
        return None

    if prefix:
        prepped_prefix = _prep_fiscal_period_str(prefix)
        if any(re.search(p, prepped_prefix) is not None for p in exclusions):
            return None

    for i, (pattern, f) in enumerate(patterns):
        match = re.search(pattern, prepped_period)
        if match:
            return f(match), len(patterns) - i

    if prefix and is_header_part(prefix):
        return parse_fiscal_period(prefix + ' ' + period)

    return None


def has_fiscal_period(row: pd.Series) -> bool:
    """
    Returns true if any value in this row is a fiscal period (starting at index 1, with index 0 being a possible
    prefix).
    """
    return any(row.iloc[1:].astype(str).map(partial(parse_fiscal_period, prefix=str(row.iloc[0]))))


def parse_fiscal_period_row(row: pd.Series) -> List[Tuple[int, str]]:
    """
    For a table row expected to have fiscal periods within, returns a list of Tuples for all elements containing
    a fiscal period, with the first tuple value being the "rank" of the pattern matched (lower having higher rank) and
    the second value being the parsed FP string.
    """
    fps = row.iloc[1:].map(partial(parse_fiscal_period, prefix=row.iloc[0]))
    return [
        (index, fiscal_period)
        for (index, (fiscal_period, _)) in fps.dropna().sort_values(ascending=False).items()
    ]


def is_header_part(cell: str) -> bool:
    """
    Return true if the supplied cell could possibly be part of a header row, either as a standalone fiscal period
    or when concatenated with cells above and below it.
    """
    pattern = '|'.join([
        rf'(?:(?:three|3|six|6|nine|9|twelve|12)\s+months?(?:\s+periods?)?|quarters?|year|ytd)(?!ly)',
        rf'\b(?:{MONTH})\b',
        rf'^(?:end(?:ed|ing))?(?:20)\s*[0-2]\s*[0-9]{FOOTNOTE}$',
        rf'^\d{1, 2}/\d{1, 2}/\d{2, 4}{FOOTNOTE}$',
        rf'^q[1-4](?:\s*\(\w+\))?{FOOTNOTE}$',
        rf'^[1-4]q(?:tr)?(?:\d{2, 4})?',
        rf'as\s+(?:reported|adjusted)',
        rf'year-?\s*to-?\s*date',
        rf'^year-$',
        rf'^to-date$',
        rf'full\s+year',
        rf'^(?:28|29|30|31){FOOTNOTE}$',
        rf'^(?:month|quarter|year)s?{FOOTNOTE}$',
        rf'^(?:three|six|nine|twelve){FOOTNOTE}$',
        rf'^(?:operating|reported|baseline|percent|%|end(?:ed|ing)){FOOTNOTE}$',
        ORDINAL,
        rf'^(?:(?:20)\s*[0-2]\s*[0-9]\*\s*)?{UNAUDITED_EXACT}$'
    ])
    prepped = str(cell).lower().strip()
    match = re.search(allow_space_between_letters(pattern), prepped)
    return match is not None or parse_fiscal_period(cell) is not None

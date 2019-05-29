from collections import namedtuple, Iterable, ChainMap
from re import Pattern
from typing import Optional, Tuple, Sequence

# noinspection PyProtectedMember
from bs4 import Tag

from bs4_util import match_table_title_text
from edgar_re import *

######################################################################
# Titles
######################################################################


TitlePattern = namedtuple('Pattern', ['pattern', 'exclusions', 'inclusions'])


def title_pattern(pattern, inc=None, exc=None) -> TitlePattern:
    return TitlePattern(re_compile(pattern), inc if inc else [], exc if exc else {})


TITLE_SUFFIX = rf'{UNAUDITED}{FOOTNOTE}'

# Patterns for titles in order of how likley they are to contain consolidated income statement items (and book to value)
title_inclusion_patterns = (
    # Consolidated
    title_pattern(
        fr'^{UNAUDITED}(?:(?:quarterly|condensed|unaudited|the\s+company\Ws)\s+)*'
        fr'consolidated\s+(?:(?:quarterly|comparative|condensed)\s+)*'
        fr'(?:statement|report)s?\s+of\s+(?:(?:net|comprehensive)\s+)*(?:income|earnings|loss|operations)'),
    title_pattern(
        r'consolidated\s+(?:(?:quarterly|comparative|condensed)\s+)*(?:statement|reports)s?\s+of\s+'
        fr'(?:(?:net|comprehensive)\s+)*(?:income|earnings|loss|operations){TITLE_SUFFIX}$'),
    title_pattern(
        fr'^{UNAUDITED}(?:(?:quarterly|comparative|condensed)\s+)*?consolidated\s+'
        r'(?:(?:quarterly|comparative)\s+)*(?:net\s+)?(?:income|earnings)\s+(?:statement|reports)s?'),
    title_pattern(
        fr'consolidated\s+(?:(?:quarterly|comparative)\s+)*(?:net\s+)?'
        fr'(?:income|earnings)\s+(?:statement|reports)s?(?:\s+information)?{TITLE_SUFFIX}$'),
    title_pattern(
        fr'^{UNAUDITED}(?:(?:quarterly|condensed|select(?:ed)?)\s+)*consolidated\s+'
        fr'(?:(?:select(?:ed)?|key)\s+)*'
        r'(?:financial|operating|earnings|capital)?(?:\s+and\s+other)?'
        r'(?:\s+(?:results|metrics|highlights?|summary|information|data))+'),
    title_pattern(
        r'consolidated\s+(?:financial|operating|earnings|capital)(?:\s+and\s+other)?'
        fr'(?:\s+(?:results|metrics|highlights?|summary|information|data))+{TITLE_SUFFIX}'),
    title_pattern(r'financial\s+(?:(?:and|&)\s+statistical\s+)?summary\W+consolidated'),
    title_pattern(fr'^{UNAUDITED}(?:(?:quarterly|condensed)\s+)*consolidated\s+balance\s+sheets?'),
    title_pattern(fr'consolidated\s+balance\s+sheets?{TITLE_SUFFIX}$'),
    title_pattern(r'^consolidated\s+(?:results|statements?)\s+of\s+(?:operations?|(?:financial\s+)?condition)'),
    title_pattern(
        fr'consolidated\s+(?:results|statements?)\s+of\s+(?:operations?|(?:financial\s+)?condition){TITLE_SUFFIX}$'
    ),

    # Special cases
    title_pattern(fr'^{UNAUDITED}statements?\s+of\s+income(?:\s*\(loss\))?{TITLE_SUFFIX}', inc={'0000019617'}),
    title_pattern(fr'^{UNAUDITED}statements?\s+of\s+income\W+reported\s+basis{TITLE_SUFFIX}', inc={'0000019617'}),

    # Summary
    title_pattern(
        fr'^{UNAUDITED}(?:(?:key|condensed|summary|supplemental|additional|\d+)\s+)(?:quarterly\s+)?'
        r'(?:financial|operating|income\s+statement)\s*'
        fr'(?:highlights?|information|results|data)(?:\s+by\s+quarter)?(?:\s+\(?continued\)?)?'),
    title_pattern(
        fr'(?:(?:key|condensed|summary|supplemental|additional|\d+)\s+)(?:quarterly\s+)?'
        r'(?:financial|operating|income\s+statement)\s*'
        fr'(?:highlights?|information|results|data)(?:\s+by\s+quarter)?(?:\s+\(?continued\)?)?{TITLE_SUFFIX}'),
    title_pattern(
        fr'^{UNAUDITED}^(?:select(?:ed))?(?:quarterly\s+)?'
        r'(?:financial|operating|income\s+statement|key)\s*'
        fr'(?:highlights?|information|results|data|metrics)(?:\s+by\s+quarter)?(?:\s+\(?continued\)?)?{TITLE_SUFFIX}$'),
    title_pattern(rf'^{UNAUDITED}(?:quarterly\s+)?(?:results|statements?)\s+of\s+operations?'),
    title_pattern(rf'(?:quarterly\s+)?(?:results|statements?)\s+of\s+operations?{TITLE_SUFFIX}'),
    title_pattern(rf'^{UNAUDITED}(?:key|select(?:ed)?)\s+'
                  rf'(?:(?:performance|financial)\s+)?(?:(?:\s*and\s+)?(?:ratios|data))+{TITLE_SUFFIX}'),
    title_pattern(rf'^{UNAUDITED}summary\s+of\s+business\s+results'),
    title_pattern(rf'summary\s+of\s+business\s+results{TITLE_SUFFIX}'),
    title_pattern(fr'(?:(?:(?:and|&)\s+)?(?:statistical|financial)\s+)+summary(?:\s+reported\s+basis)?{TITLE_SUFFIX}'),
    title_pattern(
        fr'^{UNAUDITED}(?:(?:quarterly|summary|condensed)\s+)+'
        fr'statements?\s+of\s+income(?:\s+data)?(?:\s*\(loss\))?{TITLE_SUFFIX}'),
    title_pattern(
        fr'^{UNAUDITED}(?:(?:quarterly|summary|condensed)\s+)+'
        fr'income\s+statements?(?:\s+data)?{TITLE_SUFFIX}', exc={'0000750556'}),
    title_pattern(fr'^{UNAUDITED}quarterly\s+(?:performance|results)\s+summary{TITLE_SUFFIX}', exc={'0000750556'}),
    title_pattern(
        fr'^{UNAUDITED}(?:(?:quarterly|summary|condensed)\s+)*'
        fr'statements?\s+of\s+(?:financial\s+)?condition?{TITLE_SUFFIX}', exc={'0000750556'}),
    title_pattern(fr'^{UNAUDITED}(?:earnings|revenue)\s+summary(?:\(non\s+tax\s+equivalent\)?)?{TITLE_SUFFIX}',
                  exc={'0001393612'}),
    title_pattern(fr'^{UNAUDITED}(?:financial\s+)?highlights[*]?{TITLE_SUFFIX}'),

    # Detail
    title_pattern(
        fr'^{UNAUDITED}statements?\s+of\s+(?:earnings|income)'
        fr'(?:\s+(?:data|information|summary))?(?:\s*\(loss\))?{TITLE_SUFFIX}'),
    title_pattern(
        fr'^{UNAUDITED}income(?:\s+(?:statements?|data|\s+summary))+(?:\s+for\s+the\s+[\w\s]+ended)?{TITLE_SUFFIX}',
        exc={'0000750556'}),
    title_pattern(
        fr'^{UNAUDITED}(?:selected\s+|ending\s+)?balance\s+sheet(?:\s+data|\s+and\s+capital\s+ratios)?{TITLE_SUFFIX}'),
    title_pattern(fr'^{UNAUDITED}net\s+interest\s+income\s+and\s+net\s+interest\s+margin{TITLE_SUFFIX}'),
    title_pattern(fr'^{UNAUDITED}interest\s+and\s+dividend\s+income{TITLE_SUFFIX}'),
    title_pattern(fr'^{UNAUDITED}reconciliation\s+of\s+total\s+revenue{TITLE_SUFFIX}', inc={'0001390777'}),
    title_pattern(fr'^{UNAUDITED}gaap\s+basis{TITLE_SUFFIX}'),
    title_pattern(fr'^{UNAUDITED}per\s+share-related\s+information{TITLE_SUFFIX}'),
    title_pattern(fr'^{UNAUDITED}income\s+(?:statement\s+)?trend\s+analysis'),
    title_pattern(fr'^{UNAUDITED}financial\s+statistics{TITLE_SUFFIX}'),
    title_pattern(
        fr'^{UNAUDITED}(?:selected\s+information\+for\s+)?'
        fr'(?:common\s+)?(?:share|stock)holders{APOSTROPHE}\s+equity{TITLE_SUFFIX}'),
    title_pattern(fr'^{UNAUDITED}allowance\s+for\s+credit\s+losses{TITLE_SUFFIX}'),
    title_pattern(fr'^{UNAUDITED}(?:other\s+data\s+and|financial)\s+ratios{TITLE_SUFFIX}'),
    title_pattern(fr'^{UNAUDITED}capital\s+(?:measures|information|ratios){TITLE_SUFFIX}'),
    title_pattern(fr'^{UNAUDITED}(?:eop\s+|per\s+)+(?:common\s+)?share\s+data{TITLE_SUFFIX}'),
    title_pattern(fr'^{UNAUDITED}(?:operating\s+)?efficiency\s+ratio{TITLE_SUFFIX}'),
    title_pattern(fr'^{UNAUDITED}earnings{TITLE_SUFFIX}'),
)

title_exclusion_patterns = (
    re_compile(fr'^(?:definitions\s+and\s+reconciliation\s+of\s+gaap\s+to\s+)?'
               fr'non-gaap\s+financial\s+measures{UNAUDITED}{FOOTNOTE}$'),
    re_compile(r'business\s+segment'),
    re_compile(r'segment\s+results'),
    re_compile(r'-\s+subsidiaries'),
    re_compile(fr'^impact\s+of\s+restatement\s+on\s+prior\s+period\s+balances{FOOTNOTE}$')
)


def title_from_table_tag(table: Tag, cik: str = '',
                         inclusion_patterns: Sequence[TitlePattern] = title_inclusion_patterns,
                         exclusion_patterns: Sequence[Pattern] = title_exclusion_patterns) -> Optional[Tuple[str, int]]:
    """
    Finds the highest ranking matching title within or above the table.
    :param table: the table Tag
    :param cik: used to filter the the list of inclusion_patterns relevant to the cik.
    :param inclusion_patterns: The patterns to match against in their order of preference.
    :param exclusion_patterns: The search will not continue past a tag where an exclusion pattern is reached (or
    return any matches within that tag).
    :return: The highest ranking matching pattern and its index in the inclusion_patterns list, or None for no title.
    """
    patterns = [
        pattern
        for pattern, inc_cik, exc_cik in inclusion_patterns
        if (not inc_cik or cik in inc_cik) and (not exc_cik or cik not in exc_cik)
    ]
    return match_table_title_text(table, patterns, exclusion_patterns)


######################################################################
# Units
######################################################################

units_table = ChainMap(
    {'thousand': 1e3, 'thousands': 1e3, '000s': 1e3, 'million': 1e6, 'millions': 1e6, 'billion': 1e9, 'billions': 1e9},
    {f'000{apostrophe}s': 1e3 for apostrophe in ['', "'", '\x92', '’', '']}
)

any_unit = '|'.join(units_table.keys())

unit_patterns = (
    re_compile(rf"(?:dollars|\$)(?:\s+and\s+shares)?\s+in\s+(?:{any_unit})"),
    re_compile(rf"in\s+(?:dollars|\$)\s+(?:{any_unit})"),
    re_compile(rf"\$(?:{any_unit})"),
    re_compile(rf"(?:{any_unit}),?\s+except(?:,?\s+(?:percentages|(?:per\s+)?share\s+(?:data|amounts)))+"),
    re_compile(rf"in\s+(?:{any_unit})\s+of\s+dollars"),
    re_compile(rf"in\s+(?:{any_unit})\)?$"),
    re_compile(rf"in\s+(?:{any_unit})[,\w\s]+"),
    re_compile(rf"\((?:{any_unit})\)")
)


def is_units(cell: str) -> bool:
    """Returns true if this cell contains units for the table values."""
    return any(re.search(p, cell.lower()) for p in unit_patterns)


def units_from_table(table: Tag, title: str) -> (str, float):
    """Returns true if the table contains or its previous siblings contains the units for the table values."""
    unit_match = match_table_title_text(
        table, unit_patterns, first_match=True, continue_to_next_table_after_match=title)

    if not unit_match:
        return None, 1.0
    else:
        unit_phrase, _ = unit_match
        unit = re.search(rf"({allow_space_between_letters(any_unit)})", unit_phrase, flags=re.IGNORECASE).group(1)
        return unit_phrase, units_table[re.sub(r'\s+', '', unit.lower())]

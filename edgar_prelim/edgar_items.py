from edgar_re import *
from collections import namedtuple

# PrelimItem, currently only an income statement item, has the following components:
# 1) The name of the item.
# 2) The minimum abs value expected for this value to have a units (otherwise units are inferred).
# 3) A ranked sequence of patterns to look for in the initial table column. Patterns earlier in the list are
#    preferred over those that appear later.
PrelimItem = namedtuple("PrelimItem", ["name", "min_abs_value", "patterns"])

prelim_items = [
    PrelimItem(
        'net income', 1e4, [
            # 1
            fr'net\s*(?:\(loss\)\s*/?\s*)?(?:income|earnings|profit|\(?loss\)?)\s*[\d/]?'
            fr'(?:\s*\(?(?:loss|expense)\)?\s*)*'
            fr'(?:available\s+(?:for|to)\s+common\s+(?:share|stock)holders|from\s+operations)?[\d, ]*\$*{FOOTNOTE}$',
            # 2
            fr'^net\s*(?:\(loss\)\s*/?\s*)?(?:income|earnings|profit|\(?loss\)?)\s*[\d/]?'
            fr'(?:\s*\(?(?:loss|expense)\)?\s*)*'
            fr'attributable\s+to\s+(?!noncontrolling)[\w,. ]+{FOOTNOTE}$',
        ]),
    PrelimItem(
        'net interest income', 1e5, [
            # 1
            rf'^net\s+'
            rf'(?:direct\s+)?(?:finance,\s+loan\s+and\s+)?interest(?:\s+and\s+dividend)?'
            rf'(?:\s*\((?:loss|expense)\)\s*/?\s*)?'
            rf'(?:\s+income|\s+revenue)'
            rf'(?:\s*/?\s*\((?:loss|expense)\)\s*/?\s*)?(?:\s+and\s+other\s+financing\s+income)?'
            rf'(?:,?\s+after\s+(?:\(reversal\s+of\)\s+)?(?:provision|reversal)'
            rf'(?:\s+for+\s(?:\((?:recovery|recapture)\s+of\)\s*)?'
            rf'(?:(?:and\s+)?(?:credit|loan|lease)\s+)*losses'
            rf')?)?(?:\(?\s*{HYPHEN}*\s*gaap\)?)?{FOOTNOTE}$',
            # 2
            fr'net\s+interest{FOOTNOTE}$',
            # 3
            fr'^net\s+interest\s+income(?:\s*-\s*FTE|,?\s+taxable\s+equivalent)'
            fr'(?:\(?\s*non{HYPHEN}*\s*gaap\)?)?{FOOTNOTE}$'
        ]),
    PrelimItem(
        'interest income', 1e5, [
            # 1
            fr'^(?:total\s+)?(?:direct\s+)?(?:finance,\s+loan\s+and\s+)?'
            fr'interest(?:,\s+fee)?(?:\s+and\s+dividend)?\s+'
            fr'(?:income|revenue)(?:\s+,\s+including\s+other\s+financing\s+income)?{FOOTNOTE}$',
            # 2
            r'(?:total\s+)?interest\s+and\s+dividends?',
            # 3
            fr'^(?:total\s+)?interest\s+income\s*'
            fr'(?:\s*-\s*FTE|,?\s+taxable\s+equivalent)'
            fr'(?:\(?\s*non{HYPHEN}*\s*gaap\)?)?{FOOTNOTE}$'
        ]),
    PrelimItem(
        'provision for loan losses', 1e4, [
            # 1
            r'^(?:less\s*[:-]\s+)?(?:total\s+)?'
            r'(?:\(?(?:reversal(?:\s+of)?|recovery(?:\s+of(?:\s+provision)?)?|reduction\s+in|credit)\)?\s*/?\s*)?'
            r'provision(?:\s*/?\s*\((?:benefit|credit|negative\s+provision|reversal|recapture)\))?\s+'
            r'for(?:\s+allowance\s+for)?\s+(?:\((?:recovery|reversal|recapture)\s+of\)\s*)?'
            r'(?:(?:portfolio|possible)\s+)?'
            r'(?:(?:credit|loan)(?:\s*(?:and|/))?(?:\s*(?:lease|covered\s+loan))?\s+loss(?:es)?|'
            r'loss(?:es)?\s+on\s+(?:(?:non\s*-\s*)?covered\s+)?(?:credit|loans))',
            # 2
            r'^(?:recovery\s+of|reversal\s+for)\s+'
            r'(?:credit\s+losses|loss(?:es)?\s+on\s+(?:(?:non\s*-\s*)?covered\s+)?(?:credit|loans))',
            # 3
            r'^(?:recovery\s+of|reversal\s+for)\s+'
            r'(?:credit\s+losses|loss(?:es)?\s+on\s+(?:(?:non\s*-\s*)?covered\s+)?(?:credit|loans))'
            # 4
            r'^(?:loan\s+)?loss\s+provision$'
        ]),
    PrelimItem(
        'total revenue', 1e5, [
            # 1
            r'^total\s+(?:(?:net|consolidated|gaap)\s+)?revenues?',
            # 2
            r'^net\s+revenues?'
        ]),
    PrelimItem(
        'book value per share', 1, [
            # 1
            fr'^(?:total\s+)?(?:common\s+)?(?:(?:shareholders\W?\s+)?equity\s+)?'
            fr'\(?book\s+value\)?'
            fr'(?:\s+\(?per\s+(?:common\s+|outstanding\s+)*shares?'
            fr'(?:\s+common|\s+outstanding|\s+of\s+common\s+stock)?\)?)?,?'
            fr'(?:(?:\s+at)?\s+\(?(?:period\s*-?\s*end|end\s+of\s+quarter)\)?)?'
            fr"(?:\s*\(total\s+stockholders'\s+equity\/shares\s+outstanding\))?"
            fr"(?:\s*\(basic\))?"
            fr"(?:\s*\(dollars\))?"
            fr'(?:\s*{HYPHEN}*\s*gaap)?{FOOTNOTE}$',
            # 2
            r'\(book\s+value\s+per\s+(?:common\s+)?share\)'
        ]),
]

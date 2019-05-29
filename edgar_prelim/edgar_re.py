import re
from re import Pattern

HYPHEN = r'[—\x97\x96–-]'
FOOTNOTE = r'(?:\s*(?:\([\w$]{1,2}\)|\*))*'

UNAUDITED_EXACT = r'\(?unaudited\)?'
UNAUDITED = rf'(?:-*\s*{UNAUDITED_EXACT}\s*)?:?\s*'

APOSTROPHE_LIST = ["'", '\x92', '’']
APOSTROPHE = rf"[{''.join(APOSTROPHE_LIST)}]"


def allow_space_between_letters(pattern: str) -> str:
    """Alters a regex pattern so that optional spaces can appear between any letter."""
    n = len(pattern)
    rep = {'+', '?', "*"}

    def gen():
        for i, l in enumerate(pattern):
            yield l
            if l.isalpha() and (i == 0 or pattern[i - 1] != '\\') and (i == n - 1 or pattern[i + 1] not in rep):
                yield r'\s*'

    return ''.join(gen())


def is_hyphen(src_value: str) -> bool:
    return re.match(fr'^{HYPHEN}+$', src_value) is not None


def re_compile(pattern: str) -> Pattern:
    return re.compile(allow_space_between_letters(pattern))

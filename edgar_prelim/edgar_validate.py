from typing import List, Iterable, Iterator

import pandas as pd

from edgar_prelim.edgar_items import PrelimItem, prelim_items
from edgar_prelim.edgar_query import FiscalPeriod


def validate_prelims(df: pd.DataFrame, items: List[PrelimItem] = None) -> pd.DataFrame:
    """Returns a pd.DataFrame that notes any missing or duplicate period, or outlier values in a company's data set."""
    if df.empty:
        return pd.DataFrame()

    if items is None:
        items = prelim_items

    first_period = str(FiscalPeriod.from_str(df.fiscal_period.min()) - 1)
    last_period = str(FiscalPeriod.from_str(df.fiscal_period.max()) + 1)
    cik = df.cik.iloc[0]
    res = []
    df = df.reset_index().set_index(['item', 'filing_date']).sort_index()
    for item in items:
        def add_msg(msg_type: str, msg: str, msg_period=None):
            res.append({'cik': cik, 'item': item.name, 'period': msg_period, 'msg_type': msg_type, 'message': msg})

        item_df = df.loc[item.name] if item.name in df.index.levels[0] else pd.DataFrame()

        if item_df.empty:
            add_msg('empty', 'No values for item')
            continue

        for period in _compress_consecutive_periods(
                _find_missing_periods(item_df, start_period=first_period, end_period=last_period)):
            add_msg('missing', 'Missing period', period)

        for period in _compress_consecutive_periods(_find_duplicate_periods(item_df)):
            add_msg('duplicate', 'Duplicate period', period)

        for period in _compress_consecutive_periods(_find_outlier_periods(item_df)):
            add_msg('outlier', 'Potential outlier', period)

    return (pd.DataFrame(res)
                .sort_values(['item', 'period'])
                .set_index(['cik', 'item'])
                .loc[:, ['period', 'msg_type', 'message']]) if res else pd.DataFrame()


def _compress_consecutive_periods(periods: Iterable[str]) -> Iterator[str]:
    """Compresses consecutive periods into a single message for the whole range, to reduce verbosity."""
    start_period = None
    prior_period = None
    consecutive = 0

    def msg() -> str:
        if consecutive == 1:
            return str(prior_period)
        else:
            return f'{str(start_period)} to {str(prior_period)}: {consecutive} periods'

    for period in periods:
        if prior_period is None:
            prior_period = FiscalPeriod.from_str(period)
            start_period = prior_period
            consecutive = 1
        else:
            fp = FiscalPeriod.from_str(period)
            if fp - prior_period == 1:
                consecutive += 1
            else:
                yield msg()
                start_period = period
                consecutive = 1
            prior_period = fp

    if consecutive > 0:
        yield msg()


def _find_missing_periods(item_df: pd.DataFrame, start_period: str, end_period: str = None) -> Iterable[str]:
    """Finds any missing fiscal periods in the 'fiscal_period' column of the item_df."""
    fiscal_periods = [FiscalPeriod.from_str(start_period)]
    fiscal_periods.extend(
        item_df.query(f"fiscal_period > '{start_period}'")
            .fiscal_period
            .sort_values()
            .drop_duplicates()
            .map(FiscalPeriod.from_str)
    )
    if end_period:
        fiscal_periods.append(FiscalPeriod.from_str(end_period))

    return [
        str(fp2 - i)
        for row in range(1, len(fiscal_periods))
        for fp1, fp2 in [fiscal_periods[row - 1:row + 1]]
        for gap in [fp2 - fp1]
        if gap > 1
        for i in range(gap - 1, 0, -1)
    ]


def _find_duplicate_periods(item_df: pd.DataFrame, threshold: float = 0.25) -> Iterable[str]:
    """Finds any duplicate fiscal_periods where the item_values differ by more the threshold. """
    dup_periods = item_df.groupby('fiscal_period').item_value.agg(
        lambda v: any(v.rolling(window=2).apply(lambda w: abs(1.0 - w[1] / w[0]), raw=True).dropna() >= threshold)
    )
    return list(dup_periods[dup_periods].index)


def _find_outlier_periods(item_df: pd.DataFrame, threshold: float = 1e12) -> Iterable[str]:
    """Returns any fiscal_periods whose item_value exceeds the threshold. """
    outliers = abs(item_df.item_value) > threshold
    return list(item_df[outliers].fiscal_period.unique())

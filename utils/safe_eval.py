from typing import Any

import pandas as pd


def safe_eval(x: Any) -> Any:
    if pd.isna(x):
        return []
    if isinstance(x, str):
        try:
            return eval(x)
        except:  # noqa: E722
            return []
    return x

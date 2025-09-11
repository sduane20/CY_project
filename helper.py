import pandas as pd


def convert_types(df, types):
    """
    Convert DataFrame columns to specified types.
    If a column fails, report it.
    """
    if isinstance(types, list):
        types = {i: t for i, t in enumerate(types)}

    for col, dtype in types.items():
        try:
            col_name = df.columns[col] if isinstance(col, int) else col
            df[col_name] = _convert_series(df[col_name], dtype)
        except Exception as e:
            print(f"Error in column {col} ({col_name}): {e}")
            raise
    return df


def _convert_series(s, dtype):
    """Convert a single Series to the target dtype."""
    if dtype == "datetime64[ns]":
        return pd.to_datetime(s, errors="coerce", utc=False)
    elif dtype == int:
        return pd.to_numeric(s, errors="coerce").astype("Int64")
    elif dtype == float:
        return pd.to_numeric(s, errors="coerce")
    elif dtype == str:
        return s.astype("string")
    else:
        return s.astype(dtype)

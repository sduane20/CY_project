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


def build_address(data: pd.DataFrame) -> pd.DataFrame:
    """Builds a clean Address column and drops unnecessary columns."""

    # Fill NaNs in Dir
    data["Dir"] = data["Dir"].fillna("")

    # Build Address
    data["Address"] = (
        data["House_Nr"].astype(str).fillna("") + " " +
        data["Dir"].astype(str) + " " +
        data["Street_Name"].astype(str).fillna("") + " " +
        data["St_Type"].astype(str).fillna("") + " " +
        data["Zip"].astype(str).fillna("")
    )

    # Clean up spaces
    data["Address"] = data["Address"].str.replace(
        r"\s+", " ", regex=True).str.strip()

    # Drop unwanted columns
    drop_cols = ["House_Nr", "Dir", "Street_Name", "St_Type", "Post_Dir"]
    data = data.drop(columns=[col for col in drop_cols if col in data.columns])

    # Move Address to first column
    cols = ["Address"] + [col for col in data.columns if col != "Address"]
    data = data[cols]

    # Convert type with your helper
    data["Address"] = _convert_series(data["Address"], str)

    return data


def safe_mode(series, default="N/A"):
    if series.empty:
        return default
    mode_vals = series.mode()
    return mode_vals.iloc[0] if not mode_vals.empty else default
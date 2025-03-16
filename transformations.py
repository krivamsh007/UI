# -----------------------------------------------------------------------------
# Copyright (c) [2025] [Vamshi Krishna Nagabhyru]
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
#!/usr/bin/env python
import os, json, re, uuid, hashlib, logging, time
from datetime import datetime, timedelta
from functools import lru_cache
from decimal import Decimal, InvalidOperation
import pandas as pd
from pandas import NamedAgg
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def normalize_series(s, method="minmax"):
    """Normalizes a numeric Series using min-max or zscore normalization."""
    if method == "minmax":
        return (s - s.min()) / (s.max() - s.min()) if s.max() != s.min() else s - s.min()
    elif method == "zscore":
        return (s - s.mean()) / s.std() if s.std() != 0 else s - s.mean()
    else:
        logger.warning("Normalization method '%s' not recognized. Returning unnormalized series.", method)
        return s

def extract_numeric(text):
    """Extracts all digits from text as a single concatenated string."""
    nums = re.findall(r'\d+', str(text))
    return "".join(nums) if nums else ""

def next_working_day(date_obj):
    """Returns the next working day (skips weekends)."""
    if pd.isnull(date_obj):
        return date_obj
    next_day = date_obj + timedelta(days=1)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    return next_day

@lru_cache(maxsize=1024)
def cached_date_parse(val, dayfirst, locale):
    try:
        from dateutil import parser
        return parser.parse(val, dayfirst=dayfirst)
    except Exception:
        return None

def convert_to_parquet(input_filepath, header=0, output_filepath=None):
    ext = os.path.splitext(input_filepath)[1].lower()
    if output_filepath is None:
        output_filepath = os.path.join(
            os.path.dirname(input_filepath),
            os.path.basename(input_filepath) + ".parquet"
        )
    try:
        if os.path.exists(output_filepath):
            try:
                os.remove(output_filepath)
            except Exception as rm_err:
                logger.error("Failed to remove existing parquet file '%s': %s", output_filepath, rm_err)
        if ext in [".csv", ".txt"]:
            df = pd.read_csv(input_filepath, header=header)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(input_filepath, header=header)
        else:
            df = pd.read_csv(input_filepath, header=header)
        df.to_parquet(output_filepath, index=False, engine="pyarrow")
        logger.info("Successfully converted to Parquet: %s", output_filepath)
        return output_filepath
    except Exception as e:
        logger.error("Conversion failed: %s", e)
        return input_filepath
def apply_transform_unique(df, info):
    """Returns the unique values from a column in a new column (as an array)."""
    col = info.get("column")
    new_col = info.get("new_column", f"{col}_unique")
    if col:
        unique_vals = df[col].drop_duplicates().tolist()
        df[new_col] = [unique_vals] * len(df)
    else:
        logger.warning("Unique: no column specified.")
    return df

def apply_transform_sort_array(df, info):
    """Sorts the unique values of a column and returns them in a new column."""
    col = info.get("column")
    ascending = info.get("ascending", True)
    new_col = info.get("new_column", f"{col}_sorted")
    if col:
        unique_vals = sorted(df[col].dropna().unique(), reverse=not ascending)
        df[new_col] = [unique_vals] * len(df)
    else:
        logger.warning("Sort Array: no column specified.")
    return df

# =============================================================================
# Category 2: Financial Functions
# =============================================================================

def calculate_npv(rate, cashflows):
    """Calculates the Net Present Value (NPV) of a series of cashflows."""
    npv = 0
    for t, cf in enumerate(cashflows, start=1):
        npv += cf / ((1 + rate) ** t)
    return npv

def apply_transform_npv(df, info):
    """Applies NPV calculation to a column containing cashflow lists."""
    discount_rate = info.get("discount_rate", 0.1)
    cashflow_col = info.get("cashflow_column")
    new_col = info.get("new_column", "NPV")
    if cashflow_col:
        df[new_col] = df[cashflow_col].apply(lambda x: calculate_npv(discount_rate, x)
                                             if isinstance(x, (list, tuple)) else None)
    else:
        logger.warning("NPV: no cashflow column specified.")
    return df

def apply_transform_irr(df, info):
    """Calculates the Internal Rate of Return (IRR) for a cashflow list in a column."""
    cashflow_col = info.get("cashflow_column")
    new_col = info.get("new_column", "IRR")
    if cashflow_col:
        try:
            df[new_col] = df[cashflow_col].apply(lambda x: np.irr(x) if isinstance(x, (list, tuple)) else None)
        except Exception as e:
            logger.error("IRR calculation error: %s", e)
            df[new_col] = None
    else:
        logger.warning("IRR: no cashflow column specified.")
    return df

def apply_transform_pmt(df, info):
    """
    Calculates the payment (PMT) for a loan/investment given rate, number of periods (nper) and present value (pv).
    Formula: pmt = rate * pv * (1+rate)^nper / ((1+rate)^nper - 1)
    """
    rate = info.get("rate")
    nper = info.get("nper")
    pv = info.get("pv")
    new_col = info.get("new_column", "PMT")
    if rate is not None and nper is not None and pv is not None:
        try:
            payment = rate * pv * (1 + rate) ** nper / (((1 + rate) ** nper) - 1)
        except Exception as e:
            logger.error("PMT calculation error: %s", e)
            payment = None
        df[new_col] = payment
    else:
        logger.warning("PMT: Missing rate, nper, or pv.")
    return df

# =============================================================================
# Category 3: Date & Time Functions
# =============================================================================

def apply_transform_datedif(df, info):
    """
    Calculates the difference between two dates.
    Unit can be 'days', 'months', or 'years'.
    """
    start_col = info.get("start_date_column")
    end_col = info.get("end_date_column")
    unit = info.get("unit", "days")
    new_col = info.get("new_column", f"{start_col}_datedif")
    if start_col and end_col:
        df[start_col] = pd.to_datetime(df[start_col], errors='coerce')
        df[end_col] = pd.to_datetime(df[end_col], errors='coerce')
        if unit == "days":
            df[new_col] = (df[end_col] - df[start_col]).dt.days
        elif unit == "months":
            df[new_col] = (df[end_col].dt.year - df[start_col].dt.year) * 12 + (df[end_col].dt.month - df[start_col].dt.month)
        elif unit == "years":
            df[new_col] = df[end_col].dt.year - df[start_col].dt.year
        else:
            logger.warning("DATEDIF: unknown unit '%s'", unit)
    else:
        logger.warning("DATEDIF: missing start or end date column.")
    return df

def apply_transform_eomonth(df, info):
    """
    Calculates the end of month date for a given date column with an optional month offset.
    """
    date_col = info.get("date_column")
    months = info.get("months", 0)
    new_col = info.get("new_column", f"{date_col}_eomonth")
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df[new_col] = df[date_col].apply(lambda d: (d + pd.DateOffset(months=months)).replace(day=1) + pd.DateOffset(months=1) - pd.DateOffset(days=1) if pd.notnull(d) else d)
    else:
        logger.warning("EOMONTH: missing date column.")
    return df

def apply_transform_weekday(df, info):
    """
    Extracts the weekday name from a date column.
    """
    date_col = info.get("date_column")
    new_col = info.get("new_column", f"{date_col}_weekday")
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df[new_col] = df[date_col].dt.day_name()
    else:
        logger.warning("WEEKDAY: missing date column.")
    return df

# =============================================================================
# Category 4: Statistical Functions
# =============================================================================

def apply_transform_median(df, info):
    """Calculates the median of a column and writes the value to a new column."""
    col = info.get("column")
    new_col = info.get("new_column", f"{col}_median")
    if col:
        median_val = df[col].median()
        df[new_col] = median_val
    else:
        logger.warning("Median: missing column.")
    return df

def apply_transform_std(df, info):
    """Calculates the standard deviation of a column and writes the value to a new column."""
    col = info.get("column")
    new_col = info.get("new_column", f"{col}_std")
    if col:
        std_val = df[col].std()
        df[new_col] = std_val
    else:
        logger.warning("Standard Deviation: missing column.")
    return df

def apply_transform_percentile(df, info):
    """Calculates a specified percentile for a column and writes the result to a new column."""
    col = info.get("column")
    percentile = info.get("percentile", 50)
    new_col = info.get("new_column", f"{col}_percentile_{percentile}")
    if col:
        perc_val = df[col].quantile(percentile / 100.0)
        df[new_col] = perc_val
    else:
        logger.warning("Percentile: missing column.")
    return df

def apply_transform_mode(df, info):
    """Calculates the mode of a column and writes the first mode value to a new column."""
    col = info.get("column")
    new_col = info.get("new_column", f"{col}_mode")
    if col:
        mode_val = df[col].mode()
        df[new_col] = mode_val[0] if not mode_val.empty else None
    else:
        logger.warning("Mode: missing column.")
    return df

# =============================================================================
# Category 5: Mathematical Functions
# =============================================================================

def apply_transform_abs(df, info):
    """Calculates the absolute value of a numeric column."""
    col = info.get("column")
    new_col = info.get("new_column", f"{col}_abs")
    if col:
        df[new_col] = df[col].abs()
    else:
        logger.warning("Absolute: missing column.")
    return df

def apply_transform_power(df, info):
    """Raises a column to a given power."""
    col = info.get("column")
    exponent = info.get("exponent", 2)
    new_col = info.get("new_column", f"{col}_power")
    if col:
        df[new_col] = df[col] ** exponent
    else:
        logger.warning("Power: missing column.")
    return df

def apply_transform_sqrt(df, info):
    """Calculates the square root of a column (returns None for negative values)."""
    col = info.get("column")
    new_col = info.get("new_column", f"{col}_sqrt")
    if col:
        df[new_col] = df[col].apply(lambda x: np.sqrt(x) if x >= 0 else None)
    else:
        logger.warning("Square Root: missing column.")
    return df

# =============================================================================
# Category 6: Text Functions
# =============================================================================

def apply_transform_left(df, info):
    """Returns the leftmost n characters of a text column."""
    col = info.get("column")
    num_chars = info.get("num_chars", 1)
    new_col = info.get("new_column", f"{col}_left")
    if col:
        df[new_col] = df[col].astype(str).str[:num_chars]
    else:
        logger.warning("LEFT: missing column.")
    return df

def apply_transform_right(df, info):
    """Returns the rightmost n characters of a text column."""
    col = info.get("column")
    num_chars = info.get("num_chars", 1)
    new_col = info.get("new_column", f"{col}_right")
    if col:
        df[new_col] = df[col].astype(str).str[-num_chars:]
    else:
        logger.warning("RIGHT: missing column.")
    return df

def apply_transform_mid(df, info):
    """Extracts a substring from a text column starting at a given position for a given length."""
    col = info.get("column")
    start = info.get("start", 0)
    num_chars = info.get("num_chars", None)
    new_col = info.get("new_column", f"{col}_mid")
    if col:
        s = df[col].astype(str)
        if num_chars is not None:
            df[new_col] = s.str.slice(start, start + num_chars)
        else:
            df[new_col] = s.str.slice(start)
    else:
        logger.warning("MID: missing column.")
    return df

def apply_transform_len(df, info):
    """Calculates the length of text in a column."""
    col = info.get("column")
    new_col = info.get("new_column", f"{col}_len")
    if col:
        df[new_col] = df[col].astype(str).str.len()
    else:
        logger.warning("LEN: missing column.")
    return df

def apply_transform_textjoin(df, info):
    """Joins text from multiple columns using a specified delimiter."""
    cols = info.get("columns", [])
    delimiter = info.get("delimiter", " ")
    new_col = info.get("new_column", "text_join")
    if cols:
        df[new_col] = df[cols].astype(str).agg(delimiter.join, axis=1)
    else:
        logger.warning("TEXTJOIN: missing columns.")
    return df

# =============================================================================
# Category 7: Logical Functions
# =============================================================================

def apply_transform_if(df, info):
    """
    Simulates an IF function.
    Expects a 'condition' string that can be evaluated with 'eval' (using df and np in context).
    """
    col = info.get("column")
    condition = info.get("condition")  # e.g., "df['{}'] > 5".format(col)
    true_value = info.get("true_value")
    false_value = info.get("false_value")
    new_col = info.get("new_column", f"{col}_if")
    if col and condition:
        try:
            df[new_col] = np.where(eval(condition, {"df": df, "np": np}), true_value, false_value)
        except Exception as e:
            logger.error("IF function error: %s", e)
    else:
        logger.warning("IF: missing required parameters.")
    return df

def apply_transform_iferror(df, info):
    """
    Simulates IFERROR: if a cell is an error (or NaN), replace with a fallback value.
    """
    col = info.get("column")
    fallback = info.get("fallback")
    new_col = info.get("new_column", f"{col}_iferror")
    if col:
        df[new_col] = df[col].fillna(fallback)
    else:
        logger.warning("IFERROR: missing column.")
    return df

# =============================================================================
# Category 8: Lookup & Reference Functions
# =============================================================================

def apply_transform_xlookup(df, info):
    """
    Implements a basic XLOOKUP: merges a lookup table (provided as a list of dicts)
    with the main DataFrame.
    """
    source_col = info.get("source_column")
    lookup_table = info.get("lookup_table")
    lookup_key = info.get("lookup_key")
    lookup_value = info.get("lookup_value")
    new_col = info.get("new_column", f"{source_col}_xlookup")
    if source_col and lookup_table and lookup_key and lookup_value:
        lookup_df = pd.DataFrame(lookup_table)
        if lookup_key not in lookup_df.columns or lookup_value not in lookup_df.columns:
            logger.error("XLOOKUP: Key or value column not in lookup table.")
            return df
        df = pd.merge(df, lookup_df[[lookup_key, lookup_value]], how='left', left_on=source_col, right_on=lookup_key)
        df.rename(columns={lookup_value: new_col}, inplace=True)
    else:
        logger.warning("XLOOKUP: missing required parameters.")
    return df

def apply_transform_index_match(df, info):

    source_col = info.get("source_column")
    lookup_table = info.get("lookup_table")
    lookup_key = info.get("lookup_key")
    return_col = info.get("return_column")
    new_col = info.get("new_column", f"{source_col}_indexmatch")
    if source_col and lookup_table and lookup_key and return_col:
        lookup_df = pd.DataFrame(lookup_table)
        if lookup_key not in lookup_df.columns or return_col not in lookup_df.columns:
            logger.error("INDEX/MATCH: required columns not in lookup table.")
            return df
        df = pd.merge(df, lookup_df[[lookup_key, return_col]], how='left', left_on=source_col, right_on=lookup_key)
        df.rename(columns={return_col: new_col}, inplace=True)
    else:
        logger.warning("INDEX/MATCH: missing required parameters.")
    return df
# =============================================================================
# Existing Transformation Functions (unchanged, but now grouped by purpose)
# =============================================================================
def single_friendly_to_internal(friendly, registry):
    for internal, friendly_name in registry.items():
        if friendly_name == friendly:
            return internal
    return None 

def apply_transform_drop_columns(df, info, transformation_config=None):
    print("Applying Drop Columns transformation...", info)
    friendly_cols_to_drop = info.get("columns_to_drop", [])
    registry = info.get("registry", {})
    internal_cols_to_drop = [single_friendly_to_internal(friendly, registry) for friendly in friendly_cols_to_drop]

    if transformation_config:
        for trans_key, trans_info in transformation_config.items():
            if trans_key == "Drop Columns":
                continue  # Skip self
            # Check keys that might reference a column
            for key in ["column", "columns"]:
                if key in trans_info:
                    ref = trans_info[key]
                    if isinstance(ref, list):
                        for col in ref:
                            friendly = single_friendly_to_internal(col, registry)
                            if friendly in friendly_cols_to_drop:
                                logger.warning("Column '%s' is referenced in transformation '%s' and cannot be dropped.", friendly, trans_key)
                                raise ValueError(f"Cannot drop column '{friendly}' because it is used in transformation '{trans_key}'.")
                    elif isinstance(ref, str):
                        friendly = single_friendly_to_internal(ref, registry)
                        if friendly in friendly_cols_to_drop:
                            logger.warning("Column '%s' is referenced in transformation '%s' and cannot be dropped.", friendly, trans_key)
                            raise ValueError(f"Cannot drop column '{friendly}' because it is used in transformation '{trans_key}'.")

    try:
        df = df.drop(columns=internal_cols_to_drop, errors='ignore')
    except Exception as e:
        logger.error("Error dropping columns %s: %s", internal_cols_to_drop, e)
    return df

def apply_transform_drop_unnamed_columns(df, info):
    try:
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    except Exception as e:
        logger.error("Error dropping unnamed columns: %s", e)
    return df

def apply_transform_remove_duplicates(df, info):
    cols = info.get("columns_to_dedup", [])
    keep = info.get("keep", "first")
    if cols:
        try:
            if keep in ["first", "last"]:
                df = df.drop_duplicates(subset=cols, keep=keep)
            elif keep == "none":
                df = df[~df.duplicated(subset=cols, keep=False)]
        except Exception as e:
            logger.error("Error removing duplicates on %s: %s", cols, e)
    else:
        logger.warning("Remove Duplicates: no columns specified.")
    return df

def apply_transform_detect_outliers(df, info):
    col = info.get("column")
    method = info.get("method", "zscore").lower()
    try:
        threshold = float(info.get("threshold", 3.0))
    except:
        threshold = 3.0
    new_flag = info.get("new_flag", f"{col}_outlier")
    
    if col and new_flag:
        try:
            series = pd.to_numeric(df[col], errors='coerce')
            if method == "zscore":
                mean = series.mean()
                std = series.std()
                df[new_flag] = ((series - mean).abs() > threshold * std)
            elif method == "iqr":
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                df[new_flag] = ((series < Q1 - threshold * IQR) | (series > Q3 + threshold * IQR))
            elif method == "mad":
                median = series.median()
                mad = np.median(np.abs(series - median))
                df[new_flag] = (np.abs(series - median) > threshold * mad)
            else:
                # Fallback to Z-score if method is unrecognized.
                mean = series.mean()
                std = series.std()
                df[new_flag] = ((series - mean).abs() > threshold * std)
        except Exception as e:
            print(f"Error in outlier detection: {e}")
    else:
        print("Detect Outliers: Missing required parameter 'column' or 'new_flag'.")
    return df

def apply_transform_flag_missing(df, info):
    if isinstance(info.get("columns"), dict):
        mapping = info["columns"]
        for col, new_flag in mapping.items():
            df[new_flag] = df[col].isnull()
    else:
        cols = info.get("columns")
        new_flags = info.get("new_flag")
        if cols:
            if not isinstance(cols, list):
                cols = [cols]
            if new_flags is None:
                new_flags = [f"{col}_missing" for col in cols]
            elif not isinstance(new_flags, list):
                new_flags = [new_flags] * len(cols)
            for col, new_flag in zip(cols, new_flags):
                df[new_flag] = df[col].isnull()
        else:
            logger.warning("Flag Missing Values: no columns specified.")
    return df

def apply_transform_generate_unique_ids(df, info):

    new_col = info.get("new_column", "").strip()
    method = info.get("method", "sequence").strip().lower()
    if not new_col:
        logger.warning("Generate Unique IDs: 'new_column' parameter is missing.")
        return df
    if method == "sequence":
        df[new_col] = np.arange(1, len(df) + 1)
    
    elif method == "uuid":
        df[new_col] = [str(uuid.uuid4()) for _ in range(len(df))]
    
    elif method == "hashkey":
        cols = info.get("columns", [])
        if not cols:
            logger.warning("Generate Unique IDs (hashkey): No columns specified.")
            return df

        missing_cols = [col for col in cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Generate Unique IDs (hashkey): Missing columns {missing_cols}")
            return df

        combined = df[cols].astype(str).agg('_'.join, axis=1)
        vectorized_hash = np.vectorize(lambda s: hashlib.sha256(s.encode('utf-8')).hexdigest())
        df[new_col] = vectorized_hash(combined)
    else:
        logger.warning(f"Generate Unique IDs: Unknown method '{method}'.")
    return df

def apply_transform_lag_column(df, info):
    col_name = info.get("column")
    periods = info.get("periods") or info.get("lag")
    new_col = info.get("new_column") or (f"{col_name}_lag" if col_name else None)
    if col_name and new_col and periods is not None:
        try:
            df[new_col] = df[col_name].shift(int(periods))
        except Exception as e:
            logger.error("Lag Column error for %s: %s", col_name, e)
    else:
        logger.warning("Lag Column: missing required parameters.")
    return df

def apply_transform_rank_values(df, info):
    col_name = info.get("column")
    method = info.get("method", "min")
    new_col = info.get("new_column") or (f"{col_name}_rank" if col_name else None)
    if col_name and new_col:
        ascending = True
        if "desc" in method.lower():
            ascending = False
        df[new_col] = df[col_name].rank(method='min', ascending=ascending)
    else:
        logger.warning("Rank Values: missing required parameters.")
    return df

def apply_transform_split_column(df, info):
    col_name = info.get("split_column")
    split_char = info.get("split_char")
    maxsplit = info.get("maxsplit", 1)
    if col_name and split_char:
        try:
            new_cols = df[col_name].astype(str).str.split(split_char, n=maxsplit, expand=True)
            for i in range(new_cols.shape[1]):
                df[f"{col_name}_part{i+1}"] = new_cols[i]
        except Exception as e:
            logger.error("Split Column error for %s: %s", col_name, e)
    else:
        logger.warning("Split Column: missing required parameters.")
    return df

def apply_transform_concatenate_columns(df, info):
    cols = info.get("columns", [])
    delim = info.get("delimiter", " ")
    new_col = info.get("new_column")
    if cols and new_col:
        try:
            df[new_col] = df[cols].astype(str).agg(delim.join, axis=1)
        except Exception as e:
            logger.error("Concatenate Columns error: %s", e)
    else:
        logger.warning("Concatenate Columns: missing required parameters.")
    return df

def apply_transform_pivot_data(df, info):
    index = info.get("index")
    columns = info.get("columns")
    values = info.get("values")
    aggfunc = info.get("aggfunc", "sum")
    fill_value = info.get("fill_value", None)
    if index and columns and values:
        try:
            df = df.pivot_table(
                index=index, columns=columns, values=values,
                aggfunc=aggfunc, fill_value=fill_value
            ).reset_index()
        except Exception as e:
            logger.error("Pivot Data error: %s", e)
        return df
    else:
        logger.warning("Pivot Data: missing required parameters.")
    return df

def apply_transform_unpivot_data(df, info):
    id_vars = info.get("id_vars", [])
    value_vars = info.get("value_vars", [])
    if id_vars and value_vars:
        try:
            df = pd.melt(df, id_vars=id_vars, value_vars=value_vars)
        except Exception as e:
            logger.error("Unpivot Data error: %s", e)
    else:
        logger.warning("Unpivot Data: missing required parameters.")
    return df

def apply_transform_transpose_data(df, info):
    try:
        df = df.transpose().reset_index()
    except Exception as e:
        logger.error("Transpose Data error: %s", e)
    return df

def apply_transform_group_aggregate(df, info):

    group_cols = info.get("group_columns", [])
    aggregations = info.get("aggregations", {})
    new_names = info.get("new_names", {})
    having = info.get("having", {})

    if not group_cols or not aggregations:
        logger.warning("Group & Aggregate: missing 'group_columns' or 'aggregations'.")
        return df

    try:
        agg_dict = {}
        rename_map = {}  # single-level rename: "col_2_count" -> "NameCnt"

        for col, agg_spec in aggregations.items():
            if isinstance(agg_spec, list):
                funcs = agg_spec
            elif isinstance(agg_spec, dict):
                funcs = list(agg_spec.keys())  # e.g. {"count": None, "mean": None}
            else:
                funcs = [agg_spec]

            for func in funcs:
                if isinstance(func, str) and func.lower() == "count_distinct":
                    aggfunc = lambda x: x.nunique()
                else:
                    aggfunc = func
                col_func = f"{col}_{func}"
                agg_dict[col_func] = NamedAgg(column=col, aggfunc=aggfunc)
                alias = new_names.get((col, func), col_func)
                rename_map[col_func] = alias
        grouped = df.groupby(group_cols, as_index=False).agg(**agg_dict)
        if isinstance(grouped.columns, pd.MultiIndex):
            new_cols = []
            for col_tuple in grouped.columns:
                if col_tuple[0] in group_cols and len(col_tuple) == 2 and not col_tuple[1]:
                    new_cols.append(col_tuple[0])
                else:
                    if len(col_tuple) == 2 and col_tuple[0] in rename_map:
                        new_cols.append(rename_map[col_tuple[0]])
                    else:
                        new_cols.append("_".join(x for x in col_tuple if x))
            grouped.columns = new_cols
        else:
            grouped = grouped.rename(columns=rename_map)
        if having:
            for alias_col, condition in having.items():
                try:
                    grouped = grouped.query(f"`{alias_col}` {condition}")
                except Exception as e:
                    logger.error("Error applying HAVING condition on %s: %s", alias_col, e)

        return grouped

    except Exception as e:
        logger.error("Group & Aggregate error: %s", e)
        return df

def apply_transform_sort_data(df, info):
    sort_cols = info.get("columns", [])
    ascending = info.get("ascending", True)
    if sort_cols:
        try:
            df = df.sort_values(by=sort_cols, ascending=ascending)
        except Exception as e:
            logger.error("Sort Data error: %s", e)
        return df
    else:
        logger.warning("Sort Data: no columns specified.")
    return df

def apply_transform_trim(df, info):
    columns_info = info.get("columns", {})
    if not columns_info:
        logger.warning("No columns provided for transformation.")
        return df

    for col, settings in columns_info.items():
        if col not in df.columns:
            logger.warning("Trim: Column '%s' not found in DataFrame.", col)
            continue  # Skip missing columns
        operations = settings.get("operations", [])
        custom_char = settings.get("custom_char", None)
        s = df[col].astype(str)
        if "Trim Spaces" in operations:
            s = s.str.strip()
        if "Remove Extra Spaces" in operations:
            s = s.str.replace(r'\s+', ' ', regex=True).str.strip()
        if "Remove Custom Characters" in operations and custom_char:
            pattern = f"[{re.escape(custom_char)}]+"
            s = s.str.replace(pattern, '', regex=True)
        if "Remove Special Characters" in operations:
            s = s.str.replace(r'[^\w\s]', '', regex=True)
        if "Remove Non-UTF Characters" in operations:
            s = s.str.replace(r'[^\x00-\x7F]+', '', regex=True)
        # Apply transformations to the DataFrame
        df[col] = s

    return df

def apply_transform_change_case(df, info):
    columns = info.get("columns", {})  # Dictionary: {column_name: conversion_type}
    if not columns:
        logger.warning("Change Case: No columns specified.")
        return df
    for col, conversion in columns.items():
        if col in df.columns:
            s = df[col].astype(str)  # Ensure column is treated as string
            if conversion == "uppercase":
                df[col] = s.str.upper()
            elif conversion == "lowercase":
                df[col] = s.str.lower()
            elif conversion == "title":
                df[col] = s.str.title()
            elif conversion == "capitalize":
                df[col] = s.str.capitalize()
            else:
                logger.warning("Unknown case conversion method: %s for column %s", conversion, col)
        else:
            logger.warning("Change Case: Column '%s' not found in DataFrame.", col)
    return df

def apply_transform_replace_substring(df, info):
    columns_info = info.get("columns", {})
    if not columns_info:
        logger.warning("Replace Substring: No columns provided.")
        return df

    for col, settings in columns_info.items():
        old_sub = settings.get("old_sub")
        new_sub = settings.get("new_sub")
        case_sensitive = settings.get("case_sensitive", True)
        global_replace = settings.get("global", True)

        if col not in df.columns:
            logger.warning(f"Replace Substring: Column '{col}' not found in DataFrame. Skipping...")
            continue

        if old_sub is None or new_sub is None:
            logger.warning(f"Replace Substring: Missing parameters for column '{col}'. Skipping...")
            continue
        s = df[col].astype(str)
        if case_sensitive:
            df[col] = s.str.replace(old_sub, new_sub, regex=global_replace)
        else:
            df[col] = s.str.replace(old_sub, new_sub, flags=re.IGNORECASE, regex=True)
    return df


def apply_transform_fill_missing(df, info):
    col = info.get("column")
    method = info.get("method", "Constant")
    fill_limit = info.get("fill_limit", None)
    if col:
        try:
            if method == "Constant":
                constant = info.get("constant", "")
                df[col] = df[col].fillna(constant, limit=fill_limit)
            elif method == "Forward Fill":
                df[col] = df[col].fillna(method='ffill', limit=fill_limit)
            elif method == "Backward Fill":
                df[col] = df[col].fillna(method='bfill', limit=fill_limit)
            elif method == "Mean":
                df[col] = df[col].fillna(pd.to_numeric(df[col], errors='coerce').mean())
            elif method == "Median":
                df[col] = df[col].fillna(pd.to_numeric(df[col], errors='coerce').median())
        except Exception as e:
            logger.error("Fill Missing Values error for column %s: %s", col, e)
    else:
        logger.warning("Fill Missing Values: no column specified.")
    return df

def apply_transform_convert_datatype(df, info):

    columns_info = info.get("columns", {})
    if not columns_info:
        logger.warning("Convert Datatype: No columns provided for conversion.")
        return df
    for col_name, settings in columns_info.items():
        if col_name not in df.columns:
            logger.warning(f"Convert Datatype: Column '{col_name}' not found in DataFrame. Skipping.")
            continue
        target = settings.get("new_type", "").strip().lower()
        errors = settings.get("errors", "coerce")
        default_value = settings.get("default_value", "").strip()
        if not target:
            logger.warning(f"Convert Datatype: No target type specified for column '{col_name}'. Skipping.")
            continue
        try:
            if target in ["datetime", "date"]:
                
                df[col_name] = df[col_name].astype(str).str.strip("'\" ").replace({"": np.nan, "nan": np.nan})
               
                date_formats = ["%d-%m-%Y", "%m-%d-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
                def parse_date(value):
                    if pd.isna(value) or str(value).strip() == "":
                        return pd.NaT  # Preserve NaN for missing values
                   
                    for fmt in date_formats:
                        try:
                            return pd.to_datetime(value, format=fmt)
                        except Exception:
                            continue
                    return pd.NaT  # If all formats fail, return NaT
                df[col_name] = df[col_name].apply(parse_date)

                if default_value:
                    try:
                        default_dt = pd.to_datetime(default_value, errors="coerce")
                        df[col_name].fillna(default_dt, inplace=True)
                    except Exception as e:
                        logger.warning(f"Could not parse default_date '{default_value}' for column '{col_name}': {e}")
            elif target == "int":
                df[col_name] = pd.to_numeric(df[col_name], errors=errors).astype("Int64")
                if default_value:
                    df[col_name].fillna(int(default_value), inplace=True)
            elif target == "float":
                df[col_name] = pd.to_numeric(df[col_name], errors=errors)
                if default_value:
                    df[col_name].fillna(float(default_value), inplace=True)
            elif target == "boolean":
                df[col_name] = df[col_name].astype(bool)
                if default_value.lower() in ["true", "false"]:
                    df[col_name].fillna(default_value.lower() == "true", inplace=True)
            elif target == "category":
                df[col_name] = df[col_name].astype("category")
                if default_value:
                    df[col_name].fillna(default_value, inplace=True)
            elif target == "decimal":
                df[col_name] = df[col_name].apply(lambda x: Decimal(str(x)) if pd.notnull(x) else None)
                if default_value:
                    df[col_name].fillna(Decimal(default_value), inplace=True)
            elif target == "json":
                df[col_name] = df[col_name].apply(lambda x: json.loads(x) if pd.notnull(x) else None)
                if default_value:
                    df[col_name].fillna(json.loads(default_value), inplace=True)
            elif target == "list":
                df[col_name] = df[col_name].apply(lambda x: json.loads(x) if pd.notnull(x) else None)
                if default_value:
                    df[col_name].fillna(json.loads(default_value), inplace=True)
            elif target == "timedelta":
                timestamp_unit = settings.get("timestamp_unit", "d")
                df[col_name] = pd.to_timedelta(df[col_name], errors=errors, unit=timestamp_unit)
                if default_value:
                    df[col_name].fillna(pd.to_timedelta(default_value, unit=timestamp_unit), inplace=True)
            elif target in ["str", "string"]:
                df[col_name] = df[col_name].astype(str)
                if default_value:
                    df[col_name].fillna(default_value, inplace=True)
            else:
                logger.warning(f"Convert Datatype: Unknown target type '{target}' for column '{col_name}'. Converting to string.")
                df[col_name] = df[col_name].astype(str)
                if default_value:
                    df[col_name].fillna(default_value, inplace=True)
        except Exception as e:
            logger.error(f"Convert Datatype error for column '{col_name}': {e}")
    return df

def apply_transform_standardize_date_format(df, info):

    col = info.get("column")
    fmt = info.get("date_format", "%Y-%m-%d")
    timezone = info.get("timezone", None)
    input_formats = info.get("input_formats", None)
    
    if col and fmt:
        try:
            # Attempt parsing using provided input format (if any)
            if input_formats:
                if isinstance(input_formats, list):
                    fmt_list = input_formats
                else:
                    fmt_list = [input_formats]
                dt_series = None
                for f in fmt_list:
                    dt_series = pd.to_datetime(df[col], errors='coerce', format=f)
                    if not dt_series.isnull().all():
                        break
                if dt_series is None or dt_series.isnull().all():
                    dt_series = pd.to_datetime(df[col], errors='coerce')
            else:
                dt_series = pd.to_datetime(df[col], errors='coerce')
                
            if timezone:
                dt_series = dt_series.dt.tz_localize('UTC').dt.tz_convert(timezone)
            df[col] = dt_series.dt.strftime(fmt)
        except Exception as e:
            logger.error("Standardize Date Format error for column %s: %s", col, e)
    else:
        logger.warning("Standardize Date Format: missing required parameters.")
    return df

def apply_transform_normalize_data(df, info):
    col = info.get("column")
    norm_method = info.get("norm_method", "minmax")
    if col:
        try:
            s = pd.to_numeric(df[col], errors='coerce')
            df[col] = normalize_series(s, method=norm_method)
        except Exception as e:
            logger.error("Normalize Data error for column %s: %s", col, e)
    else:
        logger.warning("Normalize Data: no column specified.")
    return df

def apply_transform_substring(df, info):
    col = info.get("column")
    try:
        start = int(info.get("start", 0))
    except Exception as e:
        logger.warning("Invalid start value, defaulting to 0: %s", e)
        start = 0
    num_chars = info.get("num_chars")
    end = info.get("end")
    new_col = info.get("new_column", f"{col}_substring")
    
    if col and new_col:
        s = df[col].astype(str)
        if num_chars is not None:
            try:
                num_chars = int(num_chars)
                df[new_col] = s.str.slice(start, start + num_chars)
            except Exception as e:
                logger.error("Error with num_chars conversion: %s", e)
                df[new_col] = s.str.slice(start)
        elif end is not None:
            try:
                end = int(end)
                df[new_col] = s.str.slice(start, end)
            except Exception as e:
                logger.error("Error with end conversion: %s", e)
                df[new_col] = s.str.slice(start)
        else:
            df[new_col] = s.str.slice(start)
    else:
        logger.warning("Substring transformation missing required parameters.")
    return df

def apply_transform_extract_text_between(df, info):
    col = info.get("column")
    left_delim = info.get("left_delim")
    right_delim = info.get("right_delim")
    try:
        occurrence = int(info.get("occurrence", 1))
    except Exception as e:
        logger.warning("Invalid occurrence value, defaulting to 1: %s", e)
        occurrence = 1
    new_col = info.get("new_column", f"{col}_extracted")
    
    if col and left_delim and right_delim and new_col:
        pattern = re.escape(left_delim) + r'(.*?)' + re.escape(right_delim)
        def extract_func(x):
            matches = re.findall(pattern, str(x))
            if matches and len(matches) >= occurrence:
                return matches[occurrence-1]
            return ""
        df[new_col] = df[col].astype(str).apply(extract_func)
    else:
        logger.warning("Extract Text Between transformation missing required parameters.")
    return df

def apply_transform_extract_numeric(df, info):
    col = info.get("column")
    new_col = info.get("new_column", f"{col}_numeric")
    preserve_decimal = info.get("preserve_decimal", False)
    
    if col and new_col:
        if preserve_decimal:
            # Matches decimals (e.g., 123.45) and integers.
            pattern = r'(\d+\.\d+|\d+)'
        else:
            pattern = r'\d+'
        def extract_func(x):
            return "".join(re.findall(pattern, str(x)))
        df[new_col] = df[col].astype(str).apply(extract_func)
    else:
        logger.warning("Extract Numeric Values transformation missing required parameters.")
    return df

def apply_transform_round_numbers(df, info):
    col_name = info.get("column")
    decimals = info.get("decimals", 0)
    new_col = info.get("new_column")
    if col_name and new_col:
        try:
            df[new_col] = pd.to_numeric(df[col_name], errors='coerce').round(decimals)
        except Exception as e:
            logger.error("Round Numbers error for column %s: %s", col_name, e)
        return df
    else:
        logger.warning("Round Numbers: missing required parameters.")
    return df

def apply_transform_percentage_change(df, info):
    col_name = info.get("column")
    new_col = info.get("new_column")
    factor = info.get("factor", 100)
    if col_name and new_col:
        try:
            df[new_col] = df[col_name].pct_change() * factor
        except Exception as e:
            logger.error("Percentage Change error for column %s: %s", col_name, e)
        return df
    else:
        logger.warning("Percentage Change: missing required parameters.")
    return df

def apply_transform_bucketize_values(df, info):
    col_name = info.get("column")
    bins = info.get("bins")
    labels = info.get("labels", None)
    new_col = info.get("new_column", f"{col_name}_bucket" if col_name else None)
    if col_name and bins and new_col:
        try:
            df[new_col] = pd.cut(
                pd.to_numeric(df[col_name], errors='coerce'),
                bins=bins,
                labels=labels,
                include_lowest=True
            )
        except Exception as e:
            logger.error("Bucketize Values error for column %s: %s", col_name, e)
        return df
    else:
        logger.warning("Bucketize Values: missing required parameters.")
    return df

def apply_transform_extract_date_components(df, info):
    col_name = info.get("column")
    year_col = info.get("year", f"{col_name}_year")
    month_col = info.get("month", f"{col_name}_month")
    day_col = info.get("day", f"{col_name}_day")
    if col_name:
        try:
            date_series = pd.to_datetime(df[col_name], errors='coerce')
            df[year_col] = date_series.dt.year
            df[month_col] = date_series.dt.month
            df[day_col] = date_series.dt.day
        except Exception as e:
            logger.error("Extract Date Components error for column %s: %s", col_name, e)
        return df
    else:
        logger.warning("Extract Date Components: no column specified.")
    return df

def apply_transform_date_shift(df, info):
    col_name = info.get("column")
    shift_value = info.get("shift_value", 0)
    unit = info.get("unit", "d")
    new_col = info.get("new_column")
    if col_name and new_col:
        try:
            df[new_col] = pd.to_datetime(df[col_name], errors='coerce') + pd.to_timedelta(shift_value, unit=unit)
        except Exception as e:
            logger.error("Date Shift error for column %s: %s", col_name, e)
        return df
    else:
        logger.warning("Date Shift: missing required parameters.")
    return df

def apply_transform_next_working_day(df, info):
    col_name = info.get("column")
    new_col = info.get("new_column")
    if col_name and new_col:
        try:
            df[new_col] = pd.to_datetime(df[col_name], errors='coerce').apply(lambda d: next_working_day(d) if pd.notnull(d) else d)
        except Exception as e:
            logger.error("Next Working Day error for column %s: %s", col_name, e)
        return df
    else:
        logger.warning("Next Working Day: missing required parameters.")
    return df

def apply_transform_find_replace(df, info):
    col_name = info.get("column")
    find_text = info.get("find")
    replace_text = info.get("replace")
    if col_name and find_text is not None and replace_text is not None:
        try:
            df[col_name] = df[col_name].astype(str).str.replace(find_text, replace_text, regex=True)
        except Exception as e:
            logger.error("Find and Replace error for column %s: %s", col_name, e)
        return df
    else:
        logger.warning("Find and Replace: missing required parameters.")
    return df

def apply_transform_running_total(df, info):
    col_name = info.get("column")
    new_col = info.get("new_column") or (f"{col_name}_cumsum" if col_name else None)
    group_by = info.get("group_by", None)
    if col_name and new_col:
        try:
            if group_by and group_by in df.columns:
                df[new_col] = df.groupby(group_by)[pd.to_numeric(df[col_name], errors='coerce')].cumsum()
            else:
                df[new_col] = pd.to_numeric(df[col_name], errors='coerce').cumsum()
        except Exception as e:
            logger.error("Running Total error for column %s: %s", col_name, e)
        return df
    else:
        logger.warning("Running Total: missing required parameters.")
    return df

def apply_transform_moving_average(df, info):
    col_name = info.get("column")
    window = info.get("window", 3)
    new_col = info.get("new_column") or (f"{col_name}_moving_avg" if col_name else None)
    min_periods = info.get("min_periods", 1)
    if col_name and new_col:
        try:
            df[new_col] = pd.to_numeric(df[col_name], errors='coerce').rolling(window=window, min_periods=min_periods).mean()
        except Exception as e:
            logger.error("Moving Average error for column %s: %s", col_name, e)
        return df
    else:
        logger.warning("Moving Average: missing required parameters.")
    return df

def apply_transform_conditional_column(df, info):
    condition = info.get("condition")
    true_val = info.get("true_value")
    false_val = info.get("false_value")
    new_col = info.get("new_column")
    if condition is not None and new_col:
        try:
            df[new_col] = np.where(df.eval(condition), true_val, false_val)
        except Exception as e:
            logger.error("Conditional Column Creation error: %s", e)
        return df
    else:
        logger.warning("Conditional Column Creation: missing required parameters.")
    return df

def apply_transform_custom_function(df, info):
    func = info.get("function")
    if func:
        if callable(func):
            try:
                df = func(df)
            except Exception as e:
                logger.error("Custom Function error: %s", e)
        elif isinstance(func, str) and func in {}:  # CUSTOM_FUNCTIONS dictionary if you register functions
            try:
                df = {}[func](df)
            except Exception as e:
                logger.error("Custom Function '%s' error: %s", func, e)
        else:
            logger.warning("Custom Function: provided function is not callable or not registered.")
    else:
        logger.warning("Custom Function: no function provided.")
    return df

def apply_transform_analytical_functions(df, info):
    group_cols = info.get("group_columns", [])
    analytical = info.get("analytical", {})
    if not group_cols or not analytical:
        logger.warning("Analytical Functions: missing 'group_columns' or 'analytical' config.")
        return df
    for target_col, funcs in analytical.items():
        for func_name, params in funcs.items():
            new_col = params.get("new_column", f"{target_col}_{func_name}")
            try:
                order_by = params.get("order_by", None)
                if func_name == "rank":
                    method = params.get("method", "min")
                    if order_by:
                        df[new_col] = (
                            df.groupby(group_cols, group_keys=False)
                              .apply(lambda x: x.sort_values(order_by)[target_col].rank(method=method))
                              .reset_index(level=0, drop=True)
                        )
                    else:
                        df[new_col] = df.groupby(group_cols)[target_col].rank(method=method)
                elif func_name == "dense_rank":
                    if order_by:
                        df[new_col] = (
                            df.groupby(group_cols, group_keys=False)
                              .apply(lambda x: x.sort_values(order_by)[target_col].rank(method="dense"))
                              .reset_index(level=0, drop=True)
                        )
                    else:
                        df[new_col] = df.groupby(group_cols)[target_col].rank(method="dense")
                elif func_name == "percent_rank":
                    if order_by:
                        df[new_col] = (
                            df.groupby(group_cols, group_keys=False)
                              .apply(lambda x: ((x.sort_values(order_by)[target_col].rank(method="min") - 1) / (len(x) - 1)
                                                 if len(x) > 1 else 0))
                              .reset_index(level=0, drop=True)
                        )
                    else:
                        df[new_col] = df.groupby(group_cols)[target_col].transform(
                            lambda x: (x.rank(method="min") - 1) / (len(x) - 1) if len(x) > 1 else 0
                        )
                elif func_name == "row_number":
                    if order_by:
                        df[new_col] = (
                            df.groupby(group_cols, group_keys=False)
                              .apply(lambda x: x.sort_values(order_by).reset_index(drop=True).index + 1)
                              .reset_index(level=0, drop=True)
                        )
                    else:
                        df[new_col] = df.groupby(group_cols, group_keys=False).cumcount() + 1
                elif func_name == "cumsum":
                    df[new_col] = df.groupby(group_cols)[target_col].cumsum()
                elif func_name.startswith("rolling_"):
                    window = params.get("window", 3)
                    min_periods = params.get("min_periods", 1)
                    roll_type = func_name.split("_", 1)[1]
                    if roll_type in ["mean", "sum", "count", "min", "max", "std", "var", "median"]:
                        df[new_col] = df.groupby(group_cols)[target_col].transform(
                            lambda x: x.rolling(window=window, min_periods=min_periods).agg(roll_type)
                        )
                    else:
                        logger.warning("Unknown rolling function type: %s", roll_type)
                elif func_name == "lag":
                    periods = params.get("periods", 1)
                    df[new_col] = df.groupby(group_cols)[target_col].shift(periods)
                elif func_name == "lead":
                    periods = params.get("periods", 1)
                    df[new_col] = df.groupby(group_cols)[target_col].shift(-periods)
                elif func_name in ["sum", "mean", "count", "max", "min"]:
                    df[new_col] = df.groupby(group_cols)[target_col].transform(func_name)
                else:
                    logger.warning("Analytical function '%s' not recognized for column '%s'.", func_name, target_col)
            except Exception as e:
                logger.error("Analytical function '%s' error for column %s: %s", func_name, target_col, e)
    return df


# =============================================================================
# Transformation Dispatcher Functions
# =============================================================================

def apply_transformations(df, transformation_config):
    """
    Applies transformations in order based on a 'sequence' key in each transformation's configuration.
    """
    steps = [(info.get("sequence", 9999), key, info) for key, info in transformation_config.items()]
    steps.sort(key=lambda x: x[0])
    for sequence, key, info in steps:
        #logger.info("Applying transformation: %s (sequence %s)", key, sequence)
        if key == "Drop Columns":
            # Pass the full transformation configuration to check dependencies.
            df = apply_transform_drop_columns(df, info, transformation_config=transformation_config)
        elif key == "Drop Unnamed Columns":
            df = apply_transform_drop_unnamed_columns(df, info)
        elif key in ("Rename Columns", "Rename Columns (Friendly)"):
            continue
        elif key == "Remove Duplicates":
            df = apply_transform_remove_duplicates(df, info)
        elif key == "Detect Outliers":
            df = apply_transform_detect_outliers(df, info)
        elif key == "Flag Missing Values":
            df = apply_transform_flag_missing(df, info)
        elif key == "Generate Unique IDs":
            df = apply_transform_generate_unique_ids(df, info)
        elif key == "Lag Column":
            df = apply_transform_lag_column(df, info)
        elif key == "Rank Values":
            df = apply_transform_rank_values(df, info)
        elif key == "Split Column":
            df = apply_transform_split_column(df, info)
        elif key == "Concatenate Columns":
            df = apply_transform_concatenate_columns(df, info)
        elif key == "Pivot Data":
            df = apply_transform_pivot_data(df, info)
        elif key == "Unpivot Data":
            df = apply_transform_unpivot_data(df, info)
        elif key == "Transpose Data":
            df = apply_transform_transpose_data(df, info)
        elif key == "Group & Aggregate":
            df = apply_transform_group_aggregate(df, info)
        elif key == "Sort Data":
            df = apply_transform_sort_data(df, info)
        elif key == "Trim":
            df = apply_transform_trim(df, info)
        elif key == "Change Case":
            df = apply_transform_change_case(df, info)
        elif key == "Replace Substring":
            df = apply_transform_replace_substring(df, info)
        elif key == "Fill Missing Values":
            df = apply_transform_fill_missing(df, info)
        elif key == "Convert Datatype":
            df = apply_transform_convert_datatype(df, info)
        elif key == "Standardize Date Format":
            df = apply_transform_standardize_date_format(df, info)
        elif key == "Normalize Data":
            df = apply_transform_normalize_data(df, info)
        elif key == "Extract Substrings":
            df = apply_transform_substring(df, info)
        elif key == "Extract Text Between":
            df = apply_transform_extract_text_between(df, info)
        elif key == "Extract Numeric Values":
            df = apply_transform_extract_numeric(df, info)
        elif key == "Round Numbers":
            df = apply_transform_round_numbers(df, info)
        elif key == "Percentage Change":
            df = apply_transform_percentage_change(df, info)
        elif key == "Bucketize Values":
            df = apply_transform_bucketize_values(df, info)
        elif key == "Extract Date Components":
            df = apply_transform_extract_date_components(df, info)
        elif key == "Date Shift":
            df = apply_transform_date_shift(df, info)
        elif key == "Next Working Day":
            df = apply_transform_next_working_day(df, info)
        elif key == "Find and Replace":
            df = apply_transform_find_replace(df, info)
        elif key == "Running Total":
            df = apply_transform_running_total(df, info)
        elif key == "Moving Average":
            df = apply_transform_moving_average(df, info)
        elif key == "Conditional Column Creation":
            df = apply_transform_conditional_column(df, info)
        elif key == "Custom Function":
            df = apply_transform_custom_function(df, info)
        elif key == "Analytical Functions":
            df = apply_transform_analytical_functions(df, info)
        # New functions
        elif key == "Unique":
            df = apply_transform_unique(df, info)
        elif key == "Sort Array":
            df = apply_transform_sort_array(df, info)
        elif key == "NPV":
            df = apply_transform_npv(df, info)
        elif key == "IRR":
            df = apply_transform_irr(df, info)
        elif key == "PMT":
            df = apply_transform_pmt(df, info)
        elif key == "DATEDIF":
            df = apply_transform_datedif(df, info)
        elif key == "EOMONTH":
            df = apply_transform_eomonth(df, info)
        elif key == "WEEKDAY":
            df = apply_transform_weekday(df, info)
        elif key == "Median":
            df = apply_transform_median(df, info)
        elif key == "Std":
            df = apply_transform_std(df, info)
        elif key == "Percentile":
            df = apply_transform_percentile(df, info)
        elif key == "Mode":
            df = apply_transform_mode(df, info)
        elif key == "Abs":
            df = apply_transform_abs(df, info)
        elif key == "Power":
            df = apply_transform_power(df, info)
        elif key == "Sqrt":
            df = apply_transform_sqrt(df, info)
        elif key == "LEFT":
            df = apply_transform_left(df, info)
        elif key == "RIGHT":
            df = apply_transform_right(df, info)
        elif key == "MID":
            df = apply_transform_mid(df, info)
        elif key == "LEN":
            df = apply_transform_len(df, info)
        elif key == "TEXTJOIN":
            df = apply_transform_textjoin(df, info)
        elif key == "IF":
            df = apply_transform_if(df, info)
        elif key == "IFERROR":
            df = apply_transform_iferror(df, info)
        elif key == "XLOOKUP":
            df = apply_transform_xlookup(df, info)
        elif key in ("INDEX/MATCH", "INDEX MATCH"):
            df = apply_transform_index_match(df, info)
        else:
            logger.warning("Unknown transformation key: %s. Skipping.", key)
    # Handle renaming after all transformations
    rename_info = {}
    if "Rename Columns" in transformation_config:
        rename_info.update(transformation_config["Rename Columns"].get("new_names", {}))
    if "Rename Columns (Friendly)" in transformation_config:
        rename_info.update(transformation_config["Rename Columns (Friendly)"])
    if rename_info:
        logger.info("Applying renaming: %s", rename_info)
        df = df.rename(columns=rename_info)
    return df

def apply_filters_and_transformations(df, config):
    filters = config.get("Filters", [])
    transformations = config.get("Transformations", {})
    df = apply_filters(df, filters)
    df = apply_transformations(df, transformations)
    return df

def apply_transformations_with_summary(df, transformation_config):
    summary = []
    initial_count = len(df)
    df = apply_filters(df, transformation_config.get("Filters", []))
    summary.append({
        "transformation": "Filters",
        "sequence": 1,
        "initial_count": initial_count,
        "new_count": len(df)
    })
    transformations = transformation_config.get("Transformations", {})
    steps = [(info.get("sequence", 9999), key, (info if isinstance(info, dict) else {}))
             for key, info in transformations.items()]
    steps.sort(key=lambda x: x[0])
    for sequence, key, info in steps:
        init_count = len(df)
        #logger.info("Applying transformation: %s (sequence %s)", key, sequence)
        df = apply_transformations(df, {key: info})
        new_count = len(df)
        summary.append({
            "transformation": key,
            "sequence": sequence,
            "initial_count": init_count,
            "new_count": new_count
        })
    if "Rename Columns" in transformations:
        rename_map = transformations["Rename Columns"].get("new_names", {})
        if rename_map:
            df = df.rename(columns=rename_map)
    if "Rename Columns (Friendly)" in transformations:
        rename_map = transformations["Rename Columns (Friendly)"]
        if rename_map:
            df = df.rename(columns=rename_map)
    return df, summary

def generate_transformation_summary_html(summary_list, source_count, final_count):
    """
    Builds an HTML-based transformation summary with a fancy, modern table style.
    Display this HTML in a QTextBrowser, QTextEdit, or QLabel that supports rich text.
    """
    # Sort by 'sequence' so transformations appear in order
    sorted_steps = sorted(summary_list, key=lambda x: x.get("sequence", 9999))

    enumerated_steps = []
    for i, step in enumerate(sorted_steps, start=1):
        enumerated_steps.append({
            "index": i,
            "transformation": step.get("transformation", "Unknown"),
            "initial_count": step.get("initial_count", ""),
            "new_count": step.get("new_count", "")
        })
    
    # Start building the HTML
    html_parts = []

    # Title
    html_parts.append("""
    <div style="font-family: 'Segoe UI', Tahoma, Arial, sans-serif; margin: 10px;">
      <h2 style="color: #2F80ED; margin-bottom: 6px;">Transformation Summary</h2>
    """)
    
    # Stats about initial/final counts
    html_parts.append(f"""
      <p style="margin: 4px 0;">
        <strong>Initial row count:</strong> {source_count}
        &nbsp; &nbsp;
        <strong>Final row count:</strong> {final_count}
      </p>
    """)
    html_parts.append("""
      <div style="border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); overflow: hidden; margin-top: 12px;">
      <table style="
        border-collapse: separate; 
        border-spacing: 0; 
        width: 100%; 
        font-size: 14px;
      ">
        <thead>
          <tr style="
            background: linear-gradient(to right, #2196F3, #6EC6FF); 
            color: #FFF;
            text-align: left;
          ">
            <th style="padding: 10px; border-right: 1px solid #bbdefb;">Seq</th>
            <th style="padding: 10px; border-right: 1px solid #bbdefb;">Transformation</th>
            <th style="padding: 10px;">Before</th>
            <th style="padding: 10px;">After</th>
          </tr>
        </thead>
        <tbody>
    """)
    row_bg1 = "#FAFAFA"
    row_bg2 = "#F0F4FF"
    
    for idx, step in enumerate(enumerated_steps):
        row_bg = row_bg1 if (idx % 2 == 0) else row_bg2
        
        seq_str = step["index"]
        trans_str = step["transformation"]
        before_val = step["initial_count"]
        after_val = step["new_count"]

        html_parts.append(f"""
          <tr style="
            background-color: {row_bg};
            transition: background-color 0.2s ease-in-out;
          "
            onmouseover="this.style.backgroundColor='#D9EDF9';"
            onmouseout="this.style.backgroundColor='{row_bg}';"
          >
            <td style="padding: 10px; border-bottom: 1px solid #E0E0E0; border-right: 1px solid #E0E0E0;">
              {seq_str}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #E0E0E0; border-right: 1px solid #E0E0E0;">
              {trans_str}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #E0E0E0; text-align: right; border-right: 1px solid #E0E0E0;">
              {before_val}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #E0E0E0; text-align: right;">
              {after_val}
            </td>
          </tr>
        """)

    # Close table and container
    html_parts.append("""
        </tbody>
      </table>
      </div>
    """)
    
    # Close outer div
    html_parts.append("</div>")
    
    return "\n".join(html_parts)

def has_tuple_key(obj):
    """
    Recursively check if the object (dict or list) contains any tuple keys.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, tuple):
                return True
            if has_tuple_key(v):
                return True
        return False
    elif isinstance(obj, list):
        return any(has_tuple_key(item) for item in obj)
    return False

def convert_tuple_keys_to_str(obj):
    """
    Recursively convert dictionary keys that are tuples into strings by joining
    the tuple elements with "::".
    """
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            new_key = "::".join(str(x) for x in k) if isinstance(k, tuple) else k
            new_obj[new_key] = convert_tuple_keys_to_str(v)
        return new_obj
    elif isinstance(obj, list):
        return [convert_tuple_keys_to_str(item) for item in obj]
    else:
        return obj

def save_pipeline_config(config, filepath):
    print("Saving pipeline config to:", config)
    serializable_config = convert_tuple_keys_to_str(config)
    with open(filepath, 'w') as f:
        json.dump(serializable_config, f, indent=4)

def convert_str_keys_to_tuple(obj, sep="::"):
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            if isinstance(k, str) and sep in k:
                new_key = tuple(k.split(sep))
            else:
                new_key = k
            new_obj[new_key] = convert_str_keys_to_tuple(v, sep)
        return new_obj
    elif isinstance(obj, list):
        return [convert_str_keys_to_tuple(item, sep) for item in obj]
    else:
        return obj

def load_pipeline_config(filepath):
    with open(filepath, 'r') as f:
        config = json.load(f)

    if "Transformations" in config and "Group & Aggregate" in config["Transformations"]:
        ga = config["Transformations"]["Group & Aggregate"]
        if "new_names" in ga:
            ga["new_names"] = convert_str_keys_to_tuple(ga["new_names"])
    if "Transformations" in config and "Group & Aggregate" in config["Transformations"]:
        ga = config["Transformations"]["Group & Aggregate"]
        if "having" in ga:
            ga["having"] = convert_str_keys_to_tuple(ga["having"])
    return config
    
def sql_like_to_regex(pattern):
    pattern = pattern.strip("'\"")
    pattern = pattern.replace('%', '.*').replace('_', '.')
    return pattern

def parse_date(s):
    return pd.to_datetime(s, errors='coerce')

def parse_date_range(val):
    parts = [v.strip() for v in str(val).split(',') if v.strip()]
    if len(parts) != 2:
        logger.warning("Date range input '%s' does not have exactly two parts.", val)
        return None, None
    d1 = parse_date(parts[0])
    d2 = parse_date(parts[1])
    if pd.isna(d1) or pd.isna(d2):
        logger.warning("Could not parse one or both dates in '%s'.", val)
    return d1, d2

def parse_between_range(val):
    parts = [v.strip() for v in str(val).split(',') if v.strip()]
    if len(parts) != 2:
        logger.warning("Between range input '%s' does not have exactly two parts.", val)
        return None, None
    try:
        lower = float(parts[0]) if '.' in parts[0] else int(parts[0])
        upper = float(parts[1]) if '.' in parts[1] else int(parts[1])
        return lower, upper
    except Exception as e:
        logger.warning("Error parsing between range '%s': %s", val, e)
        return None, None

def parse_in_list(val):
    if isinstance(val, list):
        return val
    parts = [v.strip() for v in str(val).split(',') if v.strip()]
    if not parts:
        logger.warning("In List input '%s' produced an empty list.", val)
    return parts

def parse_conditions(condition_str):
    pattern = r"\(([\w\d_]+)\s+(Not Null|Null|Equals|Not Equals|Like|Not Like|Contains|Greater Than|Less Than|Between)\s*([^\)]*)\)"
    matches = re.findall(pattern, condition_str)
    conditions = []
    for match in matches:
        col, cond, val = match
        val = None if val.strip() == "" else val.strip()
        conditions.append((col, cond, val))
    logical_ops = re.findall(r"\b(AND|OR)\b", condition_str)
    if len(logical_ops) > 0 and len(logical_ops) == len(conditions) - 1:
        combined = []
        for i, condition in enumerate(conditions):
            combined.append(condition)
            if i < len(logical_ops):
                combined.append(logical_ops[i])
        return combined
    else:
        return conditions

def apply_filters(df, filter_conditions):
    if not filter_conditions:
        #logger.warning("No filters provided. Returning original DataFrame.")
        return df
    group_results = []

    for group in filter_conditions:
        if (not isinstance(group, dict)
            or "conditions" not in group
            or "group_logic" not in group):
            logger.warning("Skipping invalid filter group: %s", group)
            continue

        group_logic = group.get("group_logic", "AND").upper()
        conditions = group.get("conditions", [])

        filtered_df = df.copy()
        condition_mask = None
        current_logic = None

        for condition in conditions:
            if isinstance(condition, str) and condition.upper() in ["AND", "OR"]:
                current_logic = condition.upper()
                continue

            if isinstance(condition, dict):
                col = condition.get("col")
                cond = condition.get("cond")
                val = condition.get("value")
                row_logic = condition.get("row_logic", "").upper()
                if row_logic in ["AND", "OR"]:
                    current_logic = row_logic
            elif isinstance(condition, tuple) and len(condition) == 3:
                col, cond, val = condition
            else:
                logger.warning("Skipping invalid condition: %s", condition)
                continue

            if col not in filtered_df.columns:
                logger.warning("Filter skipped: column '%s' not found in DataFrame.", col)
                continue

            condition_result = None

            if cond == "Equals" and val is not None:
                condition_result = (filtered_df[col] == val)
            elif cond == "Not Equals" and val is not None:
                condition_result = (filtered_df[col] != val)
            elif cond == "Contains" and val is not None:
                condition_result = filtered_df[col].astype(str).str.contains(str(val), case=False, na=False)
            elif cond == "Begins With" and val is not None:
                condition_result = filtered_df[col].astype(str).str.startswith(val, na=False)
            elif cond == "Ends With" and val is not None:
                condition_result = filtered_df[col].astype(str).str.endswith(val, na=False)
            elif cond == "Like" and val is not None:
                regex_pattern = sql_like_to_regex(val)
                condition_result = filtered_df[col].astype(str).str.contains(regex_pattern, case=False, na=False, regex=True)
            elif cond == "Not Like" and val is not None:
                regex_pattern = sql_like_to_regex(val)
                condition_result = ~filtered_df[col].astype(str).str.contains(regex_pattern, case=False, na=False, regex=True)
            elif cond == "ILIKE" and val is not None:
                regex_pattern = sql_like_to_regex(val.lower())
                condition_result = filtered_df[col].astype(str).str.lower().str.contains(regex_pattern, na=False, regex=True)
            elif cond == "Regex" and val is not None:
                try:
                    pattern = re.compile(val)
                    condition_result = filtered_df[col].astype(str).apply(lambda x: bool(pattern.search(x)))
                except re.error:
                    logger.warning("Invalid regex pattern: %s", val)
                    condition_result = pd.Series([False]*len(filtered_df), index=filtered_df.index)
            elif cond == "Greater Than" and val is not None:
                numeric_series = pd.to_numeric(filtered_df[col], errors='coerce')
                try:
                    cmpval = float(val) if '.' in str(val) else int(val)
                    condition_result = numeric_series > cmpval
                except Exception as e:
                    logger.warning("Error in 'Greater Than' for column '%s': %s", col, e)
                    condition_result = pd.Series([False]*len(filtered_df), index=filtered_df.index)
            elif cond == "Less Than" and val is not None:
                numeric_series = pd.to_numeric(filtered_df[col], errors='coerce')
                try:
                    cmpval = float(val) if '.' in str(val) else int(val)
                    condition_result = numeric_series < cmpval
                except Exception as e:
                    logger.warning("Error in 'Less Than' for column '%s': %s", col, e)
                    condition_result = pd.Series([False]*len(filtered_df), index=filtered_df.index)
            elif cond == "Between" and val is not None:
                lower, upper = parse_between_range(val)
                if lower is not None and upper is not None:
                    numeric_series = pd.to_numeric(filtered_df[col], errors='coerce')
                    condition_result = (numeric_series >= lower) & (numeric_series <= upper)
                else:
                    logger.warning("Invalid input for 'Between' on column '%s': %s", col, val)
            elif cond == "In List" and val is not None:
                items = parse_in_list(val)
                if pd.api.types.is_numeric_dtype(filtered_df[col]):
                    try:
                        items = [float(x) if '.' in str(x) else int(x) for x in items]
                    except Exception as e:
                        logger.warning("Could not convert items to numeric for column '%s': %s", col, e)
                condition_result = filtered_df[col].isin(items)
            elif cond == "Not In List" and val is not None:
                items = parse_in_list(val)
                if pd.api.types.is_numeric_dtype(filtered_df[col]):
                    try:
                        items = [float(x) if '.' in str(x) else int(x) for x in items]
                    except Exception as e:
                        logger.warning("Could not convert items to numeric for column '%s': %s", col, e)
                condition_result = ~filtered_df[col].isin(items)
            elif cond == "Date Before" and val is not None:
                dt_series = pd.to_datetime(filtered_df[col], errors='coerce')
                cmp_date = parse_date(val)
                if pd.notnull(cmp_date):
                    condition_result = dt_series < cmp_date
                else:
                    logger.warning("Invalid date for 'Date Before' on column '%s': %s", col, val)
            elif cond == "Date After" and val is not None:
                dt_series = pd.to_datetime(filtered_df[col], errors='coerce')
                cmp_date = parse_date(val)
                if pd.notnull(cmp_date):
                    condition_result = dt_series > cmp_date
                else:
                    logger.warning("Invalid date for 'Date After' on column '%s': %s", col, val)
            elif cond == "Date Between" and val is not None:
                dt_series = pd.to_datetime(filtered_df[col], errors='coerce')
                d1, d2 = parse_date_range(val)
                if pd.notnull(d1) and pd.notnull(d2):
                    condition_result = (dt_series >= d1) & (dt_series <= d2)
                else:
                    logger.warning("Invalid date range for 'Date Between' on column '%s': %s", col, val)
            elif cond == "Not Null":
                condition_result = filtered_df[col].notnull()
            elif cond == "Null":
                condition_result = filtered_df[col].isnull()
            else:
                logger.warning("Unknown condition '%s' for column '%s'. Skipped.", cond, col)
                continue

            if condition_result is not None:
                if condition_mask is None:
                    condition_mask = condition_result
                else:
                    if not current_logic:
                        current_logic = "AND"
                    if current_logic == "AND":
                        condition_mask &= condition_result
                    elif current_logic == "OR":
                        condition_mask |= condition_result

        if condition_mask is not None:
            filtered_df = filtered_df[condition_mask]

        group_results.append((filtered_df, group_logic.upper()))

    if not group_results:
        return df

    final_df = group_results[0][0]
    for i in range(1, len(group_results)):
        grp_df, grp_logic = group_results[i]
        if grp_logic == "AND":
            final_df = pd.merge(final_df, grp_df, how="inner")
        elif grp_logic == "OR":
            final_df = pd.concat([final_df, grp_df]).drop_duplicates()

    return final_df

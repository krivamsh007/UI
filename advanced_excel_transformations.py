import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, Any

# Try to import pandasql for SQL-like queries
try:
    from pandasql import sqldf
except ImportError:
    sqldf = None

# -------------------- Helper Functions --------------------
def _validate_column(df: pd.DataFrame, column: str, operation: str) -> bool:
    """Validate if a column exists in the DataFrame."""
    if column not in df.columns:
        print(f"Error in {operation}: Column '{column}' not found in DataFrame.")
        return False
    return True

# -------------------- Lookup & Conditional Transformations --------------------
def apply_lookup_and_conditional_transform(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    # Lookup Function
    if "lookup_table" in config and config["lookup_table"] != "to_be_loaded":
        lookup_info = config["lookup_table"]
        try:
            lookup_df = pd.DataFrame(lookup_info.get("data"))
            lookup_key = lookup_info.get("key")
            lookup_value = lookup_info.get("value")
            lookup_col = config.get("lookup_column")
            new_col = f"{lookup_col}_lookup"
            if _validate_column(df, lookup_col, "lookup") and lookup_key in lookup_df.columns:
                df = df.merge(lookup_df[[lookup_key, lookup_value]], left_on=lookup_col, right_on=lookup_key, how='left')
                df.rename(columns={lookup_value: new_col}, inplace=True)
        except Exception as e:
            print(f"Error in lookup function: {e}")
    # Conditional Column
    if "conditional" in config:
        for cond in config["conditional"]:
            src = cond.get("source_column")
            op = cond.get("operator")
            val = cond.get("value")
            true_val = cond.get("true_result")
            false_val = cond.get("false_result")
            output_col = cond.get("output_column", f"{src}_conditional")
            if _validate_column(df, src, "conditional"):
                if op == ">":
                    df[output_col] = np.where(df[src] > val, true_val, false_val)
                elif op == "<":
                    df[output_col] = np.where(df[src] < val, true_val, false_val)
                elif op == "==":
                    df[output_col] = np.where(df[src] == val, true_val, false_val)
    # Custom Formula Engine
    if "custom_formula" in config:
        formula = config["custom_formula"].get("formula")
        output_col = config["custom_formula"].get("output_column", "custom_formula_result")
        try:
            df[output_col] = df.eval(formula)
        except Exception as e:
            print(f"Error evaluating custom formula: {e}")
    return df

# -------------------- Advanced Date and Time Functions --------------------
def apply_advanced_date_transform(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    # Date Difference
    if "date_difference" in config:
        dd_conf = config["date_difference"]
        date_col = dd_conf.get("date_column")
        ref_date = dd_conf.get("reference_date")
        unit = dd_conf.get("unit", "days")
        new_col = f"{date_col}_diff"
        if _validate_column(df, date_col, "date_difference"):
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                ref_date = pd.to_datetime(ref_date)
                if unit == "days":
                    df[new_col] = (df[date_col] - ref_date).dt.days
                elif unit == "months":
                    df[new_col] = df[date_col].apply(lambda d: relativedelta(d, ref_date).years * 12 + relativedelta(d, ref_date).months)
                elif unit == "years":
                    df[new_col] = df[date_col].apply(lambda d: relativedelta(d, ref_date).years)
            except Exception as e:
                print(f"Error in date_difference: {e}")
    # EOMONTH
    if "EOMONTH" in config:
        eom_conf = config["EOMONTH"]
        date_col = eom_conf.get("date_column")
        add_months = eom_conf.get("months", 0)
        new_col = f"{date_col}_EOMONTH"
        if _validate_column(df, date_col, "EOMONTH"):
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                df[new_col] = df[date_col].apply(lambda d: (d + relativedelta(months=add_months)).replace(day=1) + relativedelta(months=1, days=-1))
            except Exception as e:
                print(f"Error in EOMONTH: {e}")
    # WEEKDAY
    if "WEEKDAY" in config:
        wd_conf = config["WEEKDAY"]
        date_col = wd_conf.get("date_column")
        new_col = wd_conf.get("output_column", f"{date_col}_weekday")
        if _validate_column(df, date_col, "WEEKDAY"):
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                df[new_col] = df[date_col].dt.weekday  # Monday=0
            except Exception as e:
                print(f"Error in WEEKDAY: {e}")
    # NETWORKDAYS
    if "NETWORKDAYS" in config:
        nd_conf = config["NETWORKDAYS"]
        start_col = nd_conf.get("start_date_column")
        end_col = nd_conf.get("end_date_column")
        holidays = nd_conf.get("holidays", [])
        new_col = nd_conf.get("output_column", f"{start_col}_{end_col}_networkdays")
        if _validate_column(df, start_col, "NETWORKDAYS") and _validate_column(df, end_col, "NETWORKDAYS"):
            try:
                df[start_col] = pd.to_datetime(df[start_col])
                df[end_col] = pd.to_datetime(df[end_col])
                def networkdays(start, end, holidays):
                    if pd.isnull(start) or pd.isnull(end):
                        return None
                    return np.busday_count(np.datetime64(start.date()), np.datetime64((end + pd.Timedelta(days=1)).date()), holidays=holidays)
                df[new_col] = df.apply(lambda row: networkdays(row[start_col], row[end_col], holidays), axis=1)
            except Exception as e:
                print(f"Error in NETWORKDAYS: {e}")
    return df

# -------------------- Enhanced Text Operations --------------------
def apply_enhanced_text_transform(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    # Replace/Substitute Text
    if "text_replace" in config:
        txt_conf = config["text_replace"]
        col = txt_conf.get("column")
        search_text = txt_conf.get("search_text")
        replacement_text = txt_conf.get("replacement_text")
        if _validate_column(df, col, "text_replace"):
            df[col] = df[col].astype(str).str.replace(search_text, replacement_text, regex=True)
    # Advanced Concatenation / TEXTJOIN
    if "text_join" in config:
        tj_conf = config["text_join"]
        cols = tj_conf.get("columns", [])
        delimiter = tj_conf.get("delimiter", " ")
        output_col = tj_conf.get("output_column", "text_join_result")
        if all(_validate_column(df, c, "text_join") for c in cols):
            ignore_blanks = tj_conf.get("ignore_blanks", False)
            if ignore_blanks:
                df[output_col] = df[cols].apply(lambda x: delimiter.join([str(i).strip() for i in x if pd.notnull(i) and str(i).strip() != ""]), axis=1)
            else:
                df[output_col] = df[cols].astype(str).agg(delimiter.join, axis=1)
    # Case Conversion & Advanced Text Formatting
    if "text_formatting" in config:
        tf_conf = config["text_formatting"]
        col = tf_conf.get("column")
        conversion = tf_conf.get("conversion", "proper")  # Options: upper, lower, proper
        output_col = tf_conf.get("output_column", f"{col}_{conversion}")
        if _validate_column(df, col, "text_formatting"):
            if conversion.lower() == "upper":
                df[output_col] = df[col].astype(str).str.upper()
            elif conversion.lower() == "lower":
                df[output_col] = df[col].astype(str).str.lower()
            elif conversion.lower() == "proper":
                df[output_col] = df[col].astype(str).str.title()
            if tf_conf.get("remove_nonprintable", False):
                df[output_col] = df[output_col].apply(lambda x: ''.join(filter(lambda c: c.isprintable(), x)))
    return df

# -------------------- Mathematical & Statistical Functions --------------------
def apply_math_stat_transform(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    # Cumulative Sum (Running Total)
    if "cumulative_sum" in config:
        cs_conf = config["cumulative_sum"]
        col = cs_conf.get("column")
        output_col = cs_conf.get("output_column", f"{col}_cum_sum")
        if _validate_column(df, col, "cumulative_sum"):
            df[output_col] = df[col].cumsum()
    # Moving Average
    if "moving_average" in config:
        ma_conf = config["moving_average"]
        col = ma_conf.get("column")
        window = ma_conf.get("window", 3)
        output_col = ma_conf.get("output_column", f"{col}_moving_avg")
        if _validate_column(df, col, "moving_average"):
            df[output_col] = df[col].rolling(window=window, min_periods=1).mean()
    # Advanced Aggregation: Median, Standard Deviation, Percentile
    if "advanced_aggregation" in config:
        agg_conf = config["advanced_aggregation"]
        col = agg_conf.get("column")
        if _validate_column(df, col, "advanced_aggregation"):
            df[f"{col}_median"] = df[col].median()
            df[f"{col}_std"] = df[col].std()
            percentile = agg_conf.get("percentile", 50)
            df[f"{col}_percentile_{percentile}"] = df[col].quantile(percentile/100.0)
    # Correlation between two columns
    if "correlation" in config:
        corr_conf = config["correlation"]
        col1 = corr_conf.get("column1")
        col2 = corr_conf.get("column2")
        output_col = corr_conf.get("output_column", f"{col1}_{col2}_correlation")
        if _validate_column(df, col1, "correlation") and _validate_column(df, col2, "correlation"):
            corr_value = df[col1].corr(df[col2])
            df[output_col] = corr_value
    return df

# -------------------- Data Validation and Error Checking --------------------
def apply_data_validation(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    if "data_quality" in config:
        dq_conf = config["data_quality"]
        col = dq_conf.get("column")
        rule = dq_conf.get("rule")
        output_col = dq_conf.get("output_column", f"{col}_is_valid")
        if _validate_column(df, col, "data_quality"):
            if rule.upper() == "ISNUMBER":
                df[output_col] = pd.to_numeric(df[col], errors='coerce').notnull()
            elif rule.upper() == "ISBLANK":
                df[output_col] = df[col].isnull()
    return df

# -------------------- SQL-like Querying and Data Slicing --------------------
def apply_sql_query(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    if "sql_query" in config and config["sql_query"].get("query"):
        query = config["sql_query"].get("query")
        if sqldf is not None:
            try:
                df = sqldf(query, locals())
            except Exception as e:
                print(f"Error executing SQL query: {e}")
        else:
            print("pandasql is not installed. SQL query not executed.")
    return df

# -------------------- Financial & Specialized Calculations --------------------
def calculate_npv(rate, cashflows):
    npv = 0
    for t, cf in enumerate(cashflows, start=1):
        npv += cf / ((1 + rate) ** t)
    return npv

def apply_financial_calculations(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    if "financial_calculations" in config:
        fc_conf = config["financial_calculations"]
        func = fc_conf.get("function", "").upper()
        if func == "NPV":
            discount_rate = fc_conf.get("discount_rate", 0.1)
            cashflow_col = fc_conf.get("cashflow_column")
            output_col = fc_conf.get("output_column", "NPV")
            if _validate_column(df, cashflow_col, "NPV"):
                df[output_col] = df[cashflow_col].apply(lambda x: calculate_npv(discount_rate, x) if isinstance(x, (list, tuple)) else None)
        elif func == "IRR":
            cashflow_col = fc_conf.get("cashflow_column")
            output_col = fc_conf.get("output_column", "IRR")
            if _validate_column(df, cashflow_col, "IRR"):
                try:
                    df[output_col] = df[cashflow_col].apply(lambda x: np.irr(x) if isinstance(x, (list, tuple)) else None)
                except Exception:
                    df[output_col] = None
    return df

# -------------------- Enhanced Data Merging and Appending --------------------
def apply_enhanced_data_merge(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    if "advanced_merge_append" in config:
        ama_conf = config["advanced_merge_append"]
        if ama_conf.get("fuzzy_matching", False):
            print("Fuzzy matching merge is enabled, but not implemented. Returning df unchanged.")
    return df

# -------------------- Main Function --------------------
def apply_advanced_excel_transformations(df: pd.DataFrame, adv_config: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    if not adv_config:
        return df

    # Apply transformations in sequence
    df = apply_lookup_and_conditional_transform(df, adv_config)
    df = apply_advanced_date_transform(df, adv_config)
    df = apply_enhanced_text_transform(df, adv_config)
    df = apply_math_stat_transform(df, adv_config)
    df = apply_data_validation(df, adv_config)
    df = apply_sql_query(df, adv_config)
    df = apply_financial_calculations(df, adv_config)
    df = apply_enhanced_data_merge(df, adv_config)

    return df

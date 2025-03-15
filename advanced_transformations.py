import pandas as pd

def merge_join_dataframes(dfs, join_type, base_key, other_keys):
    """
    Merges two dataframes using the specified join type.
    - dfs: a list containing two dataframes (the first is the base file).
    - join_type: one of "inner", "left", "right", "outer"
    - base_key: the column name in the first (base) dataframe to join on.
    - other_keys: a list with one element: the column name in the second dataframe.
    Returns the merged DataFrame.
    """
    if len(dfs) != 2:
        raise ValueError("Merge Join requires exactly two dataframes.")

    base_df = dfs[0]
    join_df = dfs[1]

    return pd.merge(base_df, join_df, how=join_type, left_on=base_key, right_on=other_keys[0])

def union_dataframes(dfs, union_all=False):
    """
    Unions multiple dataframes.
    - If union_all is True, returns all rows (with duplicates).
    - Else, returns union distinct (dropping duplicates).

    Validation: All dataframes must have the same number of columns.
    """
    base_df = dfs[0]
    # All dataframes are assumed to be pandas DataFrames.
    dfs_converted = dfs
    base_len = len(dfs_converted[0].columns)
    mismatch_info = []
    for i, df in enumerate(dfs_converted, start=1):
        if len(df.columns) != base_len:
            mismatch_info.append(f"DataFrame {i} has {len(df.columns)} columns, expected {base_len}.")
    if mismatch_info:
        error_message = "Union transformation requires all dataframes to have the same number of columns.\n" + "\n".join(mismatch_info)
        raise ValueError(error_message)

    concatenated = pd.concat(dfs_converted, ignore_index=True)
    if union_all:
        return concatenated
    else:
        return concatenated.drop_duplicates().reset_index(drop=True)

Below is the full content you can copy and paste into your **HELP.md** file:

---

```markdown
# Transformation Functions Help

This document provides detailed help for each Excel-like transformation function available in the Data Transformer Tool. Functions are grouped into eight main categories:

1. **Array & Dynamic Functions**
2. **Financial Functions**
3. **Date & Time Functions**
4. **Statistical Functions**
5. **Mathematical Functions**
6. **Text Functions**
7. **Logical Functions**
8. **Lookup & Reference Functions**

Click the help button next to any function’s configuration dialog in the UI to view the corresponding section from this file.

---

## 1. Array & Dynamic Functions

### Unique
**Description:**  
Extracts all distinct values from a given column and writes the resulting list (array) into a new column. Every row in the new column will display the same list.

**Parameters:**  
- **column:** The name of the column from which to extract unique values.  
- **new_column (optional):** The name for the output column (defaults to `<column>_unique`).

**Usage Example:**  
```json
{"column": "Region", "new_column": "Unique_Regions"}
```

**Explanation:**  
This configuration tells the tool: “Look at the 'Region' column, remove any duplicates, and then save the list of unique regions in a new column called 'Unique_Regions' for every row.”

---

### Sort Array
**Description:**  
Sorts the unique values obtained from a column in either ascending or descending order and outputs them as a list in a new column.

**Parameters:**  
- **column:** The source column for extracting unique values.  
- **ascending:** A string ("True" or "False") indicating whether to sort in ascending order.  
- **new_column (optional):** Name for the output column (defaults to `<column>_sorted`).

**Usage Example:**  
```json
{"column": "Region", "ascending": "True", "new_column": "Sorted_Regions"}
```

**Explanation:**  
This instructs the tool: “Extract the unique values from 'Region', sort them alphabetically, and write the sorted list to 'Sorted_Regions'.”

---

## 2. Financial Functions

### NPV (Net Present Value)
**Description:**  
Calculates the net present value of a series of cash flows using a specified discount rate.

**Parameters:**  
- **discount_rate:** The discount rate (e.g., 0.1 for 10%).  
- **cashflow_column:** The name of the column containing cash flow lists (each row should be a list or tuple).  
- **new_column (optional):** Name for the output column (defaults to "NPV").

**Usage Example:**  
```json
{"discount_rate": 0.1, "cashflow_column": "CashFlows", "new_column": "Project_NPV"}
```

**Explanation:**  
For every row, the tool calculates the net present value of the cash flows in 'CashFlows' using a 10% discount rate, then saves the result in 'Project_NPV'.

---

### IRR (Internal Rate of Return)
**Description:**  
Calculates the internal rate of return for cash flow lists in a given column.

**Parameters:**  
- **cashflow_column:** The column with cash flow lists.  
- **new_column (optional):** The output column name (defaults to "IRR").

**Usage Example:**  
```json
{"cashflow_column": "CashFlows", "new_column": "Project_IRR"}
```

**Explanation:**  
This configuration directs the tool to compute the IRR for each cash flow list in 'CashFlows' and save it in 'Project_IRR'.

---

### PMT (Payment Calculation)
**Description:**  
Computes the periodic payment for a loan or investment based on a given interest rate, number of periods, and present value.

**Parameters:**  
- **rate:** The interest rate per period.  
- **nper:** Total number of periods.  
- **pv:** The present value (loan amount or investment).  
- **new_column (optional):** Name for the output column (defaults to "PMT").

**Usage Example:**  
```json
{"rate": 0.05, "nper": 12, "pv": 10000, "new_column": "Monthly_Payment"}
```

**Explanation:**  
This tells the tool: “Calculate the monthly payment for a loan of 10,000 with a 5% interest rate over 12 periods, and store the result in 'Monthly_Payment'.”

---

## 3. Date & Time Functions

### DATEDIF
**Description:**  
Computes the difference between two date columns in days, months, or years.

**Parameters:**  
- **start_date_column:** Column name containing start dates.  
- **end_date_column:** Column name containing end dates.  
- **unit:** The unit for the difference ("days", "months", or "years").  
- **new_column (optional):** Name for the output column.

**Usage Example:**  
```json
{"start_date_column": "Start_Date", "end_date_column": "End_Date", "unit": "days", "new_column": "Duration_Days"}
```

**Explanation:**  
Subtracts the start date from the end date (in days) and saves the result in 'Duration_Days'.

---

### EOMONTH
**Description:**  
Determines the last day of the month for a specified date, optionally offset by a given number of months.

**Parameters:**  
- **date_column:** The column with date values.  
- **months:** Number of months to offset (use 0 for the current month).  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{"date_column": "Order_Date", "months": 0, "new_column": "End_Of_Month"}
```

**Explanation:**  
Calculates the end-of-month date for each entry in 'Order_Date' and stores it in 'End_Of_Month'.

---

### WEEKDAY
**Description:**  
Extracts the weekday name (e.g., Monday, Tuesday) from a date column.

**Parameters:**  
- **date_column:** The column that contains dates.  
- **new_column (optional):** Name for the output column (defaults to `<date_column>_weekday`).

**Usage Example:**  
```json
{"date_column": "Order_Date", "new_column": "Weekday_Name"}
```

**Explanation:**  
Converts each date in 'Order_Date' to its corresponding weekday name and outputs it in 'Weekday_Name'.

---

## 4. Statistical Functions

### Median
**Description:**  
Calculates the median (middle value) of a numeric column.

**Parameters:**  
- **column:** The column to compute the median from.  
- **new_column (optional):** Output column name (defaults to `<column>_median`).

**Usage Example:**  
```json
{"column": "Sales", "new_column": "Sales_Median"}
```

**Explanation:**  
Determines the median value of the 'Sales' column and writes the result to 'Sales_Median'.

---

### Std
**Description:**  
Computes the standard deviation of values in a column.

**Parameters:**  
- **column:** The column to analyze.  
- **new_column (optional):** Output column name (defaults to `<column>_std`).

**Usage Example:**  
```json
{"column": "Sales", "new_column": "Sales_StdDev"}
```

**Explanation:**  
Calculates the standard deviation for the 'Sales' column and outputs the result in 'Sales_StdDev'.

---

### Percentile
**Description:**  
Calculates a specified percentile (for example, the 75th percentile) for a column.

**Parameters:**  
- **column:** The column to analyze.  
- **percentile:** The desired percentile (e.g., 75).  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{"column": "Sales", "percentile": 75, "new_column": "Sales_75thPercentile"}
```

**Explanation:**  
Computes the 75th percentile of 'Sales' and stores it in 'Sales_75thPercentile'.

---

### Mode
**Description:**  
Identifies the most frequently occurring value in a column.

**Parameters:**  
- **column:** The column to analyze.  
- **new_column (optional):** Output column name (defaults to `<column>_mode`).

**Usage Example:**  
```json
{"column": "Category", "new_column": "Category_Mode"}
```

**Explanation:**  
Determines the mode (most common value) of 'Category' and writes it to 'Category_Mode'.

---

## 5. Mathematical Functions

### Abs
**Description:**  
Converts every value in a numeric column to its absolute value.

**Parameters:**  
- **column:** The source numeric column.  
- **new_column (optional):** Output column name (defaults to `<column>_abs`).

**Usage Example:**  
```json
{"column": "Profit", "new_column": "Profit_Abs"}
```

**Explanation:**  
Calculates the absolute value of each number in 'Profit' and outputs it in 'Profit_Abs'.

---

### Power
**Description:**  
Raises each value in a column to a specified exponent.

**Parameters:**  
- **column:** The numeric column to process.  
- **exponent:** The power to raise each value.  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{"column": "Value", "exponent": 2, "new_column": "Value_Squared"}
```

**Explanation:**  
Squares each value in 'Value' and saves the result in 'Value_Squared'.

---

### Sqrt
**Description:**  
Calculates the square root of each number in a column (returns None for negative values).

**Parameters:**  
- **column:** The numeric column.  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{"column": "Area", "new_column": "Area_Sqrt"}
```

**Explanation:**  
Computes the square root of each number in 'Area' and writes the result in 'Area_Sqrt'.

---

## 6. Text Functions

### LEFT
**Description:**  
Extracts a specified number of characters from the beginning (left side) of each cell in a text column.

**Parameters:**  
- **column:** The source text column.  
- **num_chars:** Number of characters to extract from the left.  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{"column": "Name", "num_chars": 3, "new_column": "Name_Left"}
```

**Explanation:**  
Takes the first 3 characters from each entry in 'Name' and writes them to 'Name_Left'.

---

### RIGHT
**Description:**  
Extracts a specified number of characters from the end (right side) of each cell in a text column.

**Parameters:**  
- **column:** The source text column.  
- **num_chars:** Number of characters to extract from the right.  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{"column": "Code", "num_chars": 2, "new_column": "Code_Right"}
```

**Explanation:**  
Extracts the last 2 characters of each value in 'Code' and outputs them in 'Code_Right'.

---

### MID
**Description:**  
Extracts a substring from within a text string, starting at a specified index and for a specified length.

**Parameters:**  
- **column:** The source text column.  
- **start:** The starting index (0-based).  
- **num_chars:** The number of characters to extract.  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{"column": "Name", "start": 2, "num_chars": 4, "new_column": "Name_Mid"}
```

**Explanation:**  
For each entry in 'Name', extracts 4 characters starting from index 2 and stores the result in 'Name_Mid'.

---

### LEN
**Description:**  
Determines the length (number of characters) of each text string in a column.

**Parameters:**  
- **column:** The text column.  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{"column": "Description", "new_column": "Description_Length"}
```

**Explanation:**  
Counts the number of characters in each entry of 'Description' and writes the count to 'Description_Length'.

---

### TEXTJOIN
**Description:**  
Concatenates text from multiple columns using a specified delimiter.

**Parameters:**  
- **columns:** A comma-separated list of column names to join.  
- **delimiter:** The string used to separate values.  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{"columns": "First_Name,Last_Name", "delimiter": " ", "new_column": "Full_Name"}
```

**Explanation:**  
Combines the text from 'First_Name' and 'Last_Name' with a space between them, and writes the result to 'Full_Name'.

---

## 7. Logical Functions

### IF
**Description:**  
Evaluates a condition and returns one value if true and another if false.  
*Note:* The condition is a string that is evaluated in the context of the DataFrame using Python's `eval`.

**Parameters:**  
- **column (optional):** A reference column for the condition.  
- **condition:** A string expression (e.g., `"df['Sales'] > 100"`).  
- **true_value:** The value returned if the condition is true.  
- **false_value:** The value returned if the condition is false.  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{"column": "Sales", "condition": "df['Sales'] > 100", "true_value": "High", "false_value": "Low", "new_column": "Sales_Category"}
```

**Explanation:**  
For each row, if the value in 'Sales' exceeds 100, 'Sales_Category' is set to "High"; otherwise, it is set to "Low".

---

### IFERROR
**Description:**  
Replaces any error or missing value (NaN) in a column with a specified fallback value.

**Parameters:**  
- **column:** The source column.  
- **fallback:** The value to use if an error or NaN is encountered.  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{"column": "Result", "fallback": "Error", "new_column": "Result_Fixed"}
```

**Explanation:**  
Checks the 'Result' column and replaces any errors or blanks with "Error", then writes the corrected values to 'Result_Fixed'.

---

## 8. Lookup & Reference Functions

### XLOOKUP
**Description:**  
Searches for a value in a source column and returns a corresponding value from a lookup table provided in JSON format.

**Parameters:**  
- **source_column:** The column in the main dataset to search.  
- **lookup_table:** A JSON string representing a lookup table (a list of dictionaries).  
- **lookup_key:** The key column in the lookup table for matching.  
- **lookup_value:** The column in the lookup table from which to return a value.  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{
  "source_column": "Product_ID",
  "lookup_table": "[{\"Product_ID\": 1, \"Price\": 9.99}, {\"Product_ID\": 2, \"Price\": 19.99}]",
  "lookup_key": "Product_ID",
  "lookup_value": "Price",
  "new_column": "Product_Price"
}
```

**Explanation:**  
For every row, the tool takes the 'Product_ID', searches the provided lookup table for a matching record, retrieves the 'Price', and writes it to 'Product_Price'.

---

### INDEX/MATCH
**Description:**  
Combines the INDEX and MATCH functions to look up a value in a lookup table.  
It uses the value in the source column to find a matching record in the lookup table and then retrieves the value from another specified column.

**Parameters:**  
- **source_column:** The column in the main dataset containing the lookup value.  
- **lookup_table:** A JSON string representing the lookup table.  
- **lookup_key:** The column in the lookup table to match the source value.  
- **return_column:** The column from which to return the value.  
- **new_column (optional):** Output column name.

**Usage Example:**  
```json
{
  "source_column": "Employee_ID",
  "lookup_table": "[{\"Employee_ID\": \"E001\", \"Name\": \"John Doe\"}, {\"Employee_ID\": \"E002\", \"Name\": \"Jane Smith\"}]",
  "lookup_key": "Employee_ID",
  "return_column": "Name",
  "new_column": "Employee_Name"
}
```

**Explanation:**  
This configuration instructs the tool: “For each 'Employee_ID' in the main dataset, find the matching record in the lookup table and return the corresponding 'Name', storing it in 'Employee_Name'.”
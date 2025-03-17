from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QCheckBox,
    QAbstractItemView, QMessageBox, QLayout
)
from PyQt6.QtCore import Qt
from ui_helpers import add_ok_cancel_buttons, create_combo_box, single_friendly_to_internal, internal_to_friendly
from ui_dialogs_data_cleaning import SearchableColumnListDialog

# --------------------  Pivot Data Dialog --------------------
class PivotDataDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_values=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(" Pivot Data 📊")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_values = init_values
        self.initUI()
        if self.init_values:
            self.loadConfig(self.init_values)
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        
        # Index Columns
        index_layout = QHBoxLayout()
        self.index_edit = QLineEdit()
        self.index_edit.setPlaceholderText("Comma separated or click 'Select Columns'")
        select_index_btn = QPushButton("Select Columns")
        select_index_btn.clicked.connect(self.selectIndexColumns)
        index_layout.addWidget(self.index_edit)
        index_layout.addWidget(select_index_btn)
        layout.addWidget(QLabel("Index Columns:"))
        layout.addLayout(index_layout)
        
        # Pivot Columns
        pivot_layout = QHBoxLayout()
        self.pivot_edit = QLineEdit()
        self.pivot_edit.setPlaceholderText("Comma separated or click 'Select Columns'")
        select_pivot_btn = QPushButton("Select Columns")
        select_pivot_btn.clicked.connect(self.selectPivotColumns)
        pivot_layout.addWidget(self.pivot_edit)
        pivot_layout.addWidget(select_pivot_btn)
        layout.addWidget(QLabel("Pivot Columns:"))
        layout.addLayout(pivot_layout)
        
        # Value Columns Table
        layout.addWidget(QLabel("Value Columns & Aggregations:"))
        self.value_table = QTableWidget(0, 5)
        self.value_table.setHorizontalHeaderLabels(
            ["Value Column", "Aggregation", "Delimiter", "Distinct", "Order"]
        )
        self.value_table.horizontalHeader().setStretchLastSection(True)
        self.value_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.value_table)
        
        btn_val_layout = QHBoxLayout()
        add_val_btn = QPushButton("Add Value Column")
        add_val_btn.clicked.connect(self.addValueRow)
        remove_val_btn = QPushButton("Remove Selected Row")
        remove_val_btn.clicked.connect(self.removeValueRow)
        btn_val_layout.addWidget(add_val_btn)
        btn_val_layout.addWidget(remove_val_btn)
        layout.addLayout(btn_val_layout)
        
        # Missing Value Fill
        layout.addWidget(QLabel("Missing Value Fill (optional):"))
        self.missing_fill_edit = QLineEdit()
        self.missing_fill_edit.setPlaceholderText("Enter fill value for missing pivot cells")
        layout.addWidget(self.missing_fill_edit)
        
        # Sort Option
        sort_layout = QHBoxLayout()
        self.sort_checkbox = QCheckBox("Sort Rows by Aggregated Value")
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.addItems(["Ascending", "Descending"])
        sort_layout.addWidget(self.sort_checkbox)
        sort_layout.addWidget(self.sort_order_combo)
        layout.addLayout(sort_layout)
        
        # Computed Metric Formula
        layout.addWidget(QLabel("Computed Metric Formula (optional):"))
        self.metric_edit = QLineEdit()
        self.metric_edit.setPlaceholderText("e.g., (value1 - value2) / value2")
        layout.addWidget(self.metric_edit)
        
        # Help Button
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.showHelp)
        layout.addWidget(help_btn)
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
    
    def loadConfig(self, config):
        if "index" in config:
            friendly = [internal_to_friendly(col, self.registry) for col in config["index"]]
            self.index_edit.setText(", ".join(friendly))
        if "columns" in config:
            friendly = [internal_to_friendly(col, self.registry) for col in config["columns"]]
            self.pivot_edit.setText(", ".join(friendly))
        if "value_settings" in config:
            self.value_table.setRowCount(0)
            for setting in config["value_settings"]:
                self.addValueRow()
                row = self.value_table.rowCount() - 1
                col_combo = self.value_table.cellWidget(row, 0)
                col_combo.setCurrentText(internal_to_friendly(setting.get("value_column", ""), self.registry))
                agg_combo = self.value_table.cellWidget(row, 1)
                agg_combo.setCurrentText(setting.get("aggfunc", "sum"))
                self.updateAggregationOptions(row, setting.get("aggfunc", "sum"))
                if setting.get("aggfunc", "").lower() == "concatenate":
                    delim_edit = self.value_table.cellWidget(row, 2)
                    delim_edit.setText(setting.get("delimiter", ""))
                    distinct_chk = self.value_table.cellWidget(row, 3)
                    distinct_chk.setChecked(setting.get("distinct", False))
                    order_combo = self.value_table.cellWidget(row, 4)
                    order_combo.setCurrentText(setting.get("order", "None"))
        if "missing_fill" in config:
            self.missing_fill_edit.setText(config["missing_fill"])
        if "sort" in config:
            sort_config = config["sort"]
            self.sort_checkbox.setChecked(sort_config.get("enabled", False))
            if "order" in sort_config:
                self.sort_order_combo.setCurrentText(sort_config["order"])
        if "computed_metric" in config:
            self.metric_edit.setText(config["computed_metric"])
    
    def selectIndexColumns(self):
        dlg = SearchableColumnListDialog(self.friendly_columns, title="Select Index Columns", multi_select=True, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected = dlg.getSelectedColumns()
            self.index_edit.setText(", ".join(selected))
    
    def selectPivotColumns(self):
        dlg = SearchableColumnListDialog(self.friendly_columns, title="Select Pivot Columns", multi_select=True, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected = dlg.getSelectedColumns()
            self.pivot_edit.setText(", ".join(selected))
    
    def addValueRow(self):
        row = self.value_table.rowCount()
        self.value_table.insertRow(row)
        
        col_combo = create_combo_box(self.friendly_columns, editable=True)
        self.value_table.setCellWidget(row, 0, col_combo)
        
        agg_combo = QComboBox()
        agg_combo.setEditable(True)
        agg_combo.addItems(["sum", "mean", "count", "min", "max", "concatenate"])
        agg_combo.setCurrentText("sum")
        agg_combo.currentTextChanged.connect(lambda agg, r=row: self.updateAggregationOptions(r, agg))
        self.value_table.setCellWidget(row, 1, agg_combo)
        
        delim_edit = QLineEdit()
        delim_edit.setPlaceholderText("Enter delimiter")
        delim_edit.setEnabled(False)
        self.value_table.setCellWidget(row, 2, delim_edit)
        
        distinct_chk = QCheckBox()
        distinct_chk.setEnabled(False)
        self.value_table.setCellWidget(row, 3, distinct_chk)
        
        order_combo = QComboBox()
        order_combo.addItems(["None", "Ascending", "Descending"])
        order_combo.setEnabled(False)
        self.value_table.setCellWidget(row, 4, order_combo)
    
    def updateAggregationOptions(self, row, agg):
        use_concat = (agg.lower() == "concatenate")
        delim_edit = self.value_table.cellWidget(row, 2)
        distinct_chk = self.value_table.cellWidget(row, 3)
        order_combo = self.value_table.cellWidget(row, 4)
        delim_edit.setEnabled(use_concat)
        distinct_chk.setEnabled(use_concat)
        order_combo.setEnabled(use_concat)
    
    def removeValueRow(self):
        rows = set([index.row() for index in self.value_table.selectedIndexes()])
        for row in sorted(rows, reverse=True):
            self.value_table.removeRow(row)
    
    def showHelp(self):
        help_text = (
            " Pivot Data Instructions:\n\n"
            "1. Specify the index columns (rows labels) and pivot columns (columns to pivot) either by typing comma-separated names or by clicking 'Select Columns'.\n"
            "2. In the Value Columns table, click 'Add Value Column' to add a new row. For each row:\n"
            "   - Choose the value column from the dropdown.\n"
            "   - Select the aggregation function. If 'concatenate' is selected, you can enter a custom delimiter, choose to aggregate distinct values only, and set an ordering.\n"
            "3. Optionally, enter a fill value for missing cells, select sorting options, or define a computed metric formula.\n"
            "4. Click OK to apply the pivot transformation."
        )
        QMessageBox.information(self, "Pivot Data Help", help_text)
    
    def getValues(self):
        values = {}
        index_cols = [single_friendly_to_internal(x.strip(), self.registry) for x in self.index_edit.text().split(",") if x.strip()]
        pivot_cols = [single_friendly_to_internal(x.strip(), self.registry) for x in self.pivot_edit.text().split(",") if x.strip()]
        values["index"] = index_cols
        values["columns"] = pivot_cols
        
        value_settings = []
        for row in range(self.value_table.rowCount()):
            col_widget = self.value_table.cellWidget(row, 0)
            agg_widget = self.value_table.cellWidget(row, 1)
            delim_widget = self.value_table.cellWidget(row, 2)
            distinct_widget = self.value_table.cellWidget(row, 3)
            order_widget = self.value_table.cellWidget(row, 4)
            col_name = col_widget.currentText().strip()
            if not col_name:
                continue
            internal_col = single_friendly_to_internal(col_name, self.registry)
            agg_func = agg_widget.currentText().strip()
            setting = {"value_column": internal_col, "aggfunc": agg_func}
            if agg_func.lower() == "concatenate":
                setting["delimiter"] = delim_widget.text().strip()
                setting["distinct"] = distinct_widget.isChecked()
                setting["order"] = order_widget.currentText().strip()
            value_settings.append(setting)
        values["value_settings"] = value_settings
        
        values["missing_fill"] = self.missing_fill_edit.text().strip()
        if self.sort_checkbox.isChecked():
            values["sort"] = {"enabled": True, "order": self.sort_order_combo.currentText()}
        else:
            values["sort"] = {"enabled": False}
        values["computed_metric"] = self.metric_edit.text().strip()
        return values

# --------------------  Unpivot Data Dialog --------------------
class UnpivotDataDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_values=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(" Unpivot Data 🔄")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_values = init_values
        self.initUI()
        if self.init_values:
            self.loadConfig(self.init_values)
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        
        id_layout = QHBoxLayout()
        self.id_vars_edit = QLineEdit()
        self.id_vars_edit.setPlaceholderText("Comma separated or click 'Select Columns'")
        select_id_btn = QPushButton("Select Columns")
        select_id_btn.clicked.connect(self.selectIDVars)
        id_layout.addWidget(self.id_vars_edit)
        id_layout.addWidget(select_id_btn)
        layout.addWidget(QLabel("ID Variables (Columns to remain fixed):"))
        layout.addLayout(id_layout)
        
        val_layout = QHBoxLayout()
        self.value_vars_edit = QLineEdit()
        self.value_vars_edit.setPlaceholderText("Comma separated or click 'Select Columns'")
        select_val_btn = QPushButton("Select Columns")
        select_val_btn.clicked.connect(self.selectValueVars)
        val_layout.addWidget(self.value_vars_edit)
        val_layout.addWidget(select_val_btn)
        layout.addWidget(QLabel("Value Variables (Columns to unpivot):"))
        layout.addLayout(val_layout)
        
        layout.addWidget(QLabel("New Variable Column Name:"))
        self.new_var_edit = QLineEdit()
        self.new_var_edit.setPlaceholderText("Default: variable")
        layout.addWidget(self.new_var_edit)
        
        layout.addWidget(QLabel("New Value Column Name:"))
        self.new_val_edit = QLineEdit()
        self.new_val_edit.setPlaceholderText("Default: value")
        layout.addWidget(self.new_val_edit)
        
        layout.addWidget(QLabel("Data Type Conversion (for unpivoted values):"))
        self.dtype_combo = QComboBox()
        self.dtype_combo.addItems(["None", "String", "Integer", "Float"])
        layout.addWidget(self.dtype_combo)
        
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.showHelp)
        layout.addWidget(help_btn)
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
    
    def loadConfig(self, config):
        if "id_vars" in config:
            friendly = [internal_to_friendly(col, self.registry) for col in config["id_vars"]]
            self.id_vars_edit.setText(", ".join(friendly))
        if "value_vars" in config:
            friendly = [internal_to_friendly(col, self.registry) for col in config["value_vars"]]
            self.value_vars_edit.setText(", ".join(friendly))
        if "new_variable" in config:
            self.new_var_edit.setText(config["new_variable"])
        if "new_value" in config:
            self.new_val_edit.setText(config["new_value"])
        if "dtype_conversion" in config:
            index = self.dtype_combo.findText(config["dtype_conversion"])
            if index != -1:
                self.dtype_combo.setCurrentIndex(index)
    
    def selectIDVars(self):
        dlg = SearchableColumnListDialog(self.friendly_columns, title="Select ID Variables", multi_select=True, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected = dlg.getSelectedColumns()
            self.id_vars_edit.setText(", ".join(selected))
    
    def selectValueVars(self):
        dlg = SearchableColumnListDialog(self.friendly_columns, title="Select Value Variables", multi_select=True, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected = dlg.getSelectedColumns()
            self.value_vars_edit.setText(", ".join(selected))
    
    def showHelp(self):
        help_text = (
            " Unpivot Data Instructions:\n\n"
            "1. Specify the ID Variables (columns to keep as identifiers) and Value Variables (columns to be unpivoted) using comma-separated names or by clicking the 'Select Columns' buttons.\n"
            "2. Optionally, enter new names for the output columns (the column that will contain the former column headers, and the column that will contain the unpivoted values).\n"
            "3. Select a data type conversion for the unpivoted values if needed.\n"
            "4. Click OK to apply the unpivot transformation."
        )
        QMessageBox.information(self, "Unpivot Data Help", help_text)
    
    def getValues(self):
        values = {}
        id_vars = [single_friendly_to_internal(x.strip(), self.registry) for x in self.id_vars_edit.text().split(",") if x.strip()]
        value_vars = [single_friendly_to_internal(x.strip(), self.registry) for x in self.value_vars_edit.text().split(",") if x.strip()]
        values["id_vars"] = id_vars
        values["value_vars"] = value_vars
        values["new_variable"] = self.new_var_edit.text().strip() or "variable"
        values["new_value"] = self.new_val_edit.text().strip() or "value"
        values["dtype_conversion"] = self.dtype_combo.currentText().strip()
        return values

class TransposeDataDialog(QDialog):
    def __init__(self, init_values=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transpose Data ↔️")
        self.init_values = init_values
        self.initUI()
        if self.init_values:
            self.loadConfig(self.init_values)

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        
        message = QLabel("This operation will transpose the entire dataset.\n"
                         "Select additional options to mimic Excel/SQL behavior:")
        layout.addWidget(message)
        
        self.use_header_checkbox = QCheckBox("Use first row as header")
        self.use_header_checkbox.setToolTip(
            "If checked, the first row of the transposed data will be used as the new column headers and then removed."
        )
        layout.addWidget(self.use_header_checkbox)
        
        self.retain_index_checkbox = QCheckBox("Retain original index as first column")
        self.retain_index_checkbox.setToolTip(
            "If checked, the original DataFrame index will be preserved as the first column in the transposed data."
        )
        layout.addWidget(self.retain_index_checkbox)
        
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.showHelp)
        layout.addWidget(help_btn)
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()

    def loadConfig(self, config):
        if "use_first_row_as_header" in config:
            self.use_header_checkbox.setChecked(config["use_first_row_as_header"])
        if "retain_index" in config:
            self.retain_index_checkbox.setChecked(config["retain_index"])

    def showHelp(self):
        help_text = (
            "Transpose Data Help:\n\n"
            "This transformation swaps rows and columns of your dataset.\n\n"
            "Options:\n"
            "1. Use first row as header: When checked, the first row of the transposed output will be used as column headers (and then removed from the data).\n"
            "2. Retain original index as first column: When checked, the original DataFrame index is added as the first column in the transposed result.\n\n"
            "Click OK to apply the transformation with the selected options."
        )
        QMessageBox.information(self, "Transpose Data Help", help_text)

    def getValues(self):
        return {
            "use_first_row_as_header": self.use_header_checkbox.isChecked(),
            "retain_index": self.retain_index_checkbox.isChecked()
        }
    
class SplitColumnDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_values=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Split Column ✂️")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_values = init_values
        self.initUI()
        if self.init_values:
            self.loadConfig(self.init_values)
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        
        layout.addWidget(QLabel("Select Column to Split:"))
        self.col_combo = create_combo_box(self.friendly_columns, editable=True)
        layout.addWidget(self.col_combo)
        
        layout.addWidget(QLabel("Enter Delimiter:"))
        self.delim_edit = QLineEdit()
        self.delim_edit.setPlaceholderText("e.g., ',' or ' '")
        layout.addWidget(self.delim_edit)
        
        layout.addWidget(QLabel("New Column Name for First Part (optional):"))
        self.newcol1_edit = QLineEdit()
        layout.addWidget(self.newcol1_edit)
        
        layout.addWidget(QLabel("New Column Name for Second Part (optional):"))
        self.newcol2_edit = QLineEdit()
        layout.addWidget(self.newcol2_edit)
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()

    def loadConfig(self, config):
        if "split_column" in config:
            friendly = internal_to_friendly(config["split_column"], self.registry)
            index = self.col_combo.findText(friendly)
            if index != -1:
                self.col_combo.setCurrentIndex(index)
            else:
                self.col_combo.setCurrentText(friendly)
        if "split_char" in config:
            self.delim_edit.setText(config["split_char"])
        if "new_col1" in config:
            self.newcol1_edit.setText(config["new_col1"])
        if "new_col2" in config:
            self.newcol2_edit.setText(config["new_col2"])
    
    def getValues(self):
        values = {}
        friendly = self.col_combo.currentText()
        col_id = single_friendly_to_internal(friendly, self.registry)
        if col_id:
            values["split_column"] = col_id
        values["split_char"] = self.delim_edit.text().strip()
        new1 = self.newcol1_edit.text().strip()
        new2 = self.newcol2_edit.text().strip()
        if new1:
            values["new_col1"] = new1
        if new2:
            values["new_col2"] = new2
        return values
    
class ConcatenateColumnsDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_values=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Concatenate Columns 🔗")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_values = init_values
        self.initUI()
        if self.init_values:
            self.loadConfig(self.init_values)
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        
        layout.addWidget(QLabel("Select Columns to Concatenate:"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for col in self.friendly_columns:
            self.list_widget.addItem(QListWidgetItem(col))
        layout.addWidget(self.list_widget)
        
        layout.addWidget(QLabel("Enter Delimiter:"))
        self.delim_edit = QLineEdit()
        self.delim_edit.setPlaceholderText("Enter delimiter")
        layout.addWidget(self.delim_edit)
        
        layout.addWidget(QLabel("Enter New Column Name:"))
        self.newcol_edit = QLineEdit()
        layout.addWidget(self.newcol_edit)
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()

    def loadConfig(self, config):
        if "columns" in config:
            friendly_selected = [internal_to_friendly(col, self.registry) for col in config["columns"]]
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.text() in friendly_selected:
                    item.setSelected(True)
        if "delimiter" in config:
            self.delim_edit.setText(config["delimiter"])
        if "new_column" in config:
            self.newcol_edit.setText(config["new_column"])
    
    def getValues(self):
        values = {}
        selected = [item.text() for item in self.list_widget.selectedItems()]
        cols = [single_friendly_to_internal(f, self.registry) for f in selected]
        values["columns"] = [col for col in cols if col]
        values["delimiter"] = self.delim_edit.text().strip()
        values["new_column"] = self.newcol_edit.text().strip()
        return values

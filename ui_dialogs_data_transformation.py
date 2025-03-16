# -----------------------------------------------------------------------------
# Copyright (c) [2025] [Vamshi Krishna Nagabhyru]
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
from PyQt6.QtCore import Qt 
from PyQt6.QtWidgets import (
    QFormLayout,QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QAbstractItemView,
    QSpinBox, QLayout, QListWidget, QListWidgetItem, QPushButton, QHeaderView, QTableWidget,QTableWidgetItem
)
from ui_helpers import add_ok_cancel_buttons, create_combo_box, single_friendly_to_internal, internal_to_friendly
from ui_dialogs_data_cleaning import SearchableColumnListDialog
from help_system import get_help_section, HelpDialog
# -------------------- Generate Unique IDs Dialog --------------------

class GenerateUniqueIDsDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Generate Unique IDs")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # New column name input:
        self.newcol_edit = QLineEdit()
        self.newcol_edit.setPlaceholderText("e.g., unique_id")
        if "new_column" in self.init_params:
            self.newcol_edit.setText(self.init_params["new_column"])
        form.addRow("New Column Name:", self.newcol_edit)
        
        # Method selection:
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Sequence", "UUID", "Hashkey"])
        if "method" in self.init_params:
            method = self.init_params["method"].capitalize()
            idx = self.method_combo.findText(method)
            if idx >= 0:
                self.method_combo.setCurrentIndex(idx)
        form.addRow("ID Generation Method:", self.method_combo)
        
        # Hashkey column selection (only visible if Hashkey is chosen):
        self.hash_label = QLabel("Select Columns for Hash Key:")
        self.hash_label.setVisible(False)
        form.addRow("", self.hash_label)
        self.hash_list = QListWidget()
        self.hash_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for col in self.friendly_columns:
            self.hash_list.addItem(QListWidgetItem(col))
        self.hash_list.setVisible(False)
        form.addRow("", self.hash_list)
        
        # Help text:
        help_label = QLabel(
            "From the drop down select sequance type Help: 'Sequence' assigns incremental numbers; 'UUID' uses a random unique identifier; "
            "'Hashkey' creates a hash based on selected columns."
        )
        help_label.setWordWrap(True)
        form.addRow("Info:", help_label)
        
        layout.addLayout(form)
        add_ok_cancel_buttons(self, layout)
        self.method_combo.currentTextChanged.connect(self.onMethodChanged)
        self.setLayout(layout)
        self.adjustSize()
    
    def onMethodChanged(self, text):
        if text.lower() == "hashkey":
            self.hash_label.setVisible(True)
            self.hash_list.setVisible(True)
        else:
            self.hash_label.setVisible(False)
            self.hash_list.setVisible(False)
    
    def getValues(self):
        values = {}
        new_col = self.newcol_edit.text().strip()
        if new_col:
            values["new_column"] = new_col
        values["method"] = self.method_combo.currentText().lower()
        if values["method"] == "hashkey":
            selected_friendly = [item.text() for item in self.hash_list.selectedItems()]
            internal_cols = [single_friendly_to_internal(f, self.registry) for f in selected_friendly if single_friendly_to_internal(f, self.registry)]
            values["columns"] = internal_cols
        return values
# -------------------- Convert Datatype Dialog --------------------
class ConvertDatatypeDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Convert Datatype 🔄")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.selected_columns = self.init_params.get("columns", {})  # Store user selections
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        # Column selection list
        layout.addWidget(QLabel("Select Columns to Convert:"))
        self.list_columns = QListWidget()
        self.list_columns.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list_columns.addItems(self.friendly_columns)
        layout.addWidget(self.list_columns)

        # Button to add selected columns to table
        btn_add_selected = QPushButton("➕ Add Selected Columns")
        btn_add_selected.clicked.connect(self.addSelectedColumns)
        layout.addWidget(btn_add_selected)

        # Table for column conversion settings
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Column", "New Type", "Error Handling", "Default Value"])
        layout.addWidget(self.table)

        # Restore previous selections
        self.restoreSelections()

        # Remove Selected Rows
        btn_remove = QPushButton("❌ Remove Selected Rows")
        btn_remove.clicked.connect(self.removeSelectedRows)
        layout.addWidget(btn_remove)

        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
    
    def restoreSelections(self):
        """Restores previously selected columns and their configurations."""
        for col_id, settings in self.selected_columns.items():
            friendly_name = internal_to_friendly(col_id, self.registry)
            if friendly_name in self.friendly_columns:
                self.addTableRow(friendly_name, settings.get("new_type", "str"), settings.get("errors", "coerce"), settings.get("default_value", ""))
    
    def addSelectedColumns(self):
        """Add selected columns from the list to the conversion table."""
        for item in self.list_columns.selectedItems():
            column_name = item.text()
            if not self.isAlreadyInTable(column_name):
                self.addTableRow(column_name, "datetime", "coerce", "")  # Default type: datetime, error handling: coerce, default value: empty
    
    def isAlreadyInTable(self, column_name):
        """Check if a column is already in the table."""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0) and self.table.item(row, 0).text() == column_name:
                return True
        return False
    
    def addTableRow(self, column_name, data_type, error_handling, default_value):
        """Add a row for column conversion settings."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Column name (read-only)
        item_col = QTableWidgetItem(column_name)
        item_col.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.table.setItem(row, 0, item_col)

        # Data type dropdown
        type_combo = QComboBox()
        type_combo.addItems([
            "int", "float", "str", "datetime", "date", "boolean", "category", "decimal", "json", "list", "timedelta", "User Defined"
        ])
        type_combo.setCurrentText(data_type)
        self.table.setCellWidget(row, 1, type_combo)

        # Error handling dropdown
        error_combo = QComboBox()
        error_combo.addItems(["coerce", "ignore", "raise"])
        error_combo.setCurrentText(error_handling)
        self.table.setCellWidget(row, 2, error_combo)

        # Default value input
        default_edit = QLineEdit()
        default_edit.setText(default_value)
        self.table.setCellWidget(row, 3, default_edit)
    
    def removeSelectedRows(self):
        """Remove selected rows from the table."""
        rows_to_remove = {rng.topRow() for rng in self.table.selectedRanges()}
        for row in sorted(rows_to_remove, reverse=True):
            self.table.removeRow(row)
    
    def getValues(self):
        """Return column conversion settings and persist selections."""
        column_mappings = {}
        for row in range(self.table.rowCount()):
            col_name = self.table.item(row, 0).text().strip()
            col_id = single_friendly_to_internal(col_name, self.registry)
            if col_id:
                column_mappings[col_id] = {
                    "new_type": self.table.cellWidget(row, 1).currentText().strip(),
                    "errors": self.table.cellWidget(row, 2).currentText().strip(),
                    "default_value": self.table.cellWidget(row, 3).text().strip()
                }
        self.selected_columns = column_mappings  # Persist selections
        return {"columns": column_mappings}
# -------------------- Generic Transformation Dialog --------------------
class GenericTransformationDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, param_defs=None,
                 dialog_title="Configure Transformation", multi_col_label="Select Column:", parent=None):
        super().__init__(parent)
        self.setWindowTitle(dialog_title + " ⚙️")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.param_defs = param_defs or []
        self._widgets = {}
        self.initUI(multi_col_label)
    
    def initUI(self, multi_col_label):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        # Transformation order (optional)
        layout.addWidget(QLabel("Transformation Order (optional, integer):"))
        self.order_edit = QLineEdit()
        self.order_edit.setPlaceholderText("e.g., 100")
        if "order" in self.init_params:
            self.order_edit.setText(str(self.init_params["order"]))
        layout.addWidget(self.order_edit)
        # Column selection with drop-down (searchable)
        if self.friendly_columns:
            layout.addWidget(QLabel(multi_col_label))
            self.col_combo = create_combo_box(self.friendly_columns, editable=True)
            if "column" in self.init_params:
                friendly = internal_to_friendly(self.init_params["column"], self.registry)
                if friendly in self.friendly_columns:
                    self.col_combo.setCurrentText(friendly)
            layout.addWidget(self.col_combo)
        for pdef in self.param_defs:
            layout.addWidget(QLabel(pdef["label"]))
            if pdef["type"] == "int":
                widget = QSpinBox()
                widget.setRange(-999999, 999999)
                widget.setValue(int(self.init_params.get(pdef["name"], 0)))
            else:
                widget = QLineEdit(str(self.init_params.get(pdef["name"], "")))
            layout.addWidget(widget)
            self._widgets[pdef["name"]] = widget
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
    
    def getValues(self):
        values = {}
        order_text = self.order_edit.text().strip()
        if order_text.isdigit():
            values["order"] = int(order_text)
        if self.friendly_columns:
            friendly = self.col_combo.currentText()
            col_id = single_friendly_to_internal(friendly, self.registry)
            if col_id:
                values["column"] = col_id
        for pdef in self.param_defs:
            if pdef["type"] == "int":
                values[pdef["name"]] = self._widgets[pdef["name"]].value()
            else:
                values[pdef["name"]] = self._widgets[pdef["name"]].text().strip()
        return values
# -------------------- New Dialogs for Aggregations & Analytical Functions --------------------
class GroupAggregateDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Group & Aggregate")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.selected_group_cols = []
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        
        # Group Columns selection using a searchable drop-down button
        group_layout = QHBoxLayout()
        group_layout.addWidget(QLabel("Group Columns:"))
        self.group_cols_display = QLineEdit()
        self.group_cols_display.setReadOnly(True)
        group_layout.addWidget(self.group_cols_display)
        btn_select = QPushButton("Select...")
        btn_select.clicked.connect(self.selectGroupColumns)
        group_layout.addWidget(btn_select)
        layout.addLayout(group_layout)
        
        # Table for aggregation rules – now 4 columns: Target Column, Aggregation Function, New Column Name, and Having Condition.
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Target Column", "Aggregation Function", "New Column Name", "Having Condition"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # Buttons to add/remove rows
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Rule")
        self.btn_add.clicked.connect(self.addRow)
        btn_layout.addWidget(self.btn_add)
        self.btn_remove = QPushButton("Remove Selected Rule")
        self.btn_remove.clicked.connect(self.removeRow)
        btn_layout.addWidget(self.btn_remove)
        layout.addLayout(btn_layout)
        
        # OK / Cancel buttons
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
        
        # Load initial parameters if provided.
        if "group_columns" in self.init_params:
            self.selected_group_cols = self.init_params["group_columns"]
            friendly = [internal_to_friendly(col, self.registry) for col in self.selected_group_cols]
            self.group_cols_display.setText(", ".join(friendly))
        if "aggregations" in self.init_params:
            self.loadInitialData(self.init_params.get("aggregations"),
                                 self.init_params.get("new_names", {}),
                                 self.init_params.get("having", {}))
    
    def selectGroupColumns(self):
        dlg = SearchableColumnListDialog(self.friendly_columns,
                                         title="Select Group Columns",
                                         multi_select=True,
                                         parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected = dlg.getSelectedColumns()
            self.selected_group_cols = [single_friendly_to_internal(col, self.registry) for col in selected]
            friendly = [internal_to_friendly(col, self.registry) for col in self.selected_group_cols]
            self.group_cols_display.setText(", ".join(friendly))
    
    def addRow(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # Target Column: searchable drop-down
        target_cb = create_combo_box(self.friendly_columns, editable=True)
        self.table.setCellWidget(row, 0, target_cb)
        # Aggregation Function drop-down – include common functions and "count_distinct"
        agg_cb = QComboBox()
        agg_cb.addItems(["sum", "mean", "max", "min", "count", "count_distinct", "median", "std", "var"])
        self.table.setCellWidget(row, 1, agg_cb)
        # New Column Name: free text (optional)
        newcol_edit = QLineEdit()
        self.table.setCellWidget(row, 2, newcol_edit)
        # Having Condition: free text (optional), e.g. "== 1" or "> 1"
        having_edit = QLineEdit()
        having_edit.setPlaceholderText("e.g. == 1 or > 1")
        self.table.setCellWidget(row, 3, having_edit)
    
    def removeRow(self):
        selected = self.table.selectedRanges()
        if selected:
            row = selected[0].topRow()
            self.table.removeRow(row)
    
    def loadInitialData(self, aggregations, new_names, having):
        # aggregations: dictionary where keys are target columns and values are a function or list of functions.
        # new_names: mapping from (target, func) to alias.
        # having: mapping from (target, func) or aggregated alias to condition string.
        for target, funcs in aggregations.items():
            if not isinstance(funcs, list):
                funcs = [funcs]
            for func in funcs:
                self.addRow()
                row = self.table.rowCount() - 1
                self.table.cellWidget(row, 0).setCurrentText(internal_to_friendly(target, self.registry))
                self.table.cellWidget(row, 1).setCurrentText(str(func))
                key = (target, func)
                if key in new_names:
                    self.table.cellWidget(row, 2).setText(new_names[key])
                if key in having:
                    self.table.cellWidget(row, 3).setText(having[key])
    def getValues(self):
            values = {}
            values["group_columns"] = self.selected_group_cols
            aggregations = {}
            new_names = {}
            having = {}
            for row in range(self.table.rowCount()):
                friendly_target = self.table.cellWidget(row, 0).currentText().strip()
                target = single_friendly_to_internal(friendly_target, self.registry)
                agg = self.table.cellWidget(row, 1).currentText().strip()
                newcol = self.table.cellWidget(row, 2).text().strip()
                having_condition = self.table.cellWidget(row, 3).text().strip()
                if target in aggregations:
                    if isinstance(aggregations[target], list):
                        aggregations[target].append(agg)
                    else:
                        aggregations[target] = [aggregations[target], agg]
                else:
                    aggregations[target] = agg
                if newcol:
                    new_names[(target, agg)] = newcol
                if having_condition:
                    alias = new_names.get((target, agg), f"{target}_{agg}")
                    having[alias] = having_condition
            values["aggregations"] = aggregations
            if new_names:
                values["new_names"] = new_names
            if having:
                values["having"] = having
            return values
    
    def getValues(self):
        values = {}
        values["group_columns"] = self.selected_group_cols
        aggregations = {}
        new_names = {}
        having = {}
        for row in range(self.table.rowCount()):
            friendly_target = self.table.cellWidget(row, 0).currentText().strip()
            target = single_friendly_to_internal(friendly_target, self.registry)
            agg = self.table.cellWidget(row, 1).currentText().strip()
            newcol = self.table.cellWidget(row, 2).text().strip()
            having_condition = self.table.cellWidget(row, 3).text().strip()
            # If target already exists, create a list; otherwise store a single value.
            if target in aggregations:
                if isinstance(aggregations[target], list):
                    aggregations[target].append(agg)
                else:
                    aggregations[target] = [aggregations[target], agg]
            else:
                aggregations[target] = agg
            if newcol:
                new_names[(target, agg)] = newcol
            if having_condition:
                # Determine the alias for this aggregation rule.
                alias = new_names.get((target, agg), f"{target}_{agg}")
                having[alias] = having_condition
        values["aggregations"] = aggregations
        if new_names:
            values["new_names"] = new_names
        if having:
            values["having"] = having
        return values
    
class DetectOutliersDialog(QDialog):

    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Detect Outliers")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Column selection:
        self.col_combo = create_combo_box(self.friendly_columns, editable=True)
        if "column" in self.init_params:
            friendly = internal_to_friendly(self.init_params["column"], self.registry)
            if friendly in self.friendly_columns:
                self.col_combo.setCurrentText(friendly)
        form.addRow("Column to Analyze:", self.col_combo)
        
        # Outlier detection method:
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Z-Score", "IQR", "MAD"])
        if "method" in self.init_params:
            method = self.init_params["method"].capitalize()
            idx = self.method_combo.findText(method)
            if idx >= 0:
                self.method_combo.setCurrentIndex(idx)
        form.addRow("Detection Method:", self.method_combo)
        
        # Threshold parameter:
        self.threshold_edit = QLineEdit()
        self.threshold_edit.setPlaceholderText("e.g., 3.0 (Z-Score), 1.5 (IQR), 3.0 (MAD)")
        if "threshold" in self.init_params:
            self.threshold_edit.setText(str(self.init_params["threshold"]))
        form.addRow("Threshold:", self.threshold_edit)
        
        # New flag column name:
        self.new_flag_edit = QLineEdit()
        self.new_flag_edit.setPlaceholderText("e.g., outlier_flag")
        if "new_flag" in self.init_params:
            self.new_flag_edit.setText(self.init_params["new_flag"])
        form.addRow("New Flag Column:", self.new_flag_edit)
        
        # Help information:
        help_label = QLabel(
            "Help: Z-Score is based on the mean and standard deviation; IQR uses the interquartile range; "
            "MAD uses the median absolute deviation. Choose the method that best suits your data distribution."
        )
        help_label.setWordWrap(True)
        form.addRow("Info:", help_label)
        
        layout.addLayout(form)
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
    
    def getValues(self):
        values = {}
        friendly = self.col_combo.currentText().strip()
        col_id = single_friendly_to_internal(friendly, self.registry)
        if col_id:
            values["column"] = col_id
        values["method"] = self.method_combo.currentText().lower()
        try:
            values["threshold"] = float(self.threshold_edit.text().strip())
        except:
            values["threshold"] = 3.0  # default value
        values["new_flag"] = self.new_flag_edit.text().strip() or f"{friendly}_outlier"
        return values
# -------------------- Analytical Functions Dialog --------------------
class AnalyticalFunctionsDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):

        super().__init__(parent)
        self.setWindowTitle("Configure Analytical Functions")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.selected_group_cols = []
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        
        # Group columns selection using a button
        group_layout = QHBoxLayout()
        group_layout.addWidget(QLabel("Group Columns:"))
        self.group_cols_display = QLineEdit()
        self.group_cols_display.setReadOnly(True)
        group_layout.addWidget(self.group_cols_display)
        btn_select = QPushButton("Select...")
        btn_select.clicked.connect(self.selectGroupColumns)
        group_layout.addWidget(btn_select)
        layout.addLayout(group_layout)
        
        # Table for analytical rules (4 columns: Target, Function, Parameters, New Column)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Target Column", "Function", "Parameters", "New Column Name"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # Buttons to add/remove rows
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Rule")
        self.btn_add.clicked.connect(self.addRow)
        btn_layout.addWidget(self.btn_add)
        self.btn_remove = QPushButton("Remove Selected Rule")
        self.btn_remove.clicked.connect(self.removeRow)
        btn_layout.addWidget(self.btn_remove)
        layout.addLayout(btn_layout)
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
        
        if "group_columns" in self.init_params:
            self.selected_group_cols = self.init_params["group_columns"]
            friendly = [internal_to_friendly(col, self.registry) for col in self.selected_group_cols]
            self.group_cols_display.setText(", ".join(friendly))
        if "analytical" in self.init_params:
            self.loadInitialData(self.init_params["analytical"])
    
    def selectGroupColumns(self):
        dlg = SearchableColumnListDialog(self.friendly_columns, title="Select Group Columns", multi_select=True, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected = dlg.getSelectedColumns()
            self.selected_group_cols = [single_friendly_to_internal(col, self.registry) for col in selected]
            friendly = [internal_to_friendly(col, self.registry) for col in self.selected_group_cols]
            self.group_cols_display.setText(", ".join(friendly))
    
    def addRow(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # Target Column: searchable drop-down
        target_cb = create_combo_box(self.friendly_columns, editable=True)
        self.table.setCellWidget(row, 0, target_cb)
        # Function drop-down with extended functions
        func_cb = QComboBox()
        func_cb.addItems(["rank", "dense_rank", "percent_rank", "row_number", "cumsum", "rolling_mean", "lag", "lead"])
        self.table.setCellWidget(row, 1, func_cb)
        # Parameter field: free text with placeholder (user can specify key:value pairs, e.g., "order_by:date, method:dense")
        param_edit = QLineEdit()
        param_edit.setPlaceholderText("e.g., order_by:date, method:dense; for rolling_mean: window[,min_periods]; for lag/lead: periods")
        self.table.setCellWidget(row, 2, param_edit)
        # New Column Name: free text (optional)
        newcol_edit = QLineEdit()
        self.table.setCellWidget(row, 3, newcol_edit)
    
    def removeRow(self):
        selected = self.table.selectedRanges()
        if selected:
            row = selected[0].topRow()
            self.table.removeRow(row)
    
    def loadInitialData(self, analytical):
        # analytical: dict {target_column: {function: {params}}}
        for target, funcs in analytical.items():
            for func, params in funcs.items():
                self.addRow()
                row = self.table.rowCount() - 1
                self.table.cellWidget(row, 0).setCurrentText(internal_to_friendly(target, self.registry))
                self.table.cellWidget(row, 1).setCurrentText(func)
                # For parameters, convert the params dict to a comma-separated key:value string.
                param_value = ", ".join(f"{k}:{v}" for k, v in params.items() if k != "new_column")
                self.table.cellWidget(row, 2).setText(param_value)
                if "new_column" in params:
                    self.table.cellWidget(row, 3).setText(params["new_column"])
    
    def getValues(self):
        values = {}
        if self.selected_group_cols:
            values["group_columns"] = self.selected_group_cols
        analytical = {}
        for row in range(self.table.rowCount()):
            friendly_target = self.table.cellWidget(row, 0).currentText().strip()
            target = single_friendly_to_internal(friendly_target, self.registry)
            func = self.table.cellWidget(row, 1).currentText().strip()
            param_text = self.table.cellWidget(row, 2).text().strip()
            newcol = self.table.cellWidget(row, 3).text().strip()
            params = {}
            if param_text:
                # Parse parameters entered as comma-separated key:value pairs.
                parts = [p.strip() for p in param_text.split(",") if p.strip()]
                for part in parts:
                    if ":" in part:
                        key, value = part.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        # Try to convert numeric parameters to int if possible.
                        try:
                            value = int(value)
                        except ValueError:
                            pass
                        params[key] = value
            if newcol:
                params["new_column"] = newcol
            if target not in analytical:
                analytical[target] = {}
            analytical[target][func] = params
        values["analytical"] = analytical
        return values

class NormalizeDataDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Normalize Data")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Numeric column selection:
        self.col_combo = create_combo_box(self.friendly_columns, editable=True)
        if "column" in self.init_params:
            friendly = internal_to_friendly(self.init_params["column"], self.registry)
            if friendly in self.friendly_columns:
                self.col_combo.setCurrentText(friendly)
        form.addRow("Numeric Column:", self.col_combo)
        
        # Normalization method:
        self.method_combo = QComboBox()
        self.method_combo.addItems(["minmax", "zscore"])
        if "norm_method" in self.init_params:
            idx = self.method_combo.findText(self.init_params["norm_method"].lower())
            if idx >= 0:
                self.method_combo.setCurrentIndex(idx)
        form.addRow("Normalization Method:", self.method_combo)
        
        # Help text:
        help_label = QLabel(
            "Help: 'minmax' scales values to the range 0-1; 'zscore' standardizes values based on the mean and standard deviation."
        )
        help_label.setWordWrap(True)
        form.addRow("Info:", help_label)
        
        layout.addLayout(form)
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
    
    def getValues(self):
        values = {}
        friendly = self.col_combo.currentText().strip()
        col_id = single_friendly_to_internal(friendly, self.registry)
        if col_id:
            values["column"] = col_id
        values["norm_method"] = self.method_combo.currentText().lower()
        return values

class DateFormatDialog(QDialog):
    """
    A configuration dialog for standardizing date formats.
    Allows selection of the target date column, desired output format, timezone, and optional input formats.
    """
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Standardize Date Format")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Date column selection:
        self.col_combo = create_combo_box(self.friendly_columns, editable=True)
        if "column" in self.init_params:
            friendly = internal_to_friendly(self.init_params["column"], self.registry)
            if friendly in self.friendly_columns:
                self.col_combo.setCurrentText(friendly)
        form.addRow("Date Column:", self.col_combo)
        
        # Target date format:
        self.format_edit = QLineEdit()
        self.format_edit.setPlaceholderText("e.g., %Y-%m-%d")
        if "date_format" in self.init_params:
            self.format_edit.setText(self.init_params["date_format"])
        form.addRow("Target Date Format:", self.format_edit)
        
        # Timezone (optional):
        self.tz_edit = QLineEdit()
        self.tz_edit.setPlaceholderText("e.g., UTC")
        if "timezone" in self.init_params:
            self.tz_edit.setText(self.init_params["timezone"])
        form.addRow("Timezone (optional):", self.tz_edit)
        
        # Input formats (optional):
        self.input_formats_edit = QLineEdit()
        self.input_formats_edit.setPlaceholderText("e.g., %d/%m/%Y, %Y-%m-%d")
        if "input_formats" in self.init_params:
            if isinstance(self.init_params["input_formats"], list):
                self.input_formats_edit.setText(", ".join(self.init_params["input_formats"]))
            else:
                self.input_formats_edit.setText(self.init_params["input_formats"])
        form.addRow("Input Date Formats:", self.input_formats_edit)
        
        # Help text:
        help_label = QLabel(
            "Help: Specify the desired output format as a strftime string. "
            "Optional input formats can be provided as alternatives (comma-separated) to help parse the date."
        )
        help_label.setWordWrap(True)
        form.addRow("Info:", help_label)
        
        layout.addLayout(form)
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
    
    def getValues(self):
        values = {}
        friendly = self.col_combo.currentText().strip()
        col_id = single_friendly_to_internal(friendly, self.registry)
        if col_id:
            values["column"] = col_id
        values["date_format"] = self.format_edit.text().strip() or "%Y-%m-%d"
        tz = self.tz_edit.text().strip()
        if tz:
            values["timezone"] = tz
        input_formats = self.input_formats_edit.text().strip()
        if input_formats:
            values["input_formats"] = [fmt.strip() for fmt in input_formats.split(",") if fmt.strip()]
        return values

class GenericTransformationDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, param_defs=None,
                 dialog_title="Configure Transformation", multi_col_label="Select Column:", 
                 help_section="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(dialog_title + " ⚙️")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.param_defs = param_defs or []
        self.help_section = help_section  # new parameter for help key
        self._widgets = {}
        self.initUI(multi_col_label)
    
    def initUI(self, multi_col_label):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        # Transformation order (optional)
        layout.addWidget(QLabel("Transformation Order (optional, integer):"))
        self.order_edit = QLineEdit()
        self.order_edit.setPlaceholderText("e.g., 100")
        if "order" in self.init_params:
            self.order_edit.setText(str(self.init_params["order"]))
        layout.addWidget(self.order_edit)
        
        # Add a Help button if a help_section is provided
        if self.help_section:
            btn_help = QPushButton("Help")
            btn_help.clicked.connect(lambda: self.show_help())
            layout.addWidget(btn_help)
        
        # Column selection with drop-down (searchable)
        if self.friendly_columns:
            layout.addWidget(QLabel(multi_col_label))
            self.col_combo = create_combo_box(self.friendly_columns, editable=True)
            if "column" in self.init_params:
                friendly = internal_to_friendly(self.init_params["column"], self.registry)
                if friendly in self.friendly_columns:
                    self.col_combo.setCurrentText(friendly)
            layout.addWidget(self.col_combo)
        # Additional parameter fields
        for pdef in self.param_defs:
            layout.addWidget(QLabel(pdef["label"]))
            if pdef["type"] == "int":
                widget = QSpinBox()
                widget.setRange(-999999, 999999)
                widget.setValue(int(self.init_params.get(pdef["name"], 0)))
            else:
                widget = QLineEdit(str(self.init_params.get(pdef["name"], "")))
            layout.addWidget(widget)
            self._widgets[pdef["name"]] = widget
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
    
    def show_help(self):
        help_text = get_help_section(self.help_section)
        dlg = HelpDialog(help_text, parent=self)
        dlg.exec()
    
    def getValues(self):
        values = {}
        order_text = self.order_edit.text().strip()
        if order_text.isdigit():
            values["order"] = int(order_text)
        if self.friendly_columns:
            friendly = self.col_combo.currentText()
            col_id = single_friendly_to_internal(friendly, self.registry)
            if col_id:
                values["column"] = col_id
        for pdef in self.param_defs:
            if pdef["type"] == "int":
                values[pdef["name"]] = self._widgets[pdef["name"]].value()
            else:
                values[pdef["name"]] = self._widgets[pdef["name"]].text().strip()
        return values
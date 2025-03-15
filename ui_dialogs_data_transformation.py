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
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QSpinBox, QLayout, QListWidget, QListWidgetItem, QPushButton, QHeaderView, QTableWidget,QTableWidgetItem
)
from ui_helpers import add_ok_cancel_buttons, create_combo_box, single_friendly_to_internal, internal_to_friendly
from ui_dialogs_data_cleaning import SearchableColumnListDialog
from help_system import get_help_section, HelpDialog
# -------------------- Generate Unique IDs Dialog --------------------

class GenerateUniqueIDsDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Generate Unique IDs 🔑")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.selected_columns = set()
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        # New Column Name
        layout.addWidget(QLabel("Enter New Column Name:"))
        self.newcol_edit = QLineEdit()
        self.newcol_edit.setPlaceholderText("e.g., unique_id")
        if "new_column" in self.init_params:
            self.newcol_edit.setText(self.init_params["new_column"])
        layout.addWidget(self.newcol_edit)
        
        # Method Selection
        layout.addWidget(QLabel("Select ID Generation Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Sequence", "UUID", "Hashkey"])
        if "method" in self.init_params:
            idx = self.method_combo.findText(self.init_params["method"].capitalize())
            if idx >= 0:
                self.method_combo.setCurrentIndex(idx)
        layout.addWidget(self.method_combo)
        
        # Hashkey: Select multiple columns
        self.hash_columns_label = QLabel("Select Columns for Hash Key:")
        self.hash_columns_label.setVisible(False)
        layout.addWidget(self.hash_columns_label)
        
        self.hash_list = QListWidget()
        self.hash_list.setSelectionMode(QListWidget.MultiSelection)
        for col in self.friendly_columns:
            self.hash_list.addItem(QListWidgetItem(col))
        self.hash_list.setVisible(False)
        layout.addWidget(self.hash_list)
        # Connect method change
        self.method_combo.currentTextChanged.connect(self.onMethodChanged)
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
    
    def onMethodChanged(self, text):
        """Show column selection only when Hashkey is selected."""
        if text.lower() == "hashkey":
            self.hash_columns_label.setVisible(True)
            self.hash_list.setVisible(True)
        else:
            self.hash_columns_label.setVisible(False)
            self.hash_list.setVisible(False)
    
    def getValues(self):
        values = {}
        new_column = self.newcol_edit.text().strip()
        if new_column:
            values["new_column"] = new_column
        method = self.method_combo.currentText().lower()
        values["method"] = method
        
        if method == "hashkey":
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
        layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        # Column selection list
        layout.addWidget(QLabel("Select Columns to Convert:"))
        self.list_columns = QListWidget()
        self.list_columns.setSelectionMode(QListWidget.MultiSelection)
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
        item_col.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
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
        layout.setSizeConstraint(QLayout.SetMinimumSize)
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
        """
        Dialog to configure group and aggregate transformations.
        User provides:
          - Group Columns: selected via a searchable drop-down.
          - Aggregations: entered as JSON mapping target columns to aggregation functions.
          - Optional new names mapping: entered as JSON.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure Group & Aggregate")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.selected_group_cols = []
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        
        # Group Columns selection using a button (drop-down searchable)
        group_layout = QHBoxLayout()
        group_layout.addWidget(QLabel("Group Columns:"))
        self.group_cols_display = QLineEdit()
        self.group_cols_display.setReadOnly(True)
        group_layout.addWidget(self.group_cols_display)
        btn_select = QPushButton("Select...")
        btn_select.clicked.connect(self.selectGroupColumns)
        group_layout.addWidget(btn_select)
        layout.addLayout(group_layout)
        
        # Table for aggregation rules
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Target Column", "Aggregation Function", "New Column Name"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
        if "aggregations" in self.init_params:
            self.loadInitialData(self.init_params.get("aggregations"), self.init_params.get("new_names", {}))
    
    def selectGroupColumns(self):
        dlg = SearchableColumnListDialog(self.friendly_columns, title="Select Group Columns", multi_select=True, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            selected = dlg.getSelectedColumns()
            self.selected_group_cols = [single_friendly_to_internal(col, self.registry) for col in selected]
            friendly = [internal_to_friendly(col, self.registry) for col in self.selected_group_cols]
            self.group_cols_display.setText(", ".join(friendly))
    
    def addRow(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # Use a searchable drop-down for target column
        target_cb = create_combo_box(self.friendly_columns, editable=True)
        self.table.setCellWidget(row, 0, target_cb)
        # Aggregation Function drop-down with common functions
        agg_cb = QComboBox()
        agg_cb.addItems(["sum", "mean", "max", "min", "count", "median", "std", "var"])
        self.table.setCellWidget(row, 1, agg_cb)
        # New Column Name: free text (optional)
        newcol_edit = QLineEdit()
        self.table.setCellWidget(row, 2, newcol_edit)
    
    def removeRow(self):
        selected = self.table.selectedRanges()
        if selected:
            row = selected[0].topRow()
            self.table.removeRow(row)
    
    def loadInitialData(self, aggregations, new_names):
        for target, funcs in aggregations.items():
            # funcs can be a list or a single function
            for func in (funcs if isinstance(funcs, list) else [funcs]):
                self.addRow()
                row = self.table.rowCount() - 1
                self.table.cellWidget(row, 0).setCurrentText(internal_to_friendly(target, self.registry))
                self.table.cellWidget(row, 1).setCurrentText(func)
                key = (target, func)
                if key in new_names:
                    self.table.cellWidget(row, 2).setText(new_names[key])
    
    def getValues(self):
        values = {}
        values["group_columns"] = self.selected_group_cols
        aggregations = {}
        new_names = {}
        for row in range(self.table.rowCount()):
            friendly_target = self.table.cellWidget(row, 0).currentText().strip()
            target = single_friendly_to_internal(friendly_target, self.registry)
            agg = self.table.cellWidget(row, 1).currentText().strip()
            newcol = self.table.cellWidget(row, 2).text().strip()
            if target in aggregations:
                if isinstance(aggregations[target], list):
                    aggregations[target].append(agg)
                else:
                    aggregations[target] = [aggregations[target], agg]
            else:
                aggregations[target] = agg
            if newcol:
                new_names[(target, agg)] = newcol
        values["aggregations"] = aggregations
        if new_names:
            values["new_names"] = new_names
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
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        
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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
        if dlg.exec_() == QDialog.Accepted:
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
        layout.setSizeConstraint(QLayout.SetMinimumSize)
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
        dlg.exec_()
    
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
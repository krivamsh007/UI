# -----------------------------------------------------------------------------
# Copyright (c) [2025] [Vamshi Krishna Nagabhyru]
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
from PyQt6.QtWidgets import (QAbstractItemView,QAbstractScrollArea,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QListWidget, QListWidgetItem, QPushButton, QLayout,QGroupBox,
  QCheckBox,QTableWidgetItem,QWidget,QSizePolicy,QAbstractItemView,QMessageBox,
)
from PyQt6.QtCore import Qt
from ui_helpers import add_ok_cancel_buttons, create_combo_box, single_friendly_to_internal, internal_to_friendly, create_add_remove_buttons
import logging
logger = logging.getLogger(__name__)

class SearchableColumnListDialog(QDialog):
    def __init__(self, columns, title="Select Columns", multi_select=True, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.all_columns = columns
        self.multi_select = multi_select
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to filter...")
        self.search_edit.textChanged.connect(self.filterColumns)
        hlayout.addWidget(self.search_edit)
        layout.addLayout(hlayout)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection if self.multi_select 
                                          else QListWidget.SingleSelection)
        layout.addWidget(self.list_widget)
        self.populateList(self.all_columns)

        btn_layout = QHBoxLayout()
        for text, slot in (("OK", self.accept), ("Cancel", self.reject)):
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.adjustSize()

    def populateList(self, columns):
        self.list_widget.clear()
        for col in columns:
            self.list_widget.addItem(QListWidgetItem(col))

    def filterColumns(self, text):
        text = text.lower().strip()
        filtered = [col for col in self.all_columns if text in col.lower()]
        self.populateList(filtered)

    def getSelectedColumns(self):
        return [item.text() for item in self.list_widget.selectedItems()]

GLOBAL_SAVED_FILTERS = []
class FilterDialog(QDialog):
    def __init__(self, friendly_columns, registry, filter_conditions=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Advanced Filter 🎛️")
        self.setMinimumSize(700, 500)
        self.setSizeGripEnabled(True)

        self.friendly_columns = friendly_columns
        self.registry = registry

        if filter_conditions is not None:
            self.filter_conditions = filter_conditions
        else:
            self.filter_conditions = GLOBAL_SAVED_FILTERS.copy()

        self.filter_groups = []
        self.initUI()

        if self.filter_conditions:
            self.loadFilterConditions(self.filter_conditions)

        self.adjustSizeIfNeeded()

    def accept(self):
        final = self.getFilterConditions()
        self.filter_conditions = final
        global GLOBAL_SAVED_FILTERS
        GLOBAL_SAVED_FILTERS = self.filter_conditions.copy()
        super().accept()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        btn_add_group = QPushButton("➕ Add Filter Group")
        btn_add_group.clicked.connect(self.createNewFilterGroup)
        main_layout.addWidget(btn_add_group)
        self.groups_container = QVBoxLayout()
        main_layout.addLayout(self.groups_container)
        main_layout.addWidget(QLabel("Filter Expression Preview:"))
        self.group_preview = QLineEdit()
        self.group_preview.setReadOnly(True)
        main_layout.addWidget(self.group_preview)
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK ✅")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel ❌")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def loadFilterConditions(self, filter_conditions):
        for i, group_data in enumerate(filter_conditions):
            group_box, toggle_btn, cond_logic_combo, condition_layout, container_widget = self.createNewFilterGroup(return_group_refs=True)
            if cond_logic_combo and "group_logic" in group_data:
                cond_logic_combo.setCurrentText(group_data["group_logic"])
            for j, cond_row in enumerate(group_data["conditions"]):
                self.addConditionRow(condition_layout, row_data=cond_row)

    def createNewFilterGroup(self, return_group_refs=False):
        group_number = len(self.filter_groups) + 1
        group_box = QGroupBox()
        group_box.setStyleSheet("QGroupBox { border: 2px solid #AAAAAA; margin-top:0px; }")
        group_layout = QVBoxLayout(group_box)

        header_layout = QHBoxLayout()
        toggle_btn = QPushButton("🔽")
        toggle_btn.setCheckable(True)
        toggle_btn.setFixedSize(25, 25)
        btn_remove_group = QPushButton("❌")
        btn_remove_group.setFixedSize(30, 30)
        btn_remove_group.setStyleSheet("""
            QPushButton {
                background: none; 
                color: black; 
                font-weight: bold; 
                font-size: 16px; 
                border: none;
            }
            QPushButton:hover {
                background: red;
                color: white;
                border-radius: 4px;
            }
        """)
        btn_remove_group.clicked.connect(lambda: self.removeFilterGroup(group_box))
        header_layout.addWidget(toggle_btn)
        header_layout.addWidget(QLabel(f"Filter Group {group_number}"))
        header_layout.addStretch()
        header_layout.addWidget(btn_remove_group)
        group_layout.addLayout(header_layout)
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_widget.setLayout(container_layout)
        container_widget.setVisible(True)

        if group_number > 1:
            condition_logic_combo = QComboBox()
            condition_logic_combo.addItems(["AND", "OR"])
            container_layout.addWidget(QLabel("Combine This Group With:"))
            container_layout.addWidget(condition_logic_combo)
        else:
            condition_logic_combo = None

        condition_layout = QVBoxLayout()
        container_layout.addLayout(condition_layout)
        btn_add_condition = QPushButton("➕ Add Condition")
        btn_add_condition.clicked.connect(lambda: self.addConditionRow(condition_layout))
        btn_cond_layout = QHBoxLayout()
        btn_cond_layout.addStretch()
        btn_cond_layout.addWidget(btn_add_condition)
        btn_cond_layout.addStretch()
        container_layout.addLayout(btn_cond_layout)
        group_layout.addWidget(container_widget)

        def toggleGroup():
            if container_widget.isVisible():
                container_widget.setVisible(False)
                toggle_btn.setText("🔼")
            else:
                container_widget.setVisible(True)
                toggle_btn.setText("🔽")
            self.adjustSizeIfNeeded()

        toggle_btn.clicked.connect(toggleGroup)

        self.groups_container.addWidget(group_box)

        self.filter_groups.append((group_box, toggle_btn, condition_logic_combo, condition_layout, container_widget))
        container_widget.setVisible(True)
        toggle_btn.setText("🔽")
        self.updateGroupPreview()
        self.adjustSizeIfNeeded()

        if return_group_refs:
            return (group_box, toggle_btn, condition_logic_combo, condition_layout, container_widget)

    def removeFilterGroup(self, group_box):
        for i, (gbox, _, _, _, _) in enumerate(self.filter_groups):
            if gbox == group_box:
                gbox.hide()
                self.groups_container.removeWidget(gbox)
                gbox.deleteLater()
                del self.filter_groups[i]
                break
        self.updateGroupPreview()
        self.adjustSizeIfNeeded()

    def addConditionRow(self, condition_layout, row_data=None):
        row_layout = QHBoxLayout()
        logic_combo = QComboBox()
        logic_combo.addItems(["AND", "OR"])
        if condition_layout.count() == 0:
            logic_combo.hide()
        else:
            logic_combo.show()

        col_combo = QComboBox()
        col_combo.addItems(self.friendly_columns)
        cond_combo = QComboBox()
        cond_combo.addItems([
            "Equals", "Not Equals", "Contains", "Begins With", "Ends With",
            "Like", "Not Like", "ILIKE", "Greater Than", "Less Than",
            "Between", "In List", "Not In List", "Regex",
            "Date Before", "Date After", "Date Between",
            "Null", "Not Null"
        ])

        val_edit = QLineEdit()

        if row_data:
            # Get the stored column name
            stored_col = row_data.get("col", "")
            # If the stored column name exists in the registry, use its friendly name
            friendly_col = self.registry.get(stored_col, stored_col)
            if friendly_col in self.friendly_columns:
                col_combo.setCurrentText(friendly_col)
            else:
                col_combo.setCurrentIndex(0)

            cond_combo.setCurrentText(row_data.get("cond", "Equals"))
            # Only modify behavior for In List / Not In List conditions
            value = row_data.get("value", "")
            if cond_combo.currentText() in ["In List", "Not In List"] and isinstance(value, list):
                value = ",".join(map(str, value))
            val_edit.setText(value)
            if row_data.get("row_logic") and condition_layout.count() > 0:
                logic_combo.setCurrentText(row_data["row_logic"])
                logic_combo.show()

        def updateValueEdit():
            condition = cond_combo.currentText()
            if condition in ["Null", "Not Null"]:
                val_edit.setDisabled(True)
                val_edit.clear()
                val_edit.setPlaceholderText("")
            else:
                val_edit.setDisabled(False)
                if condition in ["Between", "Date Between"]:
                    val_edit.setPlaceholderText("e.g. 10,20 or 2023-01-01,2023-12-31")
                elif condition in ["In List", "Not In List"]:
                    val_edit.setPlaceholderText("comma-separated, e.g. cat,dog,mouse")
                elif condition == "Regex":
                    val_edit.setPlaceholderText("regex pattern, e.g. ^[A-Z]{3}")
                else:
                    val_edit.setPlaceholderText("")

        cond_combo.currentIndexChanged.connect(updateValueEdit)
        updateValueEdit()

        btn_remove_condition = QPushButton("❌")
        btn_remove_condition.setFixedSize(20, 20)
        btn_remove_condition.setStyleSheet("""
            QPushButton {
                background: none; 
                color: black; 
                font-weight: bold; 
                font-size: 16px; 
                border: none;
            }
            QPushButton:hover {
                background: red;
                color: white;
                border-radius: 4px;
            }
        """)

        def removeCondition():
            for i in range(condition_layout.count()):
                layout_item = condition_layout.itemAt(i)
                if layout_item and layout_item.layout() == row_layout:
                    while row_layout.count():
                        witem = row_layout.takeAt(0)
                        w = witem.widget()
                        if w:
                            w.deleteLater()
                    condition_layout.removeItem(layout_item)
                    break
            self.updateGroupPreview()
            self.adjustSizeIfNeeded()

        btn_remove_condition.clicked.connect(removeCondition)

        row_layout.addWidget(logic_combo)
        row_layout.addWidget(col_combo)
        row_layout.addWidget(cond_combo)
        row_layout.addWidget(val_edit)
        row_layout.addWidget(btn_remove_condition)

        condition_layout.addLayout(row_layout)
        self.updateGroupPreview()
        self.adjustSizeIfNeeded()

    def updateGroupPreview(self):
        group_exprs = []
        for i, (_, _, condition_logic_combo, condition_layout, _) in enumerate(self.filter_groups):
            condition_exprs = []
            for j in range(condition_layout.count()):
                row_layout = condition_layout.itemAt(j)
                if not row_layout:
                    continue
                widgets = []
                for k in range(row_layout.count()):
                    item = row_layout.itemAt(k)
                    if item:
                        w = item.widget()
                        widgets.append(w)

                logic_combo = widgets[0]
                col_combo = widgets[1]
                cond_combo = widgets[2]
                val_edit = widgets[3]

                row_logic = ""
                if j > 0:
                    row_logic = logic_combo.currentText().strip()

                col = col_combo.currentText().strip()
                cond = cond_combo.currentText().strip()
                value = val_edit.text().strip()

                if cond in ["Null", "Not Null"]:
                    value = ""

                expr = f"{col} {cond}"
                if value:
                    expr += f" {value}"

                if row_logic:
                    condition_exprs.append(f"{row_logic} ({expr})")
                else:
                    condition_exprs.append(f"({expr})")

            if i == 0:
                group_expr = " ".join(condition_exprs)
            else:
                grp_logic = "AND"
                if condition_logic_combo:
                    grp_logic = condition_logic_combo.currentText().strip()
                group_expr = f"({f' {grp_logic} '.join(condition_exprs)})"

            if group_expr.strip():
                group_exprs.append(group_expr)

        final_expr = " AND ".join(group_exprs) if group_exprs else ""
        self.group_preview.setText(final_expr)

    def getFilterConditions(self):
        results = []
        for i, (_, _, condition_logic_combo, condition_layout, _) in enumerate(self.filter_groups):
            group_data = {
                "group_logic": condition_logic_combo.currentText() if (condition_logic_combo and i > 0) else "",
                "conditions": []
            }
            for j in range(condition_layout.count()):
                row_layout = condition_layout.itemAt(j)
                if not row_layout:
                    continue

                widgets = []
                for k in range(row_layout.count()):
                    item = row_layout.itemAt(k)
                    if item:
                        w = item.widget()
                        widgets.append(w)

                logic_combo = widgets[0]
                col_combo = widgets[1]
                cond_combo = widgets[2]
                val_edit = widgets[3]

                row_logic = ""
                if j > 0:
                    row_logic = logic_combo.currentText()

                # Save the actual column key (if available) or the displayed friendly name
                col = col_combo.currentText().strip()
                # Attempt to reverse-lookup the key from the registry if possible.
                key_for_col = None
                for key, friendly in self.registry.items():
                    if friendly == col:
                        key_for_col = key
                        break
                if key_for_col is None:
                    key_for_col = col

                cond = cond_combo.currentText().strip()
                value = val_edit.text().strip()

                if cond in ["Null", "Not Null"]:
                    value = ""
                elif cond in ["In List", "Not In List"]:
                    value = [item.strip() for item in value.split(",") if item.strip()]

                cond_data = {
                    "row_logic": row_logic,
                    "col": key_for_col,
                    "cond": cond,
                    "value": value
                }
                group_data["conditions"].append(cond_data)

            results.append(group_data)
        return results

    def adjustSizeIfNeeded(self):
        self.adjustSize()
        new_w = max(self.width(), 700)
        new_h = max(self.height(), 500)
        self.resize(new_w, new_h)

class RemoveDuplicatesDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Remove Duplicates ⚠️")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.selected_columns = set()
        self.initUI()
        self.loadPreviousSelections()  # load prior selections, if any

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        # Search field for filtering columns
        layout.addWidget(QLabel("Search Columns:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to filter columns...")
        self.search_edit.textChanged.connect(self.filterColumns)
        layout.addWidget(self.search_edit)

        # Column selection list
        layout.addWidget(QLabel("Select columns to check for duplicates:"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.populateList(self.friendly_columns)
        layout.addWidget(self.list_widget)

        # Selected columns list with remove (X) buttons
        layout.addWidget(QLabel("Columns selected for duplicate removal:"))
        self.selected_columns_layout = QVBoxLayout()
        self.selected_columns_widget = QWidget()
        self.selected_columns_widget.setLayout(self.selected_columns_layout)
        layout.addWidget(self.selected_columns_widget)

        # Dropdown for selecting which duplicate to keep
        layout.addWidget(QLabel("Select duplicate keep option:"))
        self.keep_combo = QComboBox()
        self.keep_combo.addItems(["first", "last", "none"])
        if "keep" in self.init_params:
            idx = self.keep_combo.findText(self.init_params["keep"])
            if idx >= 0:
                self.keep_combo.setCurrentIndex(idx)
        layout.addWidget(self.keep_combo)

        # Connect selection change to update selected list
        self.list_widget.itemSelectionChanged.connect(self.updateSelectedColumnsList)

        # OK and Cancel buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.adjustSize()

    def populateList(self, columns):
        self.list_widget.clear()
        for col in columns:
            self.list_widget.addItem(QListWidgetItem(col))

    def filterColumns(self, text):
        text = text.lower().strip()
        filtered = [col for col in self.friendly_columns if text in col.lower()]
        self.populateList(filtered)

    def updateSelectedColumnsList(self):
        # Clear the selected columns layout first.
        for i in reversed(range(self.selected_columns_layout.count())):
            widget = self.selected_columns_layout.itemAt(i).widget()
            if widget:
                self.selected_columns_layout.removeWidget(widget)
                widget.deleteLater()

        selected = [item.text() for item in self.list_widget.selectedItems()]
        self.selected_columns = set(selected)

        for col in self.selected_columns:
            self.addSelectedColumnWidget(col)

    def addSelectedColumnWidget(self, col_name):
        widget = QWidget()
        hlayout = QHBoxLayout(widget)
        hlayout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(col_name)
        remove_button = QPushButton("X")
        remove_button.setFixedSize(25, 25)
        remove_button.setStyleSheet("background: red; color: white; border-radius: 5px; font-weight: bold;")
        remove_button.clicked.connect(lambda: self.removeColumn(col_name))
        hlayout.addWidget(label)
        hlayout.addWidget(remove_button)
        self.selected_columns_layout.addWidget(widget)

    def removeColumn(self, col_name):
        self.selected_columns.discard(col_name)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() == col_name:
                item.setSelected(False)
                break
        self.updateSelectedColumnsList()

    def loadPreviousSelections(self):
        # If init_params contains previously selected columns (as internal names),
        # convert them to friendly names and preselect them.
        if "columns_to_dedup" in self.init_params:
            preselected_internal = self.init_params["columns_to_dedup"]
            preselected_friendly = []
            for internal in preselected_internal:
                friendly = internal_to_friendly(internal, self.registry)
                if friendly:
                    preselected_friendly.append(friendly)
            # Now, go through list_widget and select the items that are in preselected_friendly.
            for index in range(self.list_widget.count()):
                item = self.list_widget.item(index)
                if item.text() in preselected_friendly:
                    item.setSelected(True)
            # Update our selected_columns set and UI:
            self.selected_columns = set(preselected_friendly)
            self.updateSelectedColumnsList()

    def getParams(self):
        # Convert the friendly names in self.selected_columns to internal IDs.
        selected_ids = [single_friendly_to_internal(f, self.registry) for f in self.selected_columns if single_friendly_to_internal(f, self.registry)]
        return {"columns_to_dedup": selected_ids, "keep": self.keep_combo.currentText()}
        
class MultiColumnRenameDialog(QDialog):
    def __init__(self, all_friendly_columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rename Multiple Columns")
        self.all_friendly_columns = sorted(all_friendly_columns)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.line_search = QLineEdit()
        self.line_search.setPlaceholderText("Type to filter columns...")
        self.line_search.textChanged.connect(lambda text: self.populateList(
            [col for col in self.all_friendly_columns if text.lower() in col.lower()]))
        search_layout.addWidget(self.line_search)
        layout.addLayout(search_layout)

        self.list_columns = QListWidget()
        self.list_columns.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.populateList(self.all_friendly_columns)
        layout.addWidget(self.list_columns)

        btn_add_selected = QPushButton("Click here to rename the selected columns➡️")
        btn_add_selected.clicked.connect(self.addSelectedColumns)
        layout.addWidget(btn_add_selected)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Old Name", "New Name"])
        layout.addWidget(self.table)

        btn_remove = QPushButton("Remove Selected Rows ❌")
        btn_remove.clicked.connect(self.removeSelectedRows)
        layout.addWidget(btn_remove)

        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()

    def populateList(self, columns):
        self.list_columns.clear()
        for col in columns:
            self.list_columns.addItem(QListWidgetItem(col))

    def addSelectedColumns(self):
        for item in self.list_columns.selectedItems():
            old_name = item.text()
            if not self.isAlreadyInTable(old_name):
                self.addTableRow(old_name, old_name)

    def isAlreadyInTable(self, old_name):
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == old_name:
                return True
        return False

    def addTableRow(self, old_name, new_name=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        item_old = QTableWidgetItem(old_name)
        item_old.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.table.setItem(row, 0, item_old)
        self.table.setItem(row, 1, QTableWidgetItem(new_name))

    def removeSelectedRows(self):
        rows = {rng.topRow() for rng in self.table.selectedRanges()}
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)

    def getRenameMappings(self):
        return {self.table.item(row, 0).text().strip():
                (self.table.item(row, 1).text().strip() or self.table.item(row, 0).text().strip())
                for row in range(self.table.rowCount())}

class FlagMissingDialog(QDialog):
    def __init__(self, friendly_columns, registry, existing_mappings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Flag Missing (multiple columns) 🚩")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self._display_list = [(internal_to_friendly(cid, registry), flag)
                              for cid, flag in existing_mappings.items()]
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Column", "New Flag Column"])
        layout.addWidget(self.table)
        for fcol, flagcol in self._display_list:
            self.addRow(fcol, flagcol)
        layout.addLayout(create_add_remove_buttons(self.onAddRow, self.onRemoveRow))
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()

    def addRow(self, friendly_col=None, flagcol=None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        cbo = create_combo_box(self.friendly_columns, editable=True)
        if friendly_col in self.friendly_columns:
            cbo.setCurrentText(friendly_col)
        self.table.setCellWidget(row, 0, cbo)
        self.table.setCellWidget(row, 1, QLineEdit(flagcol or ""))
        
    def onAddRow(self):
        self.addRow()
    def onRemoveRow(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
    def getFlagMapping(self):
        result = {}
        for row in range(self.table.rowCount()):
            cbo = self.table.cellWidget(row, 0)
            le = self.table.cellWidget(row, 1)
            friendly_col = cbo.currentText().strip()
            col_id = single_friendly_to_internal(friendly_col, self.registry)
            flag_name = le.text().strip() or f"{friendly_col}_missing"
            if col_id:
                result[col_id] = flag_name
        return result

class DropColumnsDialog(QDialog):
    def __init__(self, available_columns, registry, preselected_columns=None, parent=None):
        print("DropColumnsDialog __init__ called with registry:", registry)
        super().__init__(parent)
        self.setWindowTitle("Drop Columns")
        self.setMinimumSize(600, 400)
        self.available_columns = available_columns[:]  # friendly names
        self.selected_columns = preselected_columns[:] if preselected_columns else []
        self.registry = registry  # mapping: internal -> friendly names
        self.initUI()
        self._refreshLists()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.addWidget(QLabel("Available Columns:"))
        self.available_list = QListWidget()
        self.available_list.addItems(self.available_columns)
        self.available_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.available_list)
        add_button = QPushButton("Add Selected Columns to Drop")
        add_button.clicked.connect(self.addColumns)
        layout.addWidget(add_button)
        layout.addWidget(QLabel("Columns to Drop:"))
        self.selected_widget = QWidget()
        self.selected_layout = QVBoxLayout(self.selected_widget)
        self.selected_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.selected_widget)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _refreshLists(self):
        self.available_list.clear()
        remaining = [col for col in self.available_columns if col not in self.selected_columns]
        self.available_list.addItems(remaining)
        for i in reversed(range(self.selected_layout.count())):
            widget = self.selected_layout.itemAt(i).widget()
            if widget:
                self.selected_layout.removeWidget(widget)
                widget.deleteLater()
        for col in self.selected_columns:
            self.addSelectedColumnWidget(col)

    def addColumns(self):
        selected_items = self.available_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select at least one column to drop.")
            return
        for item in selected_items:
            col_name = item.text()
            if col_name not in self.selected_columns:
                self.selected_columns.append(col_name)
        self._refreshLists()

    def addSelectedColumnWidget(self, col_name):
        widget = QWidget()
        hlayout = QHBoxLayout(widget)
        hlayout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(col_name)
        remove_button = QPushButton("X")
        remove_button.setFixedSize(20, 20)
        remove_button.clicked.connect(lambda: self.removeColumn(col_name))
        hlayout.addWidget(label)
        hlayout.addWidget(remove_button)
        self.selected_layout.addWidget(widget)

    def removeColumn(self, col_name):
        if col_name in self.selected_columns:
            self.selected_columns.remove(col_name)
        self._refreshLists()

    def getSelectedColumns(self):
        # Instead of converting to internal names here, we return the friendly names.
        # We'll let the drop transformation (apply_transform_drop_columns) convert them using the registry.
        # However, perform conflict checking by comparing friendly names.
        conflicting = []
        parent_state = self.parent().state if self.parent() and hasattr(self.parent(), "state") else {}
        trans_params = parent_state.get("transformation_params", {})
        for trans_name, params in trans_params.items():
            # Check common keys "column" and "columns"
            for key in ["column", "columns"]:
                if key in params:
                    ref = params[key]
                    if isinstance(ref, list):
                        for col in ref:
                            # Convert internal name to friendly using our registry
                            friendly = internal_to_friendly(col, self.registry)
                            if friendly in self.selected_columns:
                                conflicting.append((friendly, trans_name))
                    elif isinstance(ref, str):
                        friendly = internal_to_friendly(ref, self.registry)
                        if friendly in self.selected_columns:
                            conflicting.append((friendly, trans_name))
        if conflicting:
            conflicts = ", ".join([f"{col} in {trans}" for col, trans in conflicting])
            QMessageBox.warning(self, "Drop Conflict",
                f"Cannot drop selected column(s) because they are used in other transformations: {conflicts}")
            return []  # Cancel the drop operation if there is a conflict.
        return self.selected_columns  # Return friendly names

class CaseConversionDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Case Conversion 🔠")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {"columns": {}}  # Ensure persistence
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.addWidget(QLabel("Select Columns for Case Conversion:"))
        self.list_columns = QListWidget()
        self.list_columns.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_columns.addItems(self.friendly_columns)
        layout.addWidget(self.list_columns)

        # Add selected columns to the table
        btn_add_selected = QPushButton("➕ Add Selected Columns")
        btn_add_selected.clicked.connect(self.addSelectedColumns)
        layout.addWidget(btn_add_selected)

        # Table to show selected columns and their respective conversion type
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Column", "Conversion Type"])
        layout.addWidget(self.table)

        # Remove Selected Rows
        btn_remove = QPushButton("❌ Remove Selected Rows")
        btn_remove.clicked.connect(self.removeSelectedRows)
        layout.addWidget(btn_remove)

        # Restore previously selected values
        self.loadPreviousSelections()

        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
    
    def addSelectedColumns(self):
        """Add selected columns to the conversion table."""
        for item in self.list_columns.selectedItems():
            column_name = item.text()
            if not self.isAlreadyInTable(column_name):
                self.addTableRow(column_name, "UPPERCASE")  # Default to UPPERCASE

    def isAlreadyInTable(self, column_name):
        """Check if a column is already in the table."""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == column_name:
                return True
        return False

    def addTableRow(self, column_name, case_type):
        """Add a new row with column name and conversion type dropdown."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Column name (read-only)
        item_col = QTableWidgetItem(column_name)
        item_col.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.table.setItem(row, 0, item_col)

        # Conversion Type Dropdown
        combo_conversion = QComboBox()
        combo_conversion.addItems(["UPPERCASE", "lowercase", "Title Case", "Capitalize"])
        combo_conversion.setCurrentText(case_type)  # Load saved selection if available
        self.table.setCellWidget(row, 1, combo_conversion)

    def removeSelectedRows(self):
        """Remove selected rows from the table."""
        rows_to_remove = {rng.topRow() for rng in self.table.selectedRanges()}
        for row in sorted(rows_to_remove, reverse=True):
            self.table.removeRow(row)

    def loadPreviousSelections(self):
        """Restore previous user selections from saved parameters."""
        for col_name, case_type in self.init_params["columns"].items():
            friendly_name = internal_to_friendly(col_name, self.registry)
            if friendly_name in self.friendly_columns:
                self.addTableRow(friendly_name, case_type.capitalize())

    def getValues(self):
        """Return a dictionary mapping each selected column to its conversion type."""
        column_mapping = {}
        for row in range(self.table.rowCount()):
            col_name = self.table.item(row, 0).text().strip()
            conversion_type = self.table.cellWidget(row, 1).currentText().strip()

            col_id = single_friendly_to_internal(col_name, self.registry)
            if col_id:
                column_mapping[col_id] = conversion_type.lower()  # Store as lowercase for consistency
        return {"columns": column_mapping}

class ReplaceSubstringDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Replace Substring 🔄")
        self.friendly_columns = friendly_columns
        self.registry = registry
        # init_params should be a dict with a key "columns" that maps internal column IDs to settings.
        # For UI, we want to work with friendly names.
        self.init_params = init_params or {"columns": {}}
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        # Column Selection List (friendly names)
        layout.addWidget(QLabel("Select Columns for Replace Substring:"))
        self.list_columns = QListWidget()
        self.list_columns.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_columns.addItems(self.friendly_columns)
        layout.addWidget(self.list_columns)

        # Button to Add Selected Columns
        btn_add_selected = QPushButton("➕ Add Selected Columns")
        btn_add_selected.clicked.connect(self.addSelectedColumns)
        layout.addWidget(btn_add_selected)

        # Table for Column-Specific Replacements
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Column", "Find", "Replace", "Case Sensitive", "Global"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Remove Button
        btn_remove = QPushButton("❌ Remove Selected Rows")
        btn_remove.clicked.connect(self.removeSelectedRows)
        layout.addWidget(btn_remove)

        # Revert Button
        btn_revert = QPushButton("↩️ Revert to Previous Selections")
        btn_revert.clicked.connect(self.loadPreviousSelections)
        layout.addWidget(btn_revert)

        # OK & Cancel Buttons
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK ✅")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel ❌")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.resize(800, 500)
        self.adjustSize()

        # Load any previous selections from init_params.
        self.loadPreviousSelections()

    def addSelectedColumns(self):
        for item in self.list_columns.selectedItems():
            column_name = item.text()
            if not self.isAlreadyInTable(column_name):
                self.addTableRow(column_name)

    def isAlreadyInTable(self, column_name):
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0) and self.table.item(row, 0).text() == column_name:
                return True
        return False

    def addTableRow(self, column_name):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # Column Name (read-only) as friendly name
        item_col = QTableWidgetItem(column_name)
        item_col.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.table.setItem(row, 0, item_col)
        # Find Substring Input
        find_edit = QLineEdit()
        self.table.setCellWidget(row, 1, find_edit)
        # Replace Substring Input
        replace_edit = QLineEdit()
        self.table.setCellWidget(row, 2, replace_edit)
        # Case Sensitive Checkbox
        case_check = QCheckBox()
        case_check.setChecked(True)
        case_check.setStyleSheet("margin-left: 15px;")
        self.table.setCellWidget(row, 3, case_check)
        # Global Replacement Checkbox
        global_check = QCheckBox()
        global_check.setChecked(True)
        global_check.setStyleSheet("margin-left: 15px;")
        self.table.setCellWidget(row, 4, global_check)

    def removeSelectedRows(self):
        rows_to_remove = {rng.topRow() for rng in self.table.selectedRanges()}
        for row in sorted(rows_to_remove, reverse=True):
            self.table.removeRow(row)

    def loadPreviousSelections(self):
        # Clear current table
        self.table.setRowCount(0)
        # init_params["columns"] is assumed to be a dict with internal column IDs as keys.
        # Convert those to friendly names for display.
        for internal, settings in self.init_params.get("columns", {}).items():
            friendly = internal_to_friendly(internal, self.registry)
            if friendly:
                self.addTableRow(friendly)
                row = self.table.rowCount() - 1
                self.table.cellWidget(row, 1).setText(settings.get("old_sub", ""))
                self.table.cellWidget(row, 2).setText(settings.get("new_sub", ""))
                self.table.cellWidget(row, 3).setChecked(settings.get("case_sensitive", True))
                self.table.cellWidget(row, 4).setChecked(settings.get("global", True))

    def getValues(self):
        # Build a dictionary with key "columns" mapping internal column IDs to settings.
        column_settings = {}
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0) is None:
                continue
            friendly_col = self.table.item(row, 0).text().strip()
            # Convert friendly to internal name using the registry
            internal_col = single_friendly_to_internal(friendly_col, self.registry)
            if not internal_col:
                continue
            find_sub = self.table.cellWidget(row, 1).text().strip()
            replace_sub = self.table.cellWidget(row, 2).text().strip()
            case_sensitive = self.table.cellWidget(row, 3).isChecked()
            global_replace = self.table.cellWidget(row, 4).isChecked()
            column_settings[internal_col] = {
                "old_sub": find_sub,
                "new_sub": replace_sub,
                "case_sensitive": case_sensitive,
                "global": global_replace
            }
        return {"columns": column_settings}

class FillMissingDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Fill Missing Values 🩹")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {}
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.addWidget(QLabel("Select Column to Fill Missing Values:"))
        self.col_combo = create_combo_box(self.friendly_columns, editable=True)
        if "column" in self.init_params:
            friendly = internal_to_friendly(self.init_params["column"], self.registry)
            if friendly in self.friendly_columns:
                self.col_combo.setCurrentText(friendly)
        layout.addWidget(self.col_combo)
        
        layout.addWidget(QLabel("Select Fill Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Constant", "Forward Fill", "Backward Fill", "Mean", "Median"])
        if "method" in self.init_params:
            idx = self.method_combo.findText(self.init_params["method"])
            if idx >= 0:
                self.method_combo.setCurrentIndex(idx)
        layout.addWidget(self.method_combo)
        
        self.constant_edit = QLineEdit()
        self.constant_edit.setPlaceholderText("Enter constant value")
        if self.method_combo.currentText() == "Constant" and "constant" in self.init_params:
            self.constant_edit.setText(self.init_params["constant"])
        layout.addWidget(self.constant_edit)
        
        self.method_combo.currentIndexChanged.connect(self.onMethodChanged)
        self.onMethodChanged(self.method_combo.currentIndex())
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()
        
    def onMethodChanged(self, index):
        if self.method_combo.currentText() == "Constant":
            self.constant_edit.setEnabled(True)
        else:
            self.constant_edit.setEnabled(False)
            self.constant_edit.clear()
            
    def getValues(self):
        values = {}
        friendly = self.col_combo.currentText()
        col_id = single_friendly_to_internal(friendly, self.registry)
        if col_id:
            values["column"] = col_id
        values["method"] = self.method_combo.currentText()
        if values["method"] == "Constant":
            values["constant"] = self.constant_edit.text().strip()
        return values

class TrimDialog(QDialog):
    def __init__(self, friendly_columns, registry, init_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Trim Transformation ✂️")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.init_params = init_params or {"columns": {}}
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        # **Column Selection**
        layout.addWidget(QLabel("Select Columns:"))
        self.list_columns = QListWidget()
        self.list_columns.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_columns.addItems(self.friendly_columns)
        layout.addWidget(self.list_columns)

        # **Button to Add Selected Columns**
        btn_add_selected = QPushButton("➕ Add Selected Columns")
        btn_add_selected.clicked.connect(self.addSelectedColumns)
        layout.addWidget(btn_add_selected)

        # **Table for Column-Specific Operations**
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Column", "Operations", "Custom Characters"])

        # **Resize Columns to Fit Window Dynamically**
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.table.setColumnWidth(0, 200)  # Column name
        self.table.setColumnWidth(1, 300)  # Operations (slightly larger)
        self.table.setColumnWidth(2, 250)  # Custom Characters
        self.table.horizontalHeader().setStretchLastSection(True)  # Ensures full width usage

        layout.addWidget(self.table)

        # **Remove Button**
        btn_remove = QPushButton("❌ Remove Selected Rows")
        btn_remove.clicked.connect(self.removeSelectedRows)
        layout.addWidget(btn_remove)

        # **OK & Cancel Buttons**
        btn_ok = QPushButton("OK ✅")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel ❌")
        btn_cancel.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.resize(800, 500)  # **Set default size of dialog larger**
        self.adjustSize()
        self.loadPreviousSelections()

    def addSelectedColumns(self):
        """Add selected columns to the table with multiple operation support."""
        for item in self.list_columns.selectedItems():
            column_name = item.text()
            if not self.isAlreadyInTable(column_name):
                self.addTableRow(column_name)

    def isAlreadyInTable(self, column_name):
        """Check if a column is already in the table."""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == column_name:
                return True
        return False

    def addTableRow(self, column_name):
        """Add a row with a checkable operations dropdown for each column."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Column Name (Read-Only)
        item_col = QTableWidgetItem(column_name)
        item_col.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.table.setItem(row, 0, item_col)

        # **Checkable Operations Dropdown**
        available_operations = [
            "Trim Spaces", "Remove Extra Spaces", "Remove Custom Characters",
            "Remove Special Characters", "Remove Non-UTF Characters"
        ]
        operations_combo = CheckableComboBox(available_operations, self)
        self.table.setCellWidget(row, 1, operations_combo)

        # **Custom Character Input (Initially Disabled)**
        custom_char_edit = QLineEdit()
        custom_char_edit.setPlaceholderText("Enter custom chars (if required)")
        custom_char_edit.setEnabled(False)
        self.table.setCellWidget(row, 2, custom_char_edit)

        # Enable Custom Char Input when "Remove Custom Characters" is selected
        def toggleCustomCharInput():
            selected_ops = operations_combo.getSelectedItems()
            custom_char_edit.setEnabled("Remove Custom Characters" in selected_ops)

        operations_combo.list_widget.itemChanged.connect(toggleCustomCharInput)

    def removeSelectedRows(self):
        """Remove selected rows from the table."""
        rows_to_remove = {rng.topRow() for rng in self.table.selectedRanges()}
        for row in sorted(rows_to_remove, reverse=True):
            self.table.removeRow(row)

    def loadPreviousSelections(self):
        """Restore previously saved settings."""
        for col, settings in self.init_params.get("columns", {}).items():
            self.addTableRow(col)
            row = self.table.rowCount() - 1
            operations_combo = self.table.cellWidget(row, 1)
            operations_combo.setSelectedItems(settings.get("operations", []))

            custom_char_edit = self.table.cellWidget(row, 2)
            if "custom_char" in settings:
                custom_char_edit.setText(settings["custom_char"])

    def getValues(self):
        """Retrieve selected columns and their transformation settings."""
        column_settings = {}
        for row in range(self.table.rowCount()):
            col_name = self.table.item(row, 0).text().strip()
            operations_combo = self.table.cellWidget(row, 1)
            selected_operations = operations_combo.getSelectedItems()
            custom_char_edit = self.table.cellWidget(row, 2)

            column_settings[col_name] = {
                "operations": selected_operations,
                "custom_char": custom_char_edit.text().strip() or None
            }
        return {"columns": column_settings}

class CheckableComboBox(QComboBox):
    """Custom ComboBox that allows multiple checkable selections."""
    
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)  
        self.setStyleSheet("QComboBox { min-width: 200px; }")

        self.list_widget = QListWidget(self)
        self.setModel(self.list_widget.model())
        self.setView(self.list_widget)

        # Add checkable items
        for item_text in items:
            item = QListWidgetItem(item_text, self.list_widget)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)  
            item.setCheckState(Qt.CheckState.Unchecked)  

        self.list_widget.itemClicked.connect(self.toggleCheckState)

        self.view().pressed.connect(self.onItemPressed)

    def onItemPressed(self, index):
        """Manages toggling of check state on mouse press."""
        item = self.list_widget.item(index.row())
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)
        self.updateDisplayText()

    def toggleCheckState(self, item):
        """Toggle the check state of an item when clicked."""
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)
        self.updateDisplayText()

    def updateDisplayText(self):
        """Update display text with selected operations."""
        selected_items = [item.text() for item in self.getCheckedItems()]
        self.lineEdit().setText(", ".join(selected_items) if selected_items else "Select Operations")

    def getCheckedItems(self):
        """Return checked items as a list."""
        return [self.list_widget.item(i) for i in range(self.list_widget.count()) if self.list_widget.item(i).checkState() == Qt.CheckState.Checked]

    def getSelectedItems(self):
        """Return selected items as a list of strings."""
        return [item.text() for item in self.getCheckedItems()]

    def setSelectedItems(self, selected_items):
        """Restore previously selected operations."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() in selected_items:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
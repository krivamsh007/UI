# -----------------------------------------------------------------------------
# Copyright (c) [2025] [Vamshi Krishna Nagabhyru]
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QLayout
from ui_helpers import add_ok_cancel_buttons, create_combo_box, single_friendly_to_internal, internal_to_friendly
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidget, QListWidgetItem

class SplitColumnDialog(QDialog):
    def __init__(self, friendly_columns, registry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Split Column ✂️")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SetMinimumSize)
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
    def __init__(self, friendly_columns, registry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Concatenate Columns 🔗")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        layout.addWidget(QLabel("Select Columns to Concatenate:"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        for col in self.friendly_columns:
            self.list_widget.addItem(QListWidgetItem(col))
        layout.addWidget(self.list_widget)
        
        layout.addWidget(QLabel("Enter Delimiter:"))
        self.delim_edit = QLineEdit()
        self.delim_edit.setText(" ")
        layout.addWidget(self.delim_edit)
        
        layout.addWidget(QLabel("Enter New Column Name:"))
        self.newcol_edit = QLineEdit()
        layout.addWidget(self.newcol_edit)
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()

    def getValues(self):
        values = {}
        selected = [item.text() for item in self.list_widget.selectedItems()]
        cols = [single_friendly_to_internal(f, self.registry) for f in selected]
        values["columns"] = [col for col in cols if col]
        values["delimiter"] = self.delim_edit.text().strip()
        values["new_column"] = self.newcol_edit.text().strip()
        return values

class PivotDataDialog(QDialog):
    def __init__(self, friendly_columns, registry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Pivot Data 📊")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        layout.addWidget(QLabel("Enter Index Columns (comma separated):"))
        self.index_edit = QLineEdit()
        layout.addWidget(self.index_edit)
        
        layout.addWidget(QLabel("Enter Pivot Columns (comma separated):"))
        self.columns_edit = QLineEdit()
        layout.addWidget(self.columns_edit)
        
        layout.addWidget(QLabel("Select Value Column:"))
        self.value_combo = create_combo_box(self.friendly_columns, editable=True)
        layout.addWidget(self.value_combo)
        
        layout.addWidget(QLabel("Aggregation Function:"))
        self.agg_edit = QLineEdit()
        self.agg_edit.setText("sum")
        layout.addWidget(self.agg_edit)
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()

    def getValues(self):
        values = {}
        index_cols = [single_friendly_to_internal(x.strip(), self.registry) for x in self.index_edit.text().split(",") if x.strip()]
        columns_cols = [single_friendly_to_internal(x.strip(), self.registry) for x in self.columns_edit.text().split(",") if x.strip()]
        values["index"] = index_cols
        values["columns"] = columns_cols
        friendly_val = self.value_combo.currentText()
        values["values"] = single_friendly_to_internal(friendly_val, self.registry)
        values["aggfunc"] = self.agg_edit.text().strip()
        return values

class UnpivotDataDialog(QDialog):
    def __init__(self, friendly_columns, registry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Unpivot Data 🔄")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        layout.addWidget(QLabel("Enter ID Variables (comma separated):"))
        self.id_vars_edit = QLineEdit()
        layout.addWidget(self.id_vars_edit)
        
        layout.addWidget(QLabel("Enter Value Variables (comma separated):"))
        self.value_vars_edit = QLineEdit()
        layout.addWidget(self.value_vars_edit)
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()

    def getValues(self):
        values = {}
        id_vars = [single_friendly_to_internal(x.strip(), self.registry) for x in self.id_vars_edit.text().split(",") if x.strip()]
        value_vars = [single_friendly_to_internal(x.strip(), self.registry) for x in self.value_vars_edit.text().split(",") if x.strip()]
        values["id_vars"] = id_vars
        values["value_vars"] = value_vars
        return values

class TransposeDataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transpose Data ↔️")
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        layout.addWidget(QLabel("This operation will transpose the entire dataset. Continue?"))
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()

    def getValues(self):
        return {}

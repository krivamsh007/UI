# -----------------------------------------------------------------------------
# Copyright (c) [2025] [Vamshi Krishna Nagabhyru]
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
from PyQt6.QtWidgets import QAbstractItemView,QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QButtonGroup, QRadioButton, QLayout
from ui_helpers import add_ok_cancel_buttons, create_combo_box, single_friendly_to_internal, internal_to_friendly

class GroupAggregateDialog(QDialog):
    def __init__(self, friendly_columns, registry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Group & Aggregate 📈")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.initUI()
    
    def initUI(self):
        from PyQt6.QtWidgets import QListWidget
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.addWidget(QLabel("Select Group Columns:"))
        self.group_list = QListWidget()
        self.group_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for col in self.friendly_columns:
            self.group_list.addItem(QListWidgetItem(col))
        layout.addWidget(self.group_list)
        
        layout.addWidget(QLabel("Select Aggregate Column:"))
        self.agg_combo = create_combo_box(self.friendly_columns, editable=True)
        layout.addWidget(self.agg_combo)
        
        layout.addWidget(QLabel("Aggregation Function:"))
        self.agg_edit = QLineEdit()
        self.agg_edit.setText("sum")
        layout.addWidget(self.agg_edit)
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()

    def getValues(self):
        values = {}
        selected = [item.text() for item in self.group_list.selectedItems()]
        values["group_columns"] = [single_friendly_to_internal(x, self.registry) for x in selected]
        friendly = self.agg_combo.currentText()
        values["agg_column"] = single_friendly_to_internal(friendly, self.registry)
        values["agg_func"] = self.agg_edit.text().strip()
        return values

class SortDataDialog(QDialog):
    def __init__(self, friendly_columns, registry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Sort Data 🔃")
        self.friendly_columns = friendly_columns
        self.registry = registry
        self.initUI()
    
    def initUI(self):
        from PyQt6.QtWidgets import QButtonGroup, QRadioButton, QListWidget, QListWidgetItem
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.addWidget(QLabel("Select Columns to Sort:"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for col in self.friendly_columns:
            self.list_widget.addItem(QListWidgetItem(col))
        layout.addWidget(self.list_widget)
        
        layout.addWidget(QLabel("Select Sorting Order:"))
        self.order_group = QButtonGroup(self)
        order_layout = QHBoxLayout()
        self.radio_asc = QRadioButton("Ascending")
        self.radio_desc = QRadioButton("Descending")
        self.radio_asc.setChecked(True)
        self.order_group.addButton(self.radio_asc)
        self.order_group.addButton(self.radio_desc)
        order_layout.addWidget(self.radio_asc)
        order_layout.addWidget(self.radio_desc)
        layout.addLayout(order_layout)
        
        add_ok_cancel_buttons(self, layout)
        self.setLayout(layout)
        self.adjustSize()

    def getValues(self):
        values = {}
        selected = [item.text() for item in self.list_widget.selectedItems()]
        values["columns"] = [single_friendly_to_internal(x, self.registry) for x in selected]
        values["ascending"] = self.radio_asc.isChecked()
        return values

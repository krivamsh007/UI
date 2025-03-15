# -----------------------------------------------------------------------------
# Copyright (c) [2025] [Vamshi Krishna Nagabhyru]
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
import sys
import pandas as pd
from PyQt6.QtWidgets import QPushButton, QComboBox, QGroupBox, QHBoxLayout, QVBoxLayout, QLayout
from PyQt6.QtCore import QAbstractTableModel, QVariant, Qt
from PyQt6.QtCore import Qt, QVariant
from PyQt6.QtWidgets import QCompleter

def add_ok_cancel_buttons(dialog, layout):
    btn_layout = QHBoxLayout()
    for text, slot in (("OK ✅", dialog.accept), ("Cancel ❎", dialog.reject)):
        btn = QPushButton(text)
        btn.clicked.connect(slot)
        btn_layout.addWidget(btn)
    layout.addLayout(btn_layout)

def create_add_remove_buttons(add_callback, remove_callback):
    btn_layout = QHBoxLayout()
    for text, slot in (("Add Row ➕", add_callback), ("Remove Selected ❌", remove_callback)):
        btn = QPushButton(text)
        btn.clicked.connect(slot)
        btn_layout.addWidget(btn)
    return btn_layout

def create_combo_box(items, editable=False):
    combo = QComboBox()
    combo.setEditable(editable)
    combo.addItems(items)
    if editable:
        combo.setCompleter(QCompleter(items))
    return combo

def create_config_group(title, bg_color, border_color):
    group = QGroupBox(title)
    group.setStyleSheet(
        f"QGroupBox {{ background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 5px; margin-top: 10px; padding: 5px; }}"
        "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }"
    )
    return group

# PandasModel for DataFrame display
class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df

    def rowCount(self, parent=None):
        return len(self._df.index)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])
        return QVariant()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return (self._df.columns[section] if orientation == Qt.Horizontal 
                    else str(self._df.index[section]))
        return QVariant()

    def setDataFrame(self, df):
        self.beginResetModel()
        self._df = df.copy()
        self.endResetModel()

    def getDataFrame(self):
        return self._df.copy()

# Column Registry Helper Functions
def friendly_to_internal(col_names, registry):
    return [k for col in col_names for k, v in registry.items() if v == col]

def internal_to_friendly(internal_id, registry):
    return registry.get(internal_id, internal_id)

def single_friendly_to_internal(name, registry):
    for k, v in registry.items():
        if v == name:
            return k
    return None

def rename_friendly(internal_id, new_friendly_name, registry):
    if internal_id in registry:
        registry[internal_id] = new_friendly_name

# -----------------------------------------------------------------------------
# Copyright (c) [2025] [Vamshi Krishna Nagabhyru]
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
import sys, os, logging, json, re
import pandas as pd
from advanced_excel_transformations import *
from advanced_transformations import *
from transformations import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QPushButton, QLabel, QTabWidget, QComboBox, QSpinBox, QLineEdit, QTableView,
    QAbstractItemView, QGroupBox, QFileDialog, QDialog, QMessageBox, QSplitter,
    QHeaderView, QProgressDialog, QStatusBar, QStackedWidget, QRadioButton,
    QPlainTextEdit, QFormLayout, QListWidget, QListWidgetItem, QLayout, QInputDialog,QDialogButtonBox
)
from lineage import show_enhanced_lineage_in_ui
from ui_helpers import *
from ui_dialogs_data_cleaning import *
from ui_dialogs_data_transformation import *
from ui_dialogs_data_reshaping import *
from ui_dialogs_agg_sort import SortDataDialog

class ExcelAdvancedConfigDialog(QDialog):
    def __init__(self, current_config=None, columns=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Options (Excel-like) Transformations")
        self.resize(650, 400)
        self.setMinimumSize(650, 400)
        self.current_config = current_config or {}
        self.columns = columns or []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Select Advanced Transformation Category:"))
        self.type_combo = QComboBox()
        self.advanced_options = [
            "Lookup & Conditional",
            "Date & Time Functions",
            "Enhanced Text Operations",
            "Financial Calculations",
            "Data Validation",
            "SQL Query",
        ]
        self.type_combo.addItems(self.advanced_options)
        form_layout.addRow("Category:", self.type_combo)
        layout.addLayout(form_layout)
        self.stack = QStackedWidget()
        self.page_lookup_conditional = self._createLookupConditionalPage()
        self.page_datetime = self._createDateTimePage()
        self.page_text = self._createEnhancedTextPage()
        self.page_financial = self._createFinancialPage()
        self.page_dataval = self._createDataValidationPage()
        self.page_sql = self._createSQLPage()
        self.stack.addWidget(self.page_lookup_conditional)
        self.stack.addWidget(self.page_datetime)
        self.stack.addWidget(self.page_text)
        self.stack.addWidget(self.page_financial)
        self.stack.addWidget(self.page_dataval)
        self.stack.addWidget(self.page_sql)
        layout.addWidget(self.stack)
        self.type_combo.currentIndexChanged.connect(self.stack.setCurrentIndex)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Apply")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _createLookupConditionalPage(self):
        page = QWidget()
        layout = QFormLayout(page)
        self.lookup_table_file = QLineEdit()
        browse_btn = QPushButton("Browse..")
        browse_btn.clicked.connect(self._browseLookupFile)
        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.lookup_table_file)
        browse_layout.addWidget(browse_btn)
        layout.addRow("Lookup Table File:", browse_layout)
        self.lookup_src_col = QComboBox()
        self.lookup_src_col.addItems(self.columns)
        layout.addRow("Source Column for Lookup:", self.lookup_src_col)
        self.lookup_key = QLineEdit()
        layout.addRow("Lookup Key:", self.lookup_key)
        self.lookup_value = QLineEdit()
        layout.addRow("Lookup Value Column:", self.lookup_value)
        self.cond_col = QComboBox()
        self.cond_col.addItems(self.columns)
        layout.addRow("Conditional Source Column:", self.cond_col)
        self.cond_operator = QComboBox()
        self.cond_operator.addItems([">", "<", "==", ">=", "<=", "!="])
        layout.addRow("Conditional Operator:", self.cond_operator)
        self.cond_value = QLineEdit()
        layout.addRow("Conditional Value:", self.cond_value)
        self.cond_true = QLineEdit()
        layout.addRow("True Result:", self.cond_true)
        self.cond_false = QLineEdit()
        layout.addRow("False Result:", self.cond_false)
        self.cond_output = QLineEdit()
        layout.addRow("Output Column:", self.cond_output)
        return page

    def _browseLookupFile(self):
        dlg = QFileDialog(self, "Select Lookup File")
        dlg.setNameFilters(["CSV Files (*.csv)", "Excel Files (*.xlsx *.xls)", "All Files (*.*)"])
        if dlg.exec():
            path = dlg.selectedFiles()[0]
            self.lookup_table_file.setText(path)

    def _createDateTimePage(self):
        page = QWidget()
        layout = QFormLayout(page)
        self.date_col = QComboBox()
        self.date_col.addItems(self.columns)
        layout.addRow("Date Column:", self.date_col)
        self.ref_date = QLineEdit()
        layout.addRow("Reference Date (YYYY-MM-DD):", self.ref_date)
        self.date_unit = QComboBox()
        self.date_unit.addItems(["days", "months", "years"])
        layout.addRow("Unit for Date Diff:", self.date_unit)
        self.eomonth_col = QComboBox()
        self.eomonth_col.addItems(self.columns)
        layout.addRow("EOMONTH Date Column:", self.eomonth_col)
        self.eomonth_offset = QSpinBox()
        self.eomonth_offset.setRange(-120, 120)
        layout.addRow("Month Offset:", self.eomonth_offset)
        return page

    def _createEnhancedTextPage(self):
        page = QWidget()
        layout = QFormLayout(page)
        self.text_replace_col = QComboBox()
        self.text_replace_col.addItems(self.columns)
        layout.addRow("Text Replace Column:", self.text_replace_col)
        self.text_search = QLineEdit()
        layout.addRow("Search Text:", self.text_search)
        self.text_replacement = QLineEdit()
        layout.addRow("Replacement Text:", self.text_replacement)
        self.textjoin_cols = QLineEdit()
        layout.addRow("TEXTJOIN - columns (comma separated):", self.textjoin_cols)
        self.textjoin_delim = QLineEdit()
        layout.addRow("TEXTJOIN - delimiter:", self.textjoin_delim)
        return page

    def _createFinancialPage(self):
        page = QWidget()
        layout = QFormLayout(page)
        self.fc_function = QComboBox()
        self.fc_function.addItems(["NPV", "IRR", "PMT"])
        layout.addRow("Function:", self.fc_function)
        self.fc_col = QComboBox()
        self.fc_col.addItems(self.columns)
        layout.addRow("Cashflow Column:", self.fc_col)
        self.fc_discount_rate = QLineEdit()
        layout.addRow("Discount Rate (for NPV):", self.fc_discount_rate)
        self.fc_nper = QLineEdit()
        layout.addRow("Number of Periods (for PMT):", self.fc_nper)
        self.fc_pv = QLineEdit()
        layout.addRow("Present Value (for PMT):", self.fc_pv)
        return page

    def _createDataValidationPage(self):
        page = QWidget()
        layout = QFormLayout(page)
        self.dv_col = QComboBox()
        self.dv_col.addItems(self.columns)
        layout.addRow("Validation Column:", self.dv_col)
        self.dv_rule = QComboBox()
        self.dv_rule.addItems(["ISNUMBER", "ISBLANK"])
        layout.addRow("Validation Rule:", self.dv_rule)
        return page

    def _createSQLPage(self):
        page = QWidget()
        layout = QFormLayout(page)
        from PyQt6.QtWidgets import QPlainTextEdit
        self.sql_query = QPlainTextEdit()
        layout.addRow("SQL Query:", self.sql_query)
        return page

    def getValues(self):
        adv_config = {}
        idx = self.type_combo.currentIndex()
        chosen = self.advanced_options[idx]
        def map_column(col):
            return self.columns.get(col, col)  # Use internal name if available
        if chosen == "Lookup & Conditional":
            adv_config["lookup_table_file"] = self.lookup_table_file.text().strip()
            adv_config["lookup_source_col"] = self.lookup_src_col.currentText().strip()
            adv_config["lookup_key"] = self.lookup_key.text().strip()
            adv_config["lookup_value"] = self.lookup_value.text().strip()
            adv_config["cond_col"] = self.cond_col.currentText().strip()
            adv_config["cond_operator"] = self.cond_operator.currentText().strip()
            adv_config["cond_value"] = self.cond_value.text().strip()
            adv_config["cond_true"] = self.cond_true.text().strip()
            adv_config["cond_false"] = self.cond_false.text().strip()
            adv_config["cond_output"] = self.cond_output.text().strip()
        elif chosen == "Date & Time Functions":
            adv_config["date_col"] = self.date_col.currentText().strip()
            adv_config["reference_date"] = self.ref_date.text().strip()
            adv_config["unit"] = self.date_unit.currentText().strip()
            adv_config["eomonth_col"] = self.eomonth_col.currentText().strip()
            adv_config["eomonth_offset"] = self.eomonth_offset.value()
        elif chosen == "Enhanced Text Operations":
            adv_config["text_replace_col"] = self.text_replace_col.currentText().strip()
            adv_config["text_search"] = self.text_search.text().strip()
            adv_config["text_replacement"] = self.text_replacement.text().strip()
            adv_config["textjoin_cols"] = self.textjoin_cols.text().strip()
            adv_config["textjoin_delim"] = self.textjoin_delim.text().strip()
        elif chosen == "Financial Calculations":
            adv_config["fc_function"] = self.fc_function.currentText().strip()
            adv_config["fc_col"] = self.fc_col.currentText().strip()
            adv_config["fc_rate"] = self.fc_discount_rate.text().strip()
            adv_config["fc_nper"] = self.fc_nper.text().strip()
            adv_config["fc_pv"] = self.fc_pv.text().strip()
        elif chosen == "Data Validation":
            adv_config["dv_col"] = self.dv_col.currentText().strip()
            adv_config["dv_rule"] = self.dv_rule.currentText().strip()
        elif chosen == "SQL Query":
            adv_config["sql_query"] = self.sql_query.toPlainText()
        return adv_config

# -------------------------- JoinDataframesDialog --------------------------
class JoinDataframesDialog(QDialog):
    def __init__(self, base_columns, column_registry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Join Dataframes")
        self.resize(400, 300)
        self.setMinimumSize(400, 300)
        self.base_columns = base_columns
        self.column_registry = column_registry
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.file_line_edit = QLineEdit()
        browse_btn = QPushButton("Browse..")
        browse_btn.clicked.connect(self.browseFile)
        flayout = QHBoxLayout()
        flayout.addWidget(self.file_line_edit)
        flayout.addWidget(browse_btn)
        form_layout.addRow("Second DF File:", flayout)
        self.join_type_combo = QComboBox()
        self.join_type_combo.addItems(["inner", "left", "right", "outer"])
        form_layout.addRow("Join Type:", self.join_type_combo)
        self.base_key_combo = QComboBox()
        self.base_key_combo.addItems(self.base_columns)
        form_layout.addRow("Base DF Key:", self.base_key_combo)
        self.second_key_combo = QComboBox()
        self.second_key_combo.setEnabled(False)
        form_layout.addRow("Second DF Key:", self.second_key_combo)
        layout.addLayout(form_layout)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def browseFile(self):
        dlg = QFileDialog(self, "Select Second DF file")
        dlg.setNameFilters(["CSV Files (*.csv)", "Excel Files (*.xlsx *.xls)", "All Files (*.*)"])
        if dlg.exec():
            path = dlg.selectedFiles()[0]
            self.file_line_edit.setText(path)
            try:
                _, ext = os.path.splitext(path)
                ext = ext.lower()
                if ext in [".csv", ".txt"]:
                    df = pd.read_csv(path, nrows=1)
                elif ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(path, nrows=1)
                else:
                    df = pd.read_csv(path, nrows=1)
                self.second_key_combo.clear()
                self.second_key_combo.addItems(df.columns.tolist())
                self.second_key_combo.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load columns: {e}")
                self.second_key_combo.clear()
                self.second_key_combo.setEnabled(False)

    def getValues(self):
        return {
            "file_path": self.file_line_edit.text().strip(),
            "join_type": self.join_type_combo.currentText(),
            "base_key": self.base_key_combo.currentText().strip(),
            "other_key": self.second_key_combo.currentText().strip(),
        }

# -------------------------- UnionDataframesDialog --------------------------
class UnionDataframesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Union Dataframes")
        self.resize(600, 200)
        self.setMinimumSize(600, 200)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.file_line_edit = QLineEdit()
        browse_btn = QPushButton("Browse..")
        browse_btn.clicked.connect(self.browseFile)
        flayout = QHBoxLayout()
        flayout.addWidget(self.file_line_edit)
        flayout.addWidget(browse_btn)
        form_layout.addRow("Second DF File:", flayout)
        self.union_type_combo = QComboBox()
        self.union_type_combo.addItems(["Union Distinct", "Union All"])
        form_layout.addRow("Union Type:", self.union_type_combo)
        layout.addLayout(form_layout)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def browseFile(self):
        dlg = QFileDialog(self, "Select Second DF file")
        dlg.setNameFilters(["CSV Files (*.csv)", "Excel Files (*.xlsx *.xls)", "All Files (*.*)"])
        if dlg.exec():
            path = dlg.selectedFiles()[0]
            self.file_line_edit.setText(path)

    def getValues(self):
        do_union_all = True if self.union_type_combo.currentText() == "Union All" else False
        return {
            "file_path": self.file_line_edit.text().strip(),
            "union_all": do_union_all,
        }
class DataTransformerTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Transformer Tool")
        self.state = {
            "file_path": None,
            "file_ext": None,
            "original_df": None,
            "df": None,
            "header_row": 0,
            "filter_conditions": [],
            "transformation_params": {},
            "advanced_excel_config": {},
            "loaded_config": None,
            "transformation_summary": None,
            "pipeline_steps": []
        }
        self.pipeline_loaded = False
        self.master_registry = {}
        self.column_registry = {}
        self.friendly_columns = []
        self.lineage_network = None
        self.initUI()

    def addPipelineStep(self, trans_name, parameters):
        self.state["pipeline_steps"] = [step for step in self.state["pipeline_steps"] if step["transformation"] != trans_name]
        order = len(self.state["pipeline_steps"]) + 1
        self.state["pipeline_steps"].append({"order": order, "transformation": trans_name, "parameters": parameters})

    def initUI(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        self.setCentralWidget(main_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_container = QWidget()
        self.left_layout = QVBoxLayout(left_container)
        left_scroll.setWidget(left_container)
        right_container = QWidget()
        self.right_layout = QVBoxLayout(right_container)
        splitter.addWidget(left_scroll)
        splitter.addWidget(right_container)
        splitter.setSizes([600, 900])
        main_layout.addWidget(splitter)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(40)
        bottom_bar.setStyleSheet("background-color: #333; color: white;")
        b_layout = QHBoxLayout(bottom_bar)
        b_layout.setContentsMargins(10, 5, 10, 5)
        footer_label = QLabel("Powered by ED&A - All transformations in one place!")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b_layout.addWidget(footer_label)
        main_layout.addWidget(bottom_bar)
        self.buildLeftPanel()
        self.buildRightPanel()
        self.showMaximized()

    def showDialog(self, dlg):
        dlg.setMinimumSize(600, 400)
        return dlg.exec()

    def buildLeftPanel(self):
        file_group = create_config_group("Upload Data File", "#D6EAF8", "#2980B9")
        fg_layout = QVBoxLayout(file_group)
        upload_btn = QPushButton("Upload File")
        upload_btn.setToolTip("Upload a data file in CSV, TXT, Excel, Parquet, JSON, or XML format.")
        upload_btn.clicked.connect(self.loadDataFile)
        fg_layout.addWidget(upload_btn)
        header_group = create_config_group("Header Selection", "#D5F5E3", "#27AE60")
        hg_layout = QHBoxLayout(header_group)
        hg_layout.addWidget(QLabel("Header Row:"))
        self.spin_header = QSpinBox()
        self.spin_header.setRange(0, 50)
        self.spin_header.setToolTip("Select the row number to use as the header (0 for no header).")
        hg_layout.addWidget(self.spin_header)
        set_header_btn = QPushButton("Set Header")
        set_header_btn.setToolTip("Set the selected row as the header.")
        set_header_btn.clicked.connect(self.onSetHeaderClicked)
        hg_layout.addWidget(set_header_btn)
        revert_group = create_config_group("Revert Transformations", "#FCF3CF", "#F1C40F")
        rg_layout = QVBoxLayout(revert_group)
        revert_btn = QPushButton("Revert All")
        revert_btn.setToolTip("Revert all transformations and return to the original dataset.")
        revert_btn.clicked.connect(self.revertTransformations)
        rg_layout.addWidget(revert_btn)
        pipeline_group = create_config_group("Pipeline Management", "#E8DAEF", "#8E44AD")
        pg_layout = QVBoxLayout(pipeline_group)
        save_p_btn = QPushButton("Save Pipeline")
        save_p_btn.setToolTip("Save the current transformation pipeline to a file.")
        save_p_btn.clicked.connect(self.savePipeline)
        load_p_btn = QPushButton("Load Pipeline")
        load_p_btn.setToolTip("Load a transformation pipeline from a file.")
        load_p_btn.clicked.connect(self.loadPipeline)
        pg_layout.addWidget(save_p_btn)
        pg_layout.addWidget(load_p_btn)
        self.left_layout.addWidget(file_group)
        self.left_layout.addWidget(header_group)
        self.left_layout.addWidget(revert_group)
        self.left_layout.addWidget(pipeline_group)
        self.tabs = QTabWidget()
        cleaning_tab = QWidget()
        transform_tab = QWidget()
        excel_tab = QWidget()    # Excel Functions tab
        reshape_tab = QWidget()
        adv_trans_tab = QWidget()
        adv_ops_tab = QWidget()
        self.tabs.addTab(cleaning_tab, "Data Cleaning 🧹")
        self.tabs.addTab(transform_tab, "Data Transformation ⚙️")
        self.tabs.addTab(excel_tab, "Excel Functions 📊")
        self.tabs.addTab(reshape_tab, "Data Reshaping 🔀")
        self.tabs.addTab(adv_trans_tab, "Advanced Transformations 🔀")

        self.buildCleaningTab(cleaning_tab)
        self.buildTransformationTab(transform_tab)
        self.buildExcelFunctionsTab(excel_tab)
        self.buildReshapingTab(reshape_tab)
        self.buildAdvancedTransTab(adv_trans_tab)
        self.left_layout.addWidget(self.tabs)
        self.left_layout.addStretch()

    def buildCleaningTab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        mapping = [
            ("Filter Rows 🔎", self.configureFilters),
            ("Remove Duplicates 🗑️", self.configureRemoveDuplicates),
            ("Drop Columns ✂️", self.configureDropColumns),
            ("Rename Columns 📝", self.configureRenameColumns),
            ("Flag Missing Values 🚩", self.configureFlagMissing),
            ("Trim Spaces ✂️", self.configureTrim),
            ("Replace Substring 🔀", self.configureReplaceSubstring),
        ]
        for title, slot in mapping:
            gbox = QGroupBox(title)
            vb = QVBoxLayout(gbox)
            btn = QPushButton(f"Configure {title}")
            btn.clicked.connect(slot)
            vb.addWidget(btn)
            layout.addWidget(gbox)
        layout.addStretch()

    def buildTransformationTab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        mapping = [
            ("Detect Outliers 🔍", self.configureDetectOutliers),
            ("Generate Unique IDs 🆔", self.configureGenerateUniqueIDs),
            ("Lag Column ⏪", self.configureLagColumn),
            ("Rank Values 🏆", self.configureRankValues),
            ("Change Case 🔠", self.configureCaseConversion),
            ("Convert Datatype 🔄", self.configureConvertDatatype),
            ("Standardize Date Format 📅", self.configureStandardizeDateFormat),
            ("Normalize Data 📏", self.configureNormalizeData),
            ("Extract Substrings ✂️", self.configureExtractSubstrings),
            ("Extract Text Between 🔎", self.configureExtractTextBetween),
            ("Extract Numeric Values 🔢", self.configureExtractNumericValues),
            ("Round Numbers 🔄", self.configureRoundNumbers),
            ("Percentage Change 📈", self.configurePercentageChange),
            ("Bucketize Values 🗃️", self.configureBucketizeValues),
            ("Extract Date Components 🗓️", self.configureExtractDateComponents),
            ("Date Shift ⏩", self.configureDateShift),
            ("Next Working Day 📅", self.configureNextWorkingDay),
            ("Find and Replace 🔍", self.configureFindAndReplace),
            ("Fill Missing Values 🩹", self.configureFillMissing),
            ("Running Total ➕", self.configureRunningTotal),
            ("Moving Average 📉", self.configureMovingAverage),
            ("Conditional Column Creation ❓", self.configureConditionalColumnCreation),
            ("Custom Function ⚙️", self.configureCustomFunction)
        ]
        for title, slot in mapping:
            gbox = QGroupBox(title)
            vb = QVBoxLayout(gbox)
            btn = QPushButton(f"Configure {title}")
            btn.clicked.connect(slot)
            vb.addWidget(btn)
            layout.addWidget(gbox)
        layout.addStretch()

    def buildExcelFunctionsTab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        
        # Lookup & Reference Group
        lookup_group = create_config_group("Lookup & Reference", "#E8DAEF", "#8E44AD")
        up_layout = QVBoxLayout(lookup_group)
        for title, slot in [
            ("VLOOKUP", self.configureVLOOKUP),
            ("XLOOKUP", self.configureXLOOKUP),
            ("INDEX/MATCH", self.configureIndexMatch),
            ("HLOOKUP", self.configureHLOOKUP)
        ]:
            btn = QPushButton(f"Configure {title}")
            btn.clicked.connect(slot)
            up_layout.addWidget(btn)
            layout.addWidget(lookup_group)
            # Date/Time Group
            date_group = create_config_group("Date/Time", "#D5F5E8", "#3498DB")
            dg_layout = QVBoxLayout(date_group)
            for title, slot in [
                ("EDATE", self.configureEDATE),
                ("EOMONTH", self.configureEOMONTH),
                ("NETWORKDAYS", self.configureNETWORKDAYS),
                ("DATEDIF", self.configureDATEDIF)
            ]:
                btn = QPushButton(f"Configure {title}")
                btn.clicked.connect(slot)
                dg_layout.addWidget(btn)
            layout.addWidget(date_group)    
        # Financial Functions Group
        fin_group = create_config_group("Financial", "#D4EFDF", "#27AE60")
        fg_layout = QVBoxLayout(fin_group)
        for title, slot in [
            ("NPV", self.configureNPV),
            ("IRR", self.configureIRR),
            ("PMT", self.configurePMT),
            ("FV", self.configureFV),
            ("PV", self.configurePV)
        ]:
            btn = QPushButton(f"Configure {title}")
            btn.clicked.connect(slot)
            fg_layout.addWidget(btn)
        layout.addWidget(fin_group)
    
        # Logical Functions Group
        logic_group = create_config_group("Logical", "#FDEDEC", "#E67E22")
        lg_layout = QVBoxLayout(logic_group)
        for title, slot in [
            ("IF", self.configureIF),
            ("IFS", self.configureIFS),
            ("IFERROR", self.configureIFERROR),
            ("SWITCH", self.configureSWITCH)
        ]:
            btn = QPushButton(f"Configure {title}")
            btn.clicked.connect(slot)
            lg_layout.addWidget(btn)
        layout.addWidget(logic_group)
        layout.addStretch()

    def buildReshapingTab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        mapping = [
            ("Split Column ✂️", self.configureSplitColumn),
            ("Concatenate Columns 🔗", self.configureConcatenateColumns),
            ("Pivot Data 📊", self.configurePivotData),
            ("Unpivot Data 🔄", self.configureUnpivotData),
            ("Transpose Data ↔️", self.configureTransposeData),
        ]
        for title, slot in mapping:
            gbox = QGroupBox(title)
            vb = QVBoxLayout(gbox)
            btn = QPushButton(f"Configure {title}")
            btn.clicked.connect(slot)
            vb.addWidget(btn)
            layout.addWidget(gbox)
        layout.addStretch()

    def buildAdvancedTransTab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        mapping = [
            ("Group & Aggregate 📈", self.configureGroupAggregate),
            ("Sort Data 🔃", self.configureSortData),
        ]
        for title, slot in mapping:
            gbox = QGroupBox(title)
            vb = QVBoxLayout(gbox)
            btn = QPushButton(f"Configure {title}")
            btn.clicked.connect(slot)
            vb.addWidget(btn)
            layout.addWidget(gbox)
        gbox_join = QGroupBox("Join Dataframes 🔗")
        vb_join = QVBoxLayout(gbox_join)
        btn_join = QPushButton("Configure Join Dataframes 🔗")
        btn_join.clicked.connect(self.configureJoinDataframes)
        vb_join.addWidget(btn_join)
        layout.addWidget(gbox_join)
        gbox_union = QGroupBox("Union Dataframes ➕")
        vb_union = QVBoxLayout(gbox_union)
        btn_union = QPushButton("Configure Union Dataframes ➕")
        btn_union.clicked.connect(self.configureUnionDataframes)
        vb_union.addWidget(btn_union)
        layout.addWidget(gbox_union)
        gbox_analytical = QGroupBox("Analytical Functions 📝")
        vb_analytical = QVBoxLayout(gbox_analytical)
        btn_analytical = QPushButton("Configure Analytical Functions 📝")
        btn_analytical.clicked.connect(self.configureAnalyticalFunctions)
        vb_analytical.addWidget(btn_analytical)
        layout.addWidget(gbox_analytical)
        layout.addStretch()

    def buildAdvancedOpsTab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        gb_lookup_cond = QGroupBox("Lookup & Conditional 🔍")
        vb_lookup_cond = QVBoxLayout(gb_lookup_cond)
        btn_lookup_cond = QPushButton("Configure Lookup & Conditional 🔍")
        btn_lookup_cond.clicked.connect(self.configureAdvancedLookupConditional)
        vb_lookup_cond.addWidget(btn_lookup_cond)
        layout.addWidget(gb_lookup_cond)
        gb_dt = QGroupBox("Date & Time Functions ⏰")
        vb_dt = QVBoxLayout(gb_dt)
        btn_dt = QPushButton("Configure Date & Time Functions ⏰")
        btn_dt.clicked.connect(self.configureAdvancedDateTime)
        vb_dt.addWidget(btn_dt)
        layout.addWidget(gb_dt)
        gb_text = QGroupBox("Enhanced Text Operations 🔡")
        vb_text = QVBoxLayout(gb_text)
        btn_text = QPushButton("Configure Enhanced Text Operations 🔡")
        btn_text.clicked.connect(self.configureAdvancedTextOps)
        vb_text.addWidget(btn_text)
        layout.addWidget(gb_text)
        gb_fin = QGroupBox("Financial Calculations 💲")
        vb_fin = QVBoxLayout(gb_fin)
        btn_fin = QPushButton("Configure Financial Calculations 💲")
        btn_fin.clicked.connect(self.configureAdvancedFinancial)
        vb_fin.addWidget(btn_fin)
        layout.addWidget(gb_fin)
        gb_dv = QGroupBox("Data Validation ✅")
        vb_dv = QVBoxLayout(gb_dv)
        btn_dv = QPushButton("Configure Data Validation ✅")
        btn_dv.clicked.connect(self.configureAdvancedDataValidation)
        vb_dv.addWidget(btn_dv)
        layout.addWidget(gb_dv)
        gb_sql = QGroupBox("SQL Query 📝")
        vb_sql = QVBoxLayout(gb_sql)
        btn_sql = QPushButton("Configure SQL Query 📝")
        btn_sql.clicked.connect(self.configureAdvancedSQL)
        vb_sql.addWidget(btn_sql)
        layout.addWidget(gb_sql)
        layout.addStretch()

    def buildRightPanel(self):
        label_title = QLabel("Live Data Preview")
        label_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.right_layout.addWidget(label_title)
        self.table_view = QTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.model = PandasModel(pd.DataFrame())
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.right_layout.addWidget(self.table_view)
        integrated_buttons_layout = QHBoxLayout()
        download_data_btn = QPushButton("Download Data")
        download_data_btn.clicked.connect(self.downloadData)
        summary_btn = QPushButton("Transformation Summary")
        summary_btn.clicked.connect(self.showTransformationSummary)
        lineage_btn = QPushButton("Lineage Diagram")
        lineage_btn.clicked.connect(self.showLineagePopout)
        integrated_buttons_layout.addWidget(download_data_btn)
        integrated_buttons_layout.addWidget(summary_btn)
        integrated_buttons_layout.addWidget(lineage_btn)
        self.right_layout.addLayout(integrated_buttons_layout)
        note = QLabel("Use 'Set Header' to adjust which row is used as column names.")
        note.setStyleSheet("color: #555; font-style: italic;")
        self.right_layout.addWidget(note)
        self.right_layout.addStretch()

    def showLineagePopout(self):
        friendly_config = {
            "file_upload": {
            "file_name": os.path.basename(self.state["file_path"]),
            "upload_timestamp": self.state.get("upload_timestamp", "Not Provided"),
            "file_size": os.path.getsize(self.state["file_path"]),
            "file_format": self.state["file_ext"]
            },
            "header_selection": {
                "header_row": self.state["header_row"],
                "original_columns": list(self.original_registry.values())
            },
            "Filters": [],
            "Transformations": {},
            "Advanced Excel Functions": {}
        }
    
        friendly_config["Filters"] = [
            {
                "column": internal_to_friendly(filt["column"], self.master_registry),
                "condition": filt["condition"],
                "value": filt["value"]
            }
            for filt in self.state.get("filter_conditions", [])
            if isinstance(filt, dict) and "column" in filt
        ]
        # Helper function to convert transformation parameters.
        def convert_tuple_keys_to_str(obj):
        
            if isinstance(obj, dict):
                new_obj = {}
                for k, v in obj.items():
                    if isinstance(k, tuple):
                        new_key = "::".join(str(item) for item in k)
                    else:
                        new_key = k
                    new_obj[new_key] = convert_tuple_keys_to_str(v)
                return new_obj
            elif isinstance(obj, list):
                return [convert_tuple_keys_to_str(item) for item in obj]
            else:
                return obj
        
        def process_transformation(params):
            friendly_params = {}
            for key in ["column", "columns", "subset", "columns_to_drop"]:
                if key in params:
                    value = params[key]
                    if isinstance(value, list):
                        friendly_params[key] = [internal_to_friendly(col, self.master_registry) for col in value]
                    elif isinstance(value, dict):
                        # For dictionary values, convert each key.
                        friendly_params[key] = {internal_to_friendly(k, self.master_registry): v for k, v in value.items()}
                    else:
                        friendly_params[key] = internal_to_friendly(value, self.master_registry)
            # Copy any additional parameters that are not column references.
            for k, v in params.items():
                if k not in friendly_params:
                    friendly_params[k] = v
            return friendly_params

        if self.pipeline_loaded:
            for step in self.state.get("pipeline_steps", []):
                trans_name = step["transformation"]
                params = step["parameters"]
                friendly_config["Transformations"][trans_name] = process_transformation(params)
        else:
            for trans_name, params in self.state.get("transformation_params", {}).items():
                friendly_config["Transformations"][trans_name] = process_transformation(params)

        for func_name, params in self.state.get("advanced_excel_config", {}).items():
            friendly_params = params.copy()
            for key in ["column", "columns"]:
                if key in params:
                    value = params[key]
                    if isinstance(value, list):
                        friendly_params[key] = [internal_to_friendly(col, self.master_registry) for col in value]
                    elif isinstance(value, dict):
                        friendly_params[key] = {internal_to_friendly(k, self.master_registry): v for k, v in value.items()}
                    else:
                        friendly_params[key] = internal_to_friendly(value, self.master_registry)
            friendly_config["Advanced Excel Functions"][func_name] = friendly_params
        
        column_rules = {}
        for trans, params in friendly_config["Transformations"].items():
            affected_cols = []
            # Check keys that reference columns.
            for key in ["column", "columns", "subset", "columns_to_drop"]:
                if key in params:
                    val = params[key]
                    if isinstance(val, list):
                        affected_cols.extend(val)
                    elif isinstance(val, dict):
                        # When the value is a dictionary, we consider its keys as affected columns.
                        affected_cols.extend(val.keys())
                    else:
                        affected_cols.append(val)
            # For each affected column, add the transformation rule and its details.
            for col in affected_cols:
                if col not in column_rules:
                    column_rules[col] = []
                column_rules[col].append({
                    "rule": trans,
                    "details": params
                })
        friendly_config["Column Rules"] = column_rules

        if "new_names" in self.state.get("transformation_params", {}):
            friendly_config["new_names"] = convert_tuple_keys_to_str(
                self.state["transformation_params"].get("new_names", {})
        )  
        if "having" in self.state.get("transformation_params", {}):
            friendly_config["having"] = convert_tuple_keys_to_str(
                self.state["transformation_params"].get("having", {})
        )   
        print("Friendly config for lineage", friendly_config,self.master_registry)       
        show_enhanced_lineage_in_ui(friendly_config, self.master_registry)

    def updatePreview(self, df):
        self.model.setDataFrame(df)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def _readFile(self, path, ext, header):
        try:
            if ext in [".csv", ".txt"]:
                delimiter, ok = QInputDialog.getText(self, "Specify Delimiter", "Enter delimiter for text file:", text=",")
                if not ok:
                    delimiter = ","
                return pd.read_csv(path, delimiter=delimiter, header=header)
            elif ext in [".xlsx", ".xls"]:
                sheet_name, ok = QInputDialog.getText(self, "Select Sheet", "Enter sheet name (leave blank for first sheet):")
                if not ok:
                    sheet_name = 0
                return pd.read_excel(path, sheet_name=sheet_name, header=header)
            elif ext == ".parquet":
                return pd.read_parquet(path)
            elif ext == ".json":
                return pd.read_json(path)
            elif ext == ".xml":
                return pd.read_xml(path)
            else:
                return pd.read_csv(path, header=header)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read file:\n{str(e)}")
            return pd.DataFrame()
        
    def onSetHeaderClicked(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        new_header = self.spin_header.value()
        self.state["header_row"] = new_header
        try:
            old_registry = self.column_registry.copy()
            df = self._readFile(self.state["file_path"], self.state["file_ext"], new_header)
            self.friendly_columns = df.columns.tolist()
            self.master_registry.clear()
            self.column_registry.clear()
            new_cols = []
            for i, col in enumerate(self.friendly_columns):
                cid = f"col_{i+1}"
                self.master_registry[cid] = str(col)
                self.column_registry[cid] = str(col)
                new_cols.append(cid)
            df.columns = new_cols
            self.original_registry = self.master_registry.copy()
            #print("New registry", self.original_registry)
            if self.state["filter_conditions"]:
                for cond in self.state["filter_conditions"]:
                    if "column" in cond:
                        old_friendly = cond["column"]
                        for key, friendly in old_registry.items():
                            if friendly == old_friendly and key in self.column_registry:
                                cond["column"] = self.column_registry[key]
                                break
            self.state["original_df"] = df.copy()
            self.applyAllTransformationsAndRefresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Reload file failed:\n{str(e)}")

    def revertTransformations(self):
        answer = QMessageBox.warning(
            self,
            "Revert All",
            "Are you sure you want to revert all transformations?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.state["filter_conditions"] = []
            self.state["transformation_params"] = {}
            self.state["advanced_excel_config"] = {}
            self.state["pipeline_steps"] = []
            self.pipeline_loaded = False
            self.applyAllTransformationsAndRefresh()

    def savePipeline(self):
        # Check if any transformations, filters, or advanced Excel functions are selected.
        if (not self.state["filter_conditions"]
                and not (self.pipeline_loaded and self.state["pipeline_steps"])
                and not self.state["advanced_excel_config"]
                and not (not self.pipeline_loaded and self.state["transformation_params"])):
            QMessageBox.information(self, "Save Pipeline", "No transformations selected.")
            return
    
        if self.pipeline_loaded:
            config = {
                "Header Row": self.state["header_row"],
                "Filters": self.state["filter_conditions"],
                "Pipeline Steps": self.state["pipeline_steps"],
                "Advanced Excel Functions": self.state["advanced_excel_config"],
                "Column Registry": self.original_registry 
            }
        else:
            trans_config = self.state["transformation_params"].copy()
            #print("Saving transformations",trans_config)
            if "Rename Columns" in trans_config:
                friendly_mapping = trans_config["Rename Columns"]
                new_mapping = {}
                for friendly_name, new_name in friendly_mapping.items():
                    internal_key = single_friendly_to_internal(friendly_name, self.master_registry)
                    if not internal_key:
                        internal_key = friendly_name
                    new_mapping[internal_key] = new_name
                trans_config["Rename Columns"] = new_mapping
            print(trans_config)
            config = {
                "Header Row": self.state["header_row"],
                "Filters": self.state["filter_conditions"],
                "Transformations": trans_config,
                "Advanced Excel Functions": self.state["advanced_excel_config"],
                "Column Registry": self.original_registry  # Save mapping info here
            }

        path, _ = QFileDialog.getSaveFileName(self, "Save Pipeline Config", "", "JSON Files (*.json)")
        if path:
            try:
                save_pipeline_config( config,path)
                QMessageBox.information(self, "Success", "Pipeline saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving pipeline:\n{str(e)}")
    
    def loadPipeline(self):
        if self.state["df"] is None:
            QMessageBox.warning(self, "No Data", "Please upload a file before loading a pipeline.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Load Pipeline Config", "", "JSON Files (*.json)")
        if path:
            try:  
                config = load_pipeline_config(path)
                # Update state with saved header row and filters.
                self.state["header_row"] = config.get("Header Row", 0)
                self.state["filter_conditions"] = config.get("Filters", [])
                # Check if the saved config uses pipeline steps or direct transformation parameters.
                if "Pipeline Steps" in config:
                    self.state["pipeline_steps"] = config.get("Pipeline Steps", [])
                    self.pipeline_loaded = True
                else:
                    self.state["transformation_params"] = config.get("Transformations", {})
                    self.pipeline_loaded = False
                self.state["advanced_excel_config"] = config.get("Advanced Excel Functions", {})
    
                # Retrieve the saved column registry (mapping internal IDs to friendly names) from the pipeline config.
                saved_registry = config.get("Column Registry", {})
                saved_friendly = set(saved_registry.values())
                new_friendly = set(self.master_registry.values())
                missing_columns = saved_friendly - new_friendly
                if missing_columns:
                    QMessageBox.warning(
                        self,
                        "Column Mismatch",
                        f"The loaded pipeline references column(s) {', '.join(missing_columns)} that are not present in the current file.\n"
                        "Please check your file or update the pipeline accordingly."
                    )
                self.spin_header.setValue(self.state["header_row"])
                if "Rename Columns" in self.state["transformation_params"]:
                    rename_info = self.state["transformation_params"]["Rename Columns"]
                    internal_mapping = rename_info.get("internal", {})
                    for cid, new_name in internal_mapping.items():
                        if cid in self.master_registry:
                            self.master_registry[cid] = new_name
                self.state["loaded_config"] = True
                if self.state["original_df"] is not None:
                    self.applyAllTransformationsAndRefresh()
                QMessageBox.information(self, "Success", "Pipeline loaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading pipeline:\n{str(e)}")

    def applyAllTransformationsAndRefresh(self):
        if self.state["original_df"] is None:
            self.updatePreview(pd.DataFrame())
            return
        df = self.state["original_df"].copy()
        if self.pipeline_loaded:
            transformations = {}
            for step in sorted(self.state["pipeline_steps"], key=lambda x: x["order"]):
                transformations[step["transformation"]] = step["parameters"]
        else:
            transformations = self.state["transformation_params"]
        config = {
            "Header Row": self.state["header_row"],
            "Filters": self.state["filter_conditions"],
            "Transformations": transformations,
            "Advanced Excel Functions": self.state["advanced_excel_config"],
        }
        try:
            df_transformed, summary_list = apply_transformations_with_summary(df, config)
            df_transformed = apply_advanced_excel_transformations(df_transformed, config["Advanced Excel Functions"])
            if "Join Dataframes" in config["Transformations"]:
                params = config["Transformations"]["Join Dataframes"]
                join_file = params.get("file_path")
                if join_file:
                    try:
                        ext = os.path.splitext(join_file)[1].lower()
                        if ext in [".csv", ".txt"]:
                            second_df = pd.read_csv(join_file)
                        elif ext in [".xlsx", ".xls"]:
                            second_df = pd.read_excel(join_file)
                        else:
                            second_df = pd.read_csv(join_file)
                        df_transformed = merge_join_dataframes(
                            [df_transformed, second_df],
                            params["join_type"],
                            params["base_key"],
                            [params["other_key"]],
                        )
                        summary_list.append({
                            "transformation": "Join Dataframes",
                            "sequence": 9999,
                            "initial_count": None,
                            "new_count": len(df_transformed),
                        })
                    except Exception as e:
                        QMessageBox.critical(self, "Join Error", f"Error joining data:\n{str(e)}")
            if "Union Dataframes" in config["Transformations"]:
                params = config["Transformations"]["Union Dataframes"]
                union_file = params.get("file_path")
                if union_file:
                    try:
                        ext = os.path.splitext(union_file)[1].lower()
                        if ext in [".csv", ".txt"]:
                            second_df = pd.read_csv(union_file)
                        elif ext in [".xlsx", ".xls"]:
                            second_df = pd.read_excel(union_file)
                        else:
                            second_df = pd.read_csv(union_file)
                        base_cols = list(df_transformed.columns)
                        second_cols = list(second_df.columns)
                        if len(base_cols) != len(second_cols):
                            msg = (
                                "Union requires dataframes to have the same number of columns.\n"
                                f"Base has {len(base_cols)} columns, second DF has {len(second_cols)}."
                            )
                            QMessageBox.warning(self, "Union Warning", msg)
                            raise ValueError(msg)
                        union_all = params.get("union_all", False)
                        df_transformed = union_dataframes([df_transformed, second_df], union_all)
                        summary_list.append({
                            "transformation": "Union Dataframes",
                            "sequence": 9999,
                            "initial_count": None,
                            "new_count": len(df_transformed),
                        })
                    except Exception as e:
                        QMessageBox.critical(self, "Union Error", f"Error unioning data:\n{str(e)}")
            self.state["df"] = df_transformed
            self.state["transformation_summary"] = summary_list
            existing_cols = set(df_transformed.columns)
            self.column_registry = {cid: self.master_registry[cid] for cid in self.master_registry if cid in existing_cols}
            display_df = df_transformed.copy()
            display_df.columns = [internal_to_friendly(col, self.master_registry) for col in display_df.columns]
            self.updatePreview(display_df)

            rc = len(df_transformed)
            self.status_bar.showMessage(f"Row count: {rc}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not apply transformations:\n{str(e)}")

    def openSimpleDialog(self, title, fields):
        dlg = GenericTransformationDialog(list(self.column_registry.values()), self.column_registry,
                                          param_defs=fields, dialog_title=f"Configure {title}")
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            params = dlg.getValues()
            if self.pipeline_loaded:
                self.addPipelineStep(title, params)
            else:
                self.state["transformation_params"][title] = params
            self.applyAllTransformationsAndRefresh()

    def configureFilters(self):
        if self.state["df"] is None:
            QMessageBox.warning(self, "No data", "Load a file first.")
            return
    
        # Show the filter dialog
        dlg = FilterDialog(
            list(self.column_registry.values()),
            self.column_registry,
            self.state["filter_conditions"],
            self
        )
        dlg.setMinimumSize(600, 400)
    
        if dlg.exec() == QDialog.DialogCode.Accepted:
            raw_conditions = dlg.getFilterConditions()
            converted_conditions = self._convert_filter_conditions_to_internal(raw_conditions)
            self.state["filter_conditions"] = converted_conditions
            self.applyAllTransformationsAndRefresh()
    
    def _convert_filter_conditions_to_internal(self, raw_conditions):
        converted = []
        for group_data in raw_conditions:
            group_logic = group_data.get("group_logic", "")
            conditions = group_data.get("conditions", [])
            new_group = {
                "group_logic": group_logic,
                "conditions": []
            }
            for cond in conditions:
                row_logic = cond.get("row_logic", "")
                friendly_col = cond.get("col", "")
                condition_type = cond.get("cond", "")
                value = cond.get("value", "")
                
                # Find the matching internal column name
                internal_col = friendly_col
                for i_name, f_name in self.column_registry.items():
                    if f_name == friendly_col:
                        internal_col = i_name
                        break
    
                # Parse the value based on condition type
                if condition_type == "Between":
                    value = parse_between_range(value)
                elif condition_type == "Date Between":
                    value = parse_date_range(value)
                elif condition_type in ["In List", "Not In List"]:
                    value = parse_in_list(value)
                
                new_group["conditions"].append({
                    "row_logic": row_logic,
                    "col": internal_col,
                    "cond": condition_type,
                    "value": value
                })
            converted.append(new_group)
        return converted
    
    def configureRemoveDuplicates(self):
        if self.state["df"] is None:
            QMessageBox.warning(self, "No data", "Load a file first.")
            return
        init_params = self.state["transformation_params"].get("Remove Duplicates", {})
        dlg = RemoveDuplicatesDialog(list(self.column_registry.values()), self.column_registry, init_params, self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Remove Duplicates", dlg.getParams())
            else:
                self.state["transformation_params"]["Remove Duplicates"] = dlg.getParams()
            self.applyAllTransformationsAndRefresh()

    def configureDropColumns(self):
        if self.state["df"] is None:
            QMessageBox.warning(self, "No data", "Load a file first.")
            return
        preselected = self.state["transformation_params"].get("Drop Columns", {}).get("columns_to_drop", [])
        dlg = DropColumnsDialog(list(self.master_registry.values()), self.master_registry,
                                preselected_columns=preselected, parent=self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected = dlg.getSelectedColumns()
   
            if selected:
                if self.pipeline_loaded:
                    self.addPipelineStep("Drop Columns", {"columns_to_drop": selected, "registry": self.master_registry})
                else:
                    self.state["transformation_params"]["Drop Columns"] = {"columns_to_drop": selected, "registry": self.master_registry}
            else:
                if self.pipeline_loaded:
                    self.state["pipeline_steps"] = [step for step in self.state["pipeline_steps"] if step["transformation"] != "Drop Columns"]
                else:
                    self.state["transformation_params"].pop("Drop Columns", None)
            self.applyAllTransformationsAndRefresh()

    def configureRenameColumns(self):
        if self.state["df"] is None:
            QMessageBox.warning(self, "No data", "Load a file first.")
            return
        dlg = MultiColumnRenameDialog(list(self.column_registry.values()), self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            friendly_mapping = dlg.getRenameMappings()
            if friendly_mapping:
                internal_mapping = {}
                for cid, current_friendly in self.column_registry.items():
                    if current_friendly in friendly_mapping:
                        new_name = friendly_mapping[current_friendly]
                        internal_mapping[cid] = new_name
                        self.master_registry[cid] = new_name
                        self.column_registry[cid] = new_name
                rename_step = {
                    "internal": internal_mapping
                     }
                if self.pipeline_loaded:
                    self.addPipelineStep("Rename Columns", rename_step)
                    print("Renaming columns:", rename_step)
                else:
                    self.state["transformation_params"]["Rename Columns"] = rename_step  
                self.applyAllTransformationsAndRefresh()

    def configureFlagMissing(self):
        if self.state["df"] is None:
            QMessageBox.warning(self, "No data", "Load a file first.")
            return
        existing = self.state["transformation_params"].get("Flag Missing Values", {}).get("columns", {})
        dlg = FlagMissingDialog(list(self.column_registry.values()), self.column_registry, existing, self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            newmap = dlg.getFlagMapping()
            if newmap:
                if self.pipeline_loaded:
                    self.addPipelineStep("Flag Missing Values", {"columns": newmap})
                else:
                    self.state["transformation_params"]["Flag Missing Values"] = {"columns": newmap}
            else:
                if self.pipeline_loaded:
                    self.state["pipeline_steps"] = [step for step in self.state["pipeline_steps"] if step["transformation"] != "Flag Missing Values"]
                else:
                    self.state["transformation_params"].pop("Flag Missing Values", None)
            self.applyAllTransformationsAndRefresh()

    def configureTrim(self):
        if self.state["df"] is None:
            QMessageBox.warning(self, "No Data", "Please upload a file before configuring Trim Spaces.")
            return

        init_params = self.state["transformation_params"].get("Trim", {})
        converted_ui_params = {"columns": {}}
    
        for internal_name, settings in init_params.get("columns", {}).items():
            friendly_name = internal_to_friendly(internal_name, self.column_registry)
            if friendly_name:
                converted_ui_params["columns"][friendly_name] = settings  # Store under friendly name for UI
    
        dlg = TrimDialog(list(self.column_registry.values()), self.column_registry, converted_ui_params, self)
        dlg.setMinimumSize(600, 400)
    
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated_values = dlg.getValues()  # Retrieve updated user selections
    
            # **Convert friendly names back to internal names for processing**
            converted_values = {"columns": {}}
            for friendly_name, settings in updated_values.get("columns", {}).items():
                internal_name = single_friendly_to_internal(friendly_name, self.column_registry)
                if internal_name:
                    converted_values["columns"][internal_name] = settings  # Store under internal name for processing
    
            self.state["transformation_params"]["Trim"] = converted_values  # Save with internal names
    
            if self.pipeline_loaded:
                self.addPipelineStep("Trim", converted_values)
            else:
                self.applyAllTransformationsAndRefresh()

    def configureReplaceSubstring(self):
        if self.state["df"] is None:
            QMessageBox.warning(self, "No Data", "Please upload a file before configuring Replace Substring.")
            return
        init_params = self.state["transformation_params"].get("Replace Substring", {})
        dlg = ReplaceSubstringDialog(list(self.column_registry.values()), self.column_registry, init_params, parent=self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Replace Substring", dlg.getValues())
            else:
                self.state["transformation_params"]["Replace Substring"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureDetectOutliers(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        dlg = DetectOutliersDialog(self.friendly_columns, self.master_registry)
        if dlg.exec() == QDialog.DialogCode.Accepted:
                config = dlg.getValues()
                self.state["transformation_params"]["Detect Outliers"] = config
                self.applyAllTransformationsAndRefresh()

    def configureGenerateUniqueIDs(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        init_params = self.state["transformation_params"].get("Generate Unique IDs", {})
        dlg = GenerateUniqueIDsDialog(list(self.column_registry.values()), self.column_registry, init_params, self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Generate Unique IDs", dlg.getValues())
            else:
                self.state["transformation_params"]["Generate Unique IDs"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureLagColumn(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        self.openSimpleDialog("Lag Column", [{"name": "lag", "label": "Lag Amount (periods)", "type": "int"}])

    def configureRankValues(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        self.openSimpleDialog("Rank Values", [{"name": "method", "label": "Ranking Method (min, desc, etc.)", "type": "str"}])

    def configureCaseConversion(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        init_params = self.state["transformation_params"].get("Change Case", {})
        dlg = CaseConversionDialog(list(self.column_registry.values()), self.column_registry, init_params, self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated_values = dlg.getValues()
            self.state["transformation_params"]["Change Case"] = updated_values
            if self.pipeline_loaded:
                self.addPipelineStep("Change Case", updated_values)
            else:
                self.applyAllTransformationsAndRefresh()

    def configureConvertDatatype(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        init_params = self.state["transformation_params"].get("Convert Datatype", {})
        dlg = ConvertDatatypeDialog(list(self.column_registry.values()), self.column_registry, init_params, self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Convert Datatype", dlg.getValues())
            else:
                self.state["transformation_params"]["Convert Datatype"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureStandardizeDateFormat(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        dlg = DateFormatDialog(self.friendly_columns, self.master_registry)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            config = dlg.getValues()
            self.state["transformation_params"]["Standardize Date Format"] = config
            self.applyAllTransformationsAndRefresh()

    def configureNormalizeData(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        dlg = NormalizeDataDialog(self.friendly_columns, self.master_registry)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            config = dlg.getValues()
            self.state["transformation_params"]["Normalize Data"] = config
            self.applyAllTransformationsAndRefresh()

    def configureExtractSubstrings(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        fields = [
            {"name": "start", "label": "Start Position", "type": "int"},
            {"name": "length", "label": "Substring Length", "type": "int"}
        ]
        self.openSimpleDialog("Extract Substrings", fields)

    def configureExtractTextBetween(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        fields = [
            {"name": "left_delim", "label": "Left Delimiter", "type": "str"},
            {"name": "right_delim", "label": "Right Delimiter", "type": "str"}
        ]
        self.openSimpleDialog("Extract Text Between", fields)

    def configureExtractNumericValues(self):
        self.openSimpleDialog("Extract Numeric Values", [])

    def configureRoundNumbers(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        self.openSimpleDialog("Round Numbers", [{"name": "decimals", "label": "Number of Decimals", "type": "int"},
                                                  {"name": "rounding_mode", "label": "Rounding Mode", "type": "str"}])

    def configurePercentageChange(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        self.openSimpleDialog("Percentage Change", [{"name": "factor", "label": "Factor (default 100)", "type": "int"}])

    def configureBucketizeValues(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        self.openSimpleDialog("Bucketize Values", [{"name": "bins", "label": "Bucket Boundaries (comma separated)", "type": "str"}])

    def configureExtractDateComponents(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        fields = [
            {"name": "year", "label": "New Year Column", "type": "str"},
            {"name": "month", "label": "New Month Column", "type": "str"},
            {"name": "day", "label": "New Day Column", "type": "str"}
        ]
        self.openSimpleDialog("Extract Date Components", fields)

    def configureDateShift(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        fields = [{"name": "shift_value", "label": "Shift Value (# days)", "type": "int"},
                  {"name": "unit", "label": "Unit (d, h, etc.)", "type": "str"}]
        self.openSimpleDialog("Date Shift", fields)

    def configureNextWorkingDay(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        self.openSimpleDialog("Next Working Day", [])

    def configureFindAndReplace(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        fields = [
            {"name": "find", "label": "Find Text", "type": "str"},
            {"name": "replace", "label": "Replace With", "type": "str"}
        ]
        self.openSimpleDialog("Find and Replace", fields)

    def configureFillMissing(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        init_params = self.state["transformation_params"].get("Fill Missing Values", {})
        from ui_dialogs_data_cleaning import FillMissingDialog
        dlg = FillMissingDialog(list(self.column_registry.values()), self.column_registry, init_params, self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Fill Missing Values", dlg.getValues())
            else:
                self.state["transformation_params"]["Fill Missing Values"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureRunningTotal(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        self.openSimpleDialog("Running Total", [{"name": "window", "label": "Unused - or group_by param if needed", "type": "int"}])

    def configureMovingAverage(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        self.openSimpleDialog("Moving Average", [{"name": "window", "label": "Moving Average Window", "type": "int"},
                                                  {"name": "min_periods", "label": "Minimum Periods", "type": "int"}])

    def configureConditionalColumnCreation(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        fields = [
            {"name": "condition", "label": "Condition (e.g., df['col'] > 5)", "type": "str"},
            {"name": "true_value", "label": "Value if True", "type": "str"},
            {"name": "false_value", "label": "Value if False", "type": "str"},
            {"name": "new_column", "label": "New Column Name", "type": "str"}
        ]
        self.openSimpleDialog("Conditional Column Creation", fields)

    def configureCustomFunction(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        self.openSimpleDialog("Custom Function", [{"name": "function", "label": "Function Name or Code", "type": "str"}])

    def configureSplitColumn(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        init_config = self.state["transformation_params"].get("Split Column", None)
        dlg = SplitColumnDialog(list(self.column_registry.values()), self.column_registry, init_values=init_config, parent=self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Split Column", dlg.getValues())
            else:
                self.state["transformation_params"]["Split Column"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureConcatenateColumns(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        init_config = self.state["transformation_params"].get("Concatenate Columns", None)
        dlg = ConcatenateColumnsDialog(list(self.column_registry.values()), self.column_registry, init_values=init_config, parent=self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Concatenate Columns", dlg.getValues())
            else:
                self.state["transformation_params"]["Concatenate Columns"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configurePivotData(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        init_config = self.state["transformation_params"].get("Pivot Data", None)
        dlg = PivotDataDialog(list(self.column_registry.values()), self.column_registry, init_values=init_config, parent=self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Pivot Data", dlg.getValues())
            else:
                self.state["transformation_params"]["Pivot Data"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureUnpivotData(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        init_config = self.state["transformation_params"].get("Unpivot Data", None)
        dlg = UnpivotDataDialog(list(self.column_registry.values()), self.column_registry, init_values=init_config, parent=self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Unpivot Data", dlg.getValues())
            else:
                self.state["transformation_params"]["Unpivot Data"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureTransposeData(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        init_config = self.state["transformation_params"].get("Transpose Data", None)
        dlg = TransposeDataDialog(init_values=init_config, parent=self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Transpose Data", dlg.getValues())
            else:
                self.state["transformation_params"]["Transpose Data"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureGroupAggregate(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        init_params = self.state["transformation_params"].get("Group & Aggregate", {})  # ensure it's a dictionary
        dlg = GroupAggregateDialog(list(self.column_registry.values()), self.column_registry, init_params, self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Group & Aggregate", dlg.getValues())
            else:
                self.state["transformation_params"]["Group & Aggregate"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureSortData(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        dlg = SortDataDialog(list(self.column_registry.values()), self.column_registry, self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Sort Data", dlg.getValues())
            else:
                self.state["transformation_params"]["Sort Data"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureJoinDataframes(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        dlg = JoinDataframesDialog(list(self.master_registry.values()), self.master_registry, self)
        dlg.setMinimumSize(400, 300)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Join Dataframes", dlg.getValues())
            else:
                self.state["transformation_params"]["Join Dataframes"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureUnionDataframes(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        dlg = UnionDataframesDialog(self)
        dlg.setMinimumSize(600, 200)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Union Dataframes", dlg.getValues())
            else:
                self.state["transformation_params"]["Union Dataframes"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    def configureAnalyticalFunctions(self):
        if not self.state["file_path"]:
            QMessageBox.warning(self, "No File", "Load a file first.")
            return
        dlg = AnalyticalFunctionsDialog(list(self.column_registry.values()), self.column_registry, self.state["transformation_params"].get("Analytical Functions", {}), self)
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.pipeline_loaded:
                self.addPipelineStep("Analytical Functions", dlg.getValues())
            else:
                self.state["transformation_params"]["Analytical Functions"] = dlg.getValues()
            self.applyAllTransformationsAndRefresh()

    # ------------------ New Configuration Methods for Excel Functions ------------------
    def configureLeft(self):
        self.openSimpleDialog("LEFT", [{"name": "column", "label": "Column", "type": "str"},
                                       {"name": "num_chars", "label": "Number of Characters", "type": "int"}])
    def configureRight(self):
        self.openSimpleDialog("RIGHT", [{"name": "column", "label": "Column", "type": "str"},
                                        {"name": "num_chars", "label": "Number of Characters", "type": "int"}])
    def configureMid(self):
        self.openSimpleDialog("MID", [{"name": "column", "label": "Column", "type": "str"},
                                      {"name": "start", "label": "Start Position", "type": "int"},
                                      {"name": "num_chars", "label": "Number of Characters", "type": "int"}])
    def configureLen(self):
        self.openSimpleDialog("LEN", [{"name": "column", "label": "Column", "type": "str"}])
    def configureDatedif(self):
        self.openSimpleDialog("DATEDIF", [
            {"name": "start_date_column", "label": "Start Date Column", "type": "str"},
            {"name": "end_date_column", "label": "End Date Column", "type": "str"},
            {"name": "unit", "label": "Unit (days/months/years)", "type": "str"}
        ])
    def configureEOMONTH(self):
        self.openSimpleDialog("EOMONTH", [
            {"name": "date_column", "label": "Date Column", "type": "str"},
            {"name": "months", "label": "Month Offset", "type": "int"}
        ])
    def configureWeekday(self):
        self.openSimpleDialog("WEEKDAY", [{"name": "date_column", "label": "Date Column", "type": "str"}])
    def configureUnique(self):
        self.openSimpleDialog("Unique", [{"name": "column", "label": "Column", "type": "str"}])
    def configureSortArray(self):
        self.openSimpleDialog("Sort Array", [
            {"name": "column", "label": "Column", "type": "str"},
            {"name": "ascending", "label": "Ascending (True/False)", "type": "str"}
        ])
    def configureNPV(self):
        self.openSimpleDialog("NPV", [
            {"name": "discount_rate", "label": "Discount Rate", "type": "float"},
            {"name": "cashflow_column", "label": "Cashflow Column", "type": "str"}
        ])
    def configureIRR(self):
        self.openSimpleDialog("IRR", [
            {"name": "cashflow_column", "label": "Cashflow Column", "type": "str"}
        ])
    def configurePMT(self):
        self.openSimpleDialog("PMT", [
            {"name": "rate", "label": "Rate", "type": "float"},
            {"name": "nper", "label": "Number of Periods", "type": "int"},
            {"name": "pv", "label": "Present Value", "type": "float"}
        ])
    def configureIF(self):
        self.openSimpleDialog("IF", [
            {"name": "column", "label": "Reference Column", "type": "str"},
            {"name": "condition", "label": "Condition (e.g., df['col'] > 5)", "type": "str"},
            {"name": "true_value", "label": "True Value", "type": "str"},
            {"name": "false_value", "label": "False Value", "type": "str"}
        ])
    def configureIFERROR(self):
        self.openSimpleDialog("IFERROR", [
            {"name": "column", "label": "Reference Column", "type": "str"},
            {"name": "fallback", "label": "Fallback Value", "type": "str"}
        ])
    def configureVLOOKUP(self):
        self.openSimpleDialog("VLOOKUP", [
            {"name": "lookup_value", "label": "Lookup Value", "type": "str"},
            {"name": "table_array", "label": "Table Array (JSON)", "type": "str"},
            {"name": "col_index", "label": "Column Index", "type": "int"},
            {"name": "range_lookup", "label": "Range Lookup (True/False)", "type": "str"}
        ])    
    def configureXLOOKUP(self):
        self.openSimpleDialog("XLOOKUP", [
            {"name": "source_column", "label": "Source Column", "type": "str"},
            {"name": "lookup_table", "label": "Lookup Table (JSON)", "type": "str"},
            {"name": "lookup_key", "label": "Lookup Key", "type": "str"},
            {"name": "lookup_value", "label": "Lookup Value", "type": "str"},
            {"name": "approximate_match", "label": "Approximate Match (True/False)", "type": "str"},
            {"name": "tolerance", "label": "Tolerance (numeric)", "type": "float"}
        ])
    def configureHLOOKUP(self):
        self.openSimpleDialog("HLOOKUP", [
            {"name": "lookup_value", "label": "Lookup Value", "type": "str"},
            {"name": "table_array", "label": "Table Array (JSON)", "type": "str"},
            {"name": "row_index", "label": "Row Index", "type": "int"},
            {"name": "range_lookup", "label": "Range Lookup (True/False)", "type": "str"}
        ])        
    def configureEDATE(self):
        self.openSimpleDialog("EDATE", [
            {"name": "start_date", "label": "Start Date Column", "type": "str"},
            {"name": "months", "label": "Month Offset", "type": "int"}
        ]) 
    def configureNETWORKDAYS(self):
        self.openSimpleDialog("NETWORKDAYS", [
            {"name": "start_date", "label": "Start Date Column", "type": "str"},
            {"name": "end_date", "label": "End Date Column", "type": "str"},
            {"name": "holidays", "label": "Holidays (Comma-separated dates)", "type": "str"}
        ])    
    def configureDATEDIF(self):
        self.openSimpleDialog("DATEDIF", [
            {"name": "start_date_column", "label": "Start Date Column", "type": "str"},
            {"name": "end_date_column", "label": "End Date Column", "type": "str"},
            {"name": "unit", "label": "Unit (days/months/years)", "type": "str"}
        ])   
    def configureFV(self):
        self.openSimpleDialog("FV", [
            {"name": "rate", "label": "Rate", "type": "float"},
            {"name": "nper", "label": "Number of Periods", "type": "int"},
            {"name": "pmt", "label": "Payment per Period", "type": "float"},
            {"name": "pv", "label": "Present Value", "type": "float"}
        ])     
    def configurePV(self):
        self.openSimpleDialog("PV", [
            {"name": "rate", "label": "Rate", "type": "float"},
            {"name": "nper", "label": "Number of Periods", "type": "int"},
            {"name": "pmt", "label": "Payment per Period", "type": "float"},
            {"name": "fv", "label": "Future Value", "type": "float"}
        ])    
    def configureIFS(self):
        self.openSimpleDialog("IFS", [
            {"name": "conditions", "label": "Conditions (comma separated)", "type": "str"},
            {"name": "results", "label": "Results (comma separated)", "type": "str"},
            {"name": "default_value", "label": "Default Value", "type": "str"}
        ])    
    def configureSWITCH(self):
        self.openSimpleDialog("SWITCH", [
            {"name": "expression", "label": "Expression", "type": "str"},
            {"name": "cases", "label": "Cases (JSON: key-value pairs)", "type": "str"},
            {"name": "default", "label": "Default Value", "type": "str"}
        ])                                   
    def configureIndexMatch(self):
        self.openSimpleDialog("INDEX/MATCH", [
            {"name": "source_column", "label": "Source Column", "type": "str"},
            {"name": "lookup_table", "label": "Lookup Table (JSON)", "type": "str"},
            {"name": "lookup_key", "label": "Lookup Key", "type": "str"},
            {"name": "return_column", "label": "Return Column", "type": "str"},
            {"name": "approximate_match", "label": "Approximate Match (True/False)", "type": "str"},
            {"name": "tolerance", "label": "Tolerance (numeric)", "type": "float"}
        ])
    def configureTEXTJOIN(self):
        self.openSimpleDialog("TEXTJOIN", [
            {"name": "columns", "label": "Columns (comma separated)", "type": "str"},
            {"name": "delimiter", "label": "Delimiter", "type": "str"}
        ])

    def openSimpleDialog(self, title, fields):
        dlg = GenericTransformationDialog(list(self.column_registry.values()), self.column_registry,
                                          param_defs=fields, dialog_title=f"Configure {title}")
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            params = dlg.getValues()
            if self.pipeline_loaded:
                self.addPipelineStep(title, params)
            else:
                self.state["transformation_params"][title] = params
            self.applyAllTransformationsAndRefresh()

    def loadDataFile(self):
        dlg = QFileDialog(self, "Select Data File")
        dlg.setNameFilters([
            "CSV Files (*.csv)",
            "Text Files (*.txt)",
            "Excel Files (*.xlsx *.xls)",
            "Parquet Files (*.parquet)",
            "JSON Files (*.json)",
            "XML Files (*.xml)",
            "All Files (*.*)"
        ])
        if dlg.exec():
            path = dlg.selectedFiles()[0]
            if not path:
                return
            path = os.path.normpath(path)
            self.state["file_path"] = path
            file_size = os.path.getsize(path)
            threshold = 1 * 1024 * 1024  # 1 MB
            if file_size > threshold and not path.lower().endswith('.parquet'):
                progress = QProgressDialog("Converting large file to Parquet...", None, 0, 0, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
                QApplication.processEvents()
                path = convert_to_parquet(path, header=self.spin_header.value())
                progress.close()
            self.state["file_ext"] = os.path.splitext(path)[1].lower()
            try:
                if self.state["file_ext"] in [".csv", ".txt"]:
                    delimiter, ok = QInputDialog.getText(self, "Specify Delimiter", "Enter delimiter for text file:", text=",")
                    if not ok:
                        delimiter = ","
                    df = pd.read_csv(path, delimiter=delimiter, header=self.spin_header.value())
                elif self.state["file_ext"] in [".xlsx", ".xls"]:
                    # Get the list of sheets in the Excel file
                    excel_file = pd.ExcelFile(path)
                    sheet_names = excel_file.sheet_names
                    
                    # Create a dialog with a dropdown to select the sheet
                    sheet_dialog = QDialog(self)
                    sheet_dialog.setWindowTitle("Select Sheet")
                    layout = QVBoxLayout(sheet_dialog)
                    sheet_label = QLabel("Select a sheet to load:")
                    layout.addWidget(sheet_label)
                    sheet_combo = QComboBox()
                    sheet_combo.addItems(sheet_names)
                    layout.addWidget(sheet_combo)
                    button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
                    button_box.accepted.connect(sheet_dialog.accept)
                    button_box.rejected.connect(sheet_dialog.reject)
                    layout.addWidget(button_box)
                    sheet_dialog.setLayout(layout)
                    
                    if sheet_dialog.exec() == QDialog.DialogCode.Accepted:
                        selected_sheet = sheet_combo.currentText()
                        df = pd.read_excel(path, sheet_name=selected_sheet, header=self.spin_header.value())
                    else:
                        return  # User canceled the sheet selection
                elif self.state["file_ext"] == ".parquet":
                    df = pd.read_parquet(path)
                elif self.state["file_ext"] == ".json":
                    df = pd.read_json(path)
                elif self.state["file_ext"] == ".xml":
                    df = pd.read_xml(path)
                else:
                    df = pd.read_csv(path, header=self.spin_header.value())
                
                self.friendly_columns = df.columns.tolist()
                self.master_registry.clear()
                self.column_registry.clear()
                new_cols = []
                for i, col in enumerate(self.friendly_columns):
                    cid = f"col_{i+1}"
                    self.master_registry[cid] = str(col)
                    self.column_registry[cid] = str(col)
                    new_cols.append(cid)
                df.columns = new_cols
                self.original_registry = self.master_registry.copy()
                #print("New registry", self.original_registry)
                self.state["original_df"] = df.copy()
                if not self.state["loaded_config"]:
                    self.state["filter_conditions"] = []
                    self.state["transformation_params"] = {}
                    self.state["advanced_excel_config"] = {}
                    self.state["pipeline_steps"] = []
                    self.pipeline_loaded = False
                self.applyAllTransformationsAndRefresh()
                QMessageBox.information(self, "Success", "Data file loaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not read file:\n{str(e)}")

    def applyAllTransformationsAndRefresh(self):
        if self.state["original_df"] is None:
            self.updatePreview(pd.DataFrame())
            return
        df = self.state["original_df"].copy()
        if self.pipeline_loaded:
            transformations = {}
            for step in sorted(self.state["pipeline_steps"], key=lambda x: x["order"]):
                transformations[step["transformation"]] = step["parameters"]
        else:
            transformations = self.state["transformation_params"]
        config = {
            "Header Row": self.state["header_row"],
            "Filters": self.state["filter_conditions"],
            "Transformations": transformations,
            "Advanced Excel Functions": self.state["advanced_excel_config"],
        }
        try:
            df_transformed, summary_list = apply_transformations_with_summary(df, config)
            df_transformed = apply_advanced_excel_transformations(df_transformed, config["Advanced Excel Functions"])
            if "Join Dataframes" in config["Transformations"]:
                params = config["Transformations"]["Join Dataframes"]
                join_file = params.get("file_path")
                if join_file:
                    try:
                        ext = os.path.splitext(join_file)[1].lower()
                        if ext in [".csv", ".txt"]:
                            second_df = pd.read_csv(join_file)
                        elif ext in [".xlsx", ".xls"]:
                            second_df = pd.read_excel(join_file)
                        else:
                            second_df = pd.read_csv(join_file)
                        df_transformed = merge_join_dataframes(
                            [df_transformed, second_df],
                            params["join_type"],
                            params["base_key"],
                            [params["other_key"]],
                        )
                        summary_list.append({
                            "transformation": "Join Dataframes",
                            "sequence": 9999,
                            "initial_count": None,
                            "new_count": len(df_transformed),
                        })
                    except Exception as e:
                        QMessageBox.critical(self, "Join Error", f"Error joining data:\n{str(e)}")
            if "Union Dataframes" in config["Transformations"]:
                params = config["Transformations"]["Union Dataframes"]
                union_file = params.get("file_path")
                if union_file:
                    try:
                        ext = os.path.splitext(union_file)[1].lower()
                        if ext in [".csv", ".txt"]:
                            second_df = pd.read_csv(union_file)
                        elif ext in [".xlsx", ".xls"]:
                            second_df = pd.read_excel(union_file)
                        else:
                            second_df = pd.read_csv(union_file)
                        base_cols = list(df_transformed.columns)
                        second_cols = list(second_df.columns)
                        if len(base_cols) != len(second_cols):
                            msg = (
                                "Union requires dataframes to have the same number of columns.\n"
                                f"Base has {len(base_cols)} columns, second DF has {len(second_cols)}."
                            )
                            QMessageBox.warning(self, "Union Warning", msg)
                            raise ValueError(msg)
                        union_all = params.get("union_all", False)
                        df_transformed = union_dataframes([df_transformed, second_df], union_all)
                        summary_list.append({
                            "transformation": "Union Dataframes",
                            "sequence": 9999,
                            "initial_count": None,
                            "new_count": len(df_transformed),
                        })
                    except Exception as e:
                        QMessageBox.critical(self, "Union Error", f"Error unioning data:\n{str(e)}")
            self.state["df"] = df_transformed
            self.state["transformation_summary"] = summary_list
            existing_cols = set(df_transformed.columns)
            self.column_registry = {cid: self.master_registry[cid] for cid in self.master_registry if cid in existing_cols}
            display_df = df_transformed.copy()
            display_df.columns = [internal_to_friendly(col, self.master_registry) for col in display_df.columns]
            self.updatePreview(display_df)
            rc = len(df_transformed)
            self.status_bar.showMessage(f"Row count: {rc}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not apply transformations:\n{str(e)}")

    def openSimpleDialog(self, title, fields):
        dlg = GenericTransformationDialog(list(self.column_registry.values()), self.column_registry,
                                          param_defs=fields, dialog_title=f"Configure {title}")
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            params = dlg.getValues()
            if self.pipeline_loaded:
                self.addPipelineStep(title, params)
            else:
                self.state["transformation_params"][title] = params
            self.applyAllTransformationsAndRefresh()

    # ------------------ New Configuration Methods for Excel Functions ------------------
    def configureLeft(self):
        self.openSimpleDialog("LEFT", [{"name": "column", "label": "Column", "type": "str"},
                                       {"name": "num_chars", "label": "Number of Characters", "type": "int"}])
    def configureRight(self):
        self.openSimpleDialog("RIGHT", [{"name": "column", "label": "Column", "type": "str"},
                                        {"name": "num_chars", "label": "Number of Characters", "type": "int"}])
    def configureMid(self):
        self.openSimpleDialog("MID", [{"name": "column", "label": "Column", "type": "str"},
                                      {"name": "start", "label": "Start Position", "type": "int"},
                                      {"name": "num_chars", "label": "Number of Characters", "type": "int"}])
    def configureLen(self):
        self.openSimpleDialog("LEN", [{"name": "column", "label": "Column", "type": "str"}])
    def configureDatedif(self):
        self.openSimpleDialog("DATEDIF", [
            {"name": "start_date_column", "label": "Start Date Column", "type": "str"},
            {"name": "end_date_column", "label": "End Date Column", "type": "str"},
            {"name": "unit", "label": "Unit (days/months/years)", "type": "str"}
        ])
    def configureEOMONTH(self):
        self.openSimpleDialog("EOMONTH", [
            {"name": "date_column", "label": "Date Column", "type": "str"},
            {"name": "months", "label": "Month Offset", "type": "int"}
        ])
    def configureWeekday(self):
        self.openSimpleDialog("WEEKDAY", [{"name": "date_column", "label": "Date Column", "type": "str"}])
    def configureUnique(self):
        self.openSimpleDialog("Unique", [{"name": "column", "label": "Column", "type": "str"}])
    def configureSortArray(self):
        self.openSimpleDialog("Sort Array", [
            {"name": "column", "label": "Column", "type": "str"},
            {"name": "ascending", "label": "Ascending (True/False)", "type": "str"}
        ])
    def configureNPV(self):
        self.openSimpleDialog("NPV", [
            {"name": "discount_rate", "label": "Discount Rate", "type": "float"},
            {"name": "cashflow_column", "label": "Cashflow Column", "type": "str"}
        ])
    def configureIRR(self):
        self.openSimpleDialog("IRR", [
            {"name": "cashflow_column", "label": "Cashflow Column", "type": "str"}
        ])
    def configurePMT(self):
        self.openSimpleDialog("PMT", [
            {"name": "rate", "label": "Rate", "type": "float"},
            {"name": "nper", "label": "Number of Periods", "type": "int"},
            {"name": "pv", "label": "Present Value", "type": "float"}
        ])
    def configureIF(self):
        self.openSimpleDialog("IF", [
            {"name": "column", "label": "Reference Column", "type": "str"},
            {"name": "condition", "label": "Condition (e.g., df['col'] > 5)", "type": "str"},
            {"name": "true_value", "label": "True Value", "type": "str"},
            {"name": "false_value", "label": "False Value", "type": "str"}
        ])
    def configureIFERROR(self):
        self.openSimpleDialog("IFERROR", [
            {"name": "column", "label": "Reference Column", "type": "str"},
            {"name": "fallback", "label": "Fallback Value", "type": "str"}
        ])
    def configureXLOOKUP(self):
        self.openSimpleDialog("XLOOKUP", [
            {"name": "source_column", "label": "Source Column", "type": "str"},
            {"name": "lookup_table", "label": "Lookup Table (JSON)", "type": "str"},
            {"name": "lookup_key", "label": "Lookup Key", "type": "str"},
            {"name": "lookup_value", "label": "Lookup Value", "type": "str"},
            {"name": "approximate_match", "label": "Approximate Match (True/False)", "type": "str"},
            {"name": "tolerance", "label": "Tolerance (numeric)", "type": "float"}
        ])
    def configureIndexMatch(self):
        self.openSimpleDialog("INDEX/MATCH", [
            {"name": "source_column", "label": "Source Column", "type": "str"},
            {"name": "lookup_table", "label": "Lookup Table (JSON)", "type": "str"},
            {"name": "lookup_key", "label": "Lookup Key", "type": "str"},
            {"name": "return_column", "label": "Return Column", "type": "str"},
            {"name": "approximate_match", "label": "Approximate Match (True/False)", "type": "str"},
            {"name": "tolerance", "label": "Tolerance (numeric)", "type": "float"}
        ])
    def configureTEXTJOIN(self):
        self.openSimpleDialog("TEXTJOIN", [
            {"name": "columns", "label": "Columns (comma separated)", "type": "str"},
            {"name": "delimiter", "label": "Delimiter", "type": "str"}
        ])

    def configureAdvancedLookupConditional(self):
        QMessageBox.information(self, "Advanced Lookup", "Advanced Lookup & Conditional configuration dialog goes here.")

    def configureAdvancedDateTime(self):
        QMessageBox.information(self, "Advanced Date/Time", "Advanced Date & Time configuration dialog goes here.")

    def configureAdvancedTextOps(self):
        QMessageBox.information(self, "Advanced Text Ops", "Advanced Text Operations configuration dialog goes here.")

    def configureAdvancedFinancial(self):
        QMessageBox.information(self, "Advanced Financial", "Advanced Financial Calculations configuration dialog goes here.")

    def configureAdvancedDataValidation(self):
        QMessageBox.information(self, "Advanced Data Validation", "Advanced Data Validation configuration dialog goes here.")

    def configureAdvancedSQL(self):
        QMessageBox.information(self, "Advanced SQL", "Advanced SQL Query configuration dialog goes here.")

    def openSimpleDialog(self, title, fields):
        dlg = GenericTransformationDialog(list(self.column_registry.values()), self.column_registry,
                                          param_defs=fields, dialog_title=f"Configure {title}")
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            params = dlg.getValues()
            if self.pipeline_loaded:
                self.addPipelineStep(title, params)
            else:
                self.state["transformation_params"][title] = params
            self.applyAllTransformationsAndRefresh()

    # ---------------------- Download/Preview Methods ----------------------
    def downloadData(self):
        if self.state["df"] is None:
            QMessageBox.warning(self, "No Data", "No data available for download.")
            return
        filename, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Data", "", "CSV Files (*.csv);;Text Files (*.txt);;Excel Files (*.xlsx)"
        )
        if filename:
            df = self.state["df"]
            friendly_df = df.copy()
            friendly_df.columns = [internal_to_friendly(col, self.master_registry) for col in friendly_df.columns]
            print("Saving file with columns:", friendly_df.columns.tolist())
            try:
                if selected_filter.startswith("CSV"):
                    friendly_df.to_csv(filename, index=False)
                elif selected_filter.startswith("Text"):
                    delimiter, ok = QInputDialog.getText(self, "Specify Delimiter", "Enter delimiter for text file:", text="\t")
                    if ok:
                        friendly_df.to_csv(filename, sep=delimiter, index=False)
                    else:
                        friendly_df.to_csv(filename, sep="\t", index=False)
                elif selected_filter.startswith("Excel"):
                    friendly_df.to_excel(filename, index=False)
                QMessageBox.information(self, "Success", "Data downloaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to download data: {str(e)}")

    def showTransformationSummary(self):
        if not self.state["transformation_summary"]:
            QMessageBox.information(self, "Summary", "No transformations have been applied.")
            return
        source_count = len(self.state["original_df"]) if self.state["original_df"] is not None else 0
        final_count = len(self.state["df"]) if self.state["df"] is not None else 0
        html_string = f"""
        <html>
        <head>
            <meta charset="utf-8" />
            <title>Transformation Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin:0; padding:20px; }}
                .summary {{ background-color: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                h2 {{ color: #2c3e50; margin-top: 0; }}
                .step {{ margin-bottom: 10px; padding: 5px; border-bottom: 1px solid #e1e5ec; }}
                .final {{ font-weight: bold; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="summary">
                <h2>Transformation Summary</h2>
        """
        for step in self.state["transformation_summary"]:
            html_string += f"<div class='step'><strong>{step['transformation']}</strong>: {step.get('initial_count','-')} → {step.get('new_count','-')}</div>"
        html_string += f"<div class='final'>Source Rows: {source_count} | Final Rows: {final_count}</div>"
        html_string += """
            </div>
        </body>
        </html>
        """
        dlg = QDialog(self)
        dlg.setObjectName("TransformationSummaryDialog")
        dlg.setWindowTitle("Transformation Summary")
        dlg.setMinimumSize(800, 600)
        layout = QVBoxLayout(dlg)
        if QWebEngineView is not None:
            view = QWebEngineView()
            view.setHtml(html_string)
            layout.addWidget(view)
        else:
            text_edit = QPlainTextEdit()
            text_edit.setPlainText("Transformation summary:\n" + "\n".join(
                [f"{step['transformation']}: {step.get('initial_count','-')} → {step.get('new_count','-')}" for step in self.state["transformation_summary"]]
            ))
            layout.addWidget(text_edit)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn)
        dlg.setLayout(layout)
        dlg.exec()

    def applyAllTransformationsAndRefresh(self):
        if self.state["original_df"] is None:
            self.updatePreview(pd.DataFrame())
            return
        df = self.state["original_df"].copy()
        if self.pipeline_loaded:
            transformations = {}
            for step in sorted(self.state["pipeline_steps"], key=lambda x: x["order"]):
                transformations[step["transformation"]] = step["parameters"]
        else:
            transformations = self.state["transformation_params"]
        config = {
            "Header Row": self.state["header_row"],
            "Filters": self.state["filter_conditions"],
            "Transformations": transformations,
            "Advanced Excel Functions": self.state["advanced_excel_config"],
        }
        try:
            df_transformed, summary_list = apply_transformations_with_summary(df, config)
            df_transformed = apply_advanced_excel_transformations(df_transformed, config["Advanced Excel Functions"])
            if "Join Dataframes" in config["Transformations"]:
                params = config["Transformations"]["Join Dataframes"]
                join_file = params.get("file_path")
                if join_file:
                    try:
                        ext = os.path.splitext(join_file)[1].lower()
                        if ext in [".csv", ".txt"]:
                            second_df = pd.read_csv(join_file)
                        elif ext in [".xlsx", ".xls"]:
                            second_df = pd.read_excel(join_file)
                        else:
                            second_df = pd.read_csv(join_file)
                        df_transformed = merge_join_dataframes(
                            [df_transformed, second_df],
                            params["join_type"],
                            params["base_key"],
                            [params["other_key"]],
                        )
                        summary_list.append({
                            "transformation": "Join Dataframes",
                            "sequence": 9999,
                            "initial_count": None,
                            "new_count": len(df_transformed),
                        })
                    except Exception as e:
                        QMessageBox.critical(self, "Join Error", f"Error joining data:\n{str(e)}")
            if "Union Dataframes" in config["Transformations"]:
                params = config["Transformations"]["Union Dataframes"]
                union_file = params.get("file_path")
                if union_file:
                    try:
                        ext = os.path.splitext(union_file)[1].lower()
                        if ext in [".csv", ".txt"]:
                            second_df = pd.read_csv(union_file)
                        elif ext in [".xlsx", ".xls"]:
                            second_df = pd.read_excel(union_file)
                        else:
                            second_df = pd.read_csv(union_file)
                        base_cols = list(df_transformed.columns)
                        second_cols = list(second_df.columns)
                        if len(base_cols) != len(second_cols):
                            msg = (
                                "Union requires dataframes to have the same number of columns.\n"
                                f"Base has {len(base_cols)} columns, second DF has {len(second_cols)}."
                            )
                            QMessageBox.warning(self, "Union Warning", msg)
                            raise ValueError(msg)
                        union_all = params.get("union_all", False)
                        df_transformed = union_dataframes([df_transformed, second_df], union_all)
                        summary_list.append({
                            "transformation": "Union Dataframes",
                            "sequence": 9999,
                            "initial_count": None,
                            "new_count": len(df_transformed),
                        })
                    except Exception as e:
                        QMessageBox.critical(self, "Union Error", f"Error unioning data:\n{str(e)}")
            self.state["df"] = df_transformed
            self.state["transformation_summary"] = summary_list
            existing_cols = set(df_transformed.columns)
            self.column_registry = {cid: self.master_registry[cid] for cid in self.master_registry if cid in existing_cols}
            display_df = df_transformed.copy()
            display_df.columns = [internal_to_friendly(col, self.master_registry) for col in display_df.columns]
            self.updatePreview(display_df)
            rc = len(df_transformed)
            self.status_bar.showMessage(f"Row count: {rc}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not apply transformations:\n{str(e)}")

    def openSimpleDialog(self, title, fields):
        dlg = GenericTransformationDialog(list(self.column_registry.values()), self.column_registry,
                                          param_defs=fields, dialog_title=f"Configure {title}")
        dlg.setMinimumSize(600, 400)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            params = dlg.getValues()
            if self.pipeline_loaded:
                self.addPipelineStep(title, params)
            else:
                self.state["transformation_params"][title] = params
            self.applyAllTransformationsAndRefresh()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataTransformerTool()
    window.show()
    sys.exit(app.exec())
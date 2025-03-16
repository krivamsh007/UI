import json
import datetime
from pyvis.network import Network
from ui_helpers import internal_to_friendly
from jinja2 import Template
from PyQt6.QtCore import QUrl, Qt, QSize, QPoint
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QToolBar, QSplitter,
    QFrame, QTextBrowser, QToolTip,
)
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction
from PyQt6.QtWebEngineCore import QWebEnginePage

# Define a custom QWebEnginePage that intercepts navigation requests.
class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None, node_click_handler=None):
        super().__init__(parent)
        self.node_click_handler = node_click_handler

    def acceptNavigationRequest(self, url: QUrl, _type, isMainFrame):
        url_str = url.toString()
        if url_str.startswith("detail:"):
            if self.node_click_handler:
                self.node_click_handler(url)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)

# Define a modern HTML template with enhanced styling and interactive features.
# A script is added at the end to listen for node clicks and redirect to a custom URL.
modern_template = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Data Transformation Lineage</title>
    <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/vis-network.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/vis-network.min.css" rel="stylesheet" type="text/css" />
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet" type="text/css" />
    <style>
      html, body { 
        width: 100%; 
        height: 100%; 
        margin: 0; 
        padding: 0; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      }
      #mynetwork { 
        width: 100%; 
        height: 800px; 
        border: 1px solid #ddd;
        background-color: #f9f9f9;
      }
      .controls {
        padding: 10px;
        background-color: #f0f0f0;
        border-bottom: 1px solid #ddd;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .controls button {
        padding: 5px 10px;
        margin: 0 5px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
      }
      .controls button:hover {
        background-color: #45a049;
      }
      .legend {
        position: absolute;
        bottom: 10px;
        right: 10px;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 10px;
        border-radius: 4px;
        border: 1px solid #ddd;
        z-index: 1000;
      }
      .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
      }
      .legend-color {
        width: 20px;
        height: 20px;
        margin-right: 10px;
        border-radius: 3px;
      }
      .tooltip {
        position: absolute;
        background-color: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 10px;
        border-radius: 4px;
        z-index: 1000;
        max-width: 300px;
        display: none;
      }
      .node-details {
        padding: 15px;
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        margin-top: 10px;
      }
      .search-box {
        padding: 5px;
        border-radius: 4px;
        border: 1px solid #ddd;
        width: 200px;
      }
      .badge {
        display: inline-block;
        padding: 3px 7px;
        font-size: 12px;
        font-weight: bold;
        line-height: 1;
        color: #fff;
        text-align: center;
        white-space: nowrap;
        vertical-align: middle;
        background-color: #777;
        border-radius: 10px;
        margin-left: 5px;
      }
    </style>
  </head>
  <body>
    <div class="controls">
      <div>
        <button onclick="network.fit()"><i class="fas fa-expand"></i> Fit View</button>
        <button onclick="toggleLegend()"><i class="fas fa-info-circle"></i> Legend</button>
        <input type="text" id="searchBox" class="search-box" placeholder="Search nodes..." onkeyup="searchNodes()">
      </div>
      <div>
        <button onclick="exportImage()"><i class="fas fa-download"></i> Export</button>
        <select id="layoutSelect" onchange="changeLayout()">
          <option value="hierarchical">Hierarchical Layout</option>
          <option value="physics">Force-Directed Layout</option>
        </select>
      </div>
    </div>
    
    <div id="mynetwork"></div>
    
    <div class="node-details" id="nodeDetails">
      <h3>Select a node to see details</h3>
      <p>Click on any node in the graph to view detailed information about that transformation step.</p>
    </div>
    
    <div class="legend" id="legend" style="display: none;">
      <h3>Legend</h3>
      <div class="legend-item">
        <div class="legend-color" style="background-color: #A9A9A9;"></div>
        <span>Source Data</span>
      </div>
      <div class="legend-item">
        <div class="legend-color" style="background-color: #ADD8E6;"></div>
        <span>Filter Operation</span>
      </div>
    </div>
    
    <script type="text/javascript">
      function toggleLegend() {
          var legend = document.getElementById("legend");
          legend.style.display = legend.style.display === "none" ? "block" : "none";
      }
      function searchNodes() {
          // Implement search functionality as needed
      }
      function exportImage() {
          // Implement export functionality as needed
      }
      function changeLayout() {
          // Implement layout change functionality as needed
      }
      
      // When a node is clicked, get its details and redirect to a custom URL.
      network.on("click", function(params) {
          if (params.nodes.length > 0) {
              var nodeId = params.nodes[0];
              var clickedNode = nodes.get(nodeId);
              window.location.href = "detail:" + encodeURIComponent(clickedNode.details);
          }
      });
    </script>
  </body>
</html>
"""

class ColumnTransformationTracker:
    """
    Tracks transformations applied to columns throughout the data processing pipeline.
    Maintains a history of operations and their effects on each column.
    """
    def __init__(self):
        self.column_history = {}  # Maps column_id to list of transformations
        self.derived_columns = {}  # Maps derived column_id to source column_id(s)
        
    def add_transformation(self, column_id, transformation_name, parameters, timestamp=None):
        if column_id not in self.column_history:
            self.column_history[column_id] = []
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.column_history[column_id].append({
            "transformation": transformation_name,
            "parameters": parameters,
            "timestamp": timestamp
        })
        
    def register_derived_column(self, new_column_id, source_column_ids, transformation_name, parameters):
        self.derived_columns[new_column_id] = {
            "sources": source_column_ids if isinstance(source_column_ids, list) else [source_column_ids],
            "transformation": transformation_name,
            "parameters": parameters,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if new_column_id not in self.column_history:
            self.column_history[new_column_id] = []
            
    def get_column_history(self, column_id):
        return self.column_history.get(column_id, [])
        
    def get_column_lineage(self, column_id):
        lineage = {
            "column_id": column_id,
            "history": self.get_column_history(column_id),
            "is_derived": column_id in self.derived_columns
        }
        if column_id in self.derived_columns:
            lineage["derivation"] = self.derived_columns[column_id]
            lineage["source_columns"] = []
            for source_id in self.derived_columns[column_id]["sources"]:
                lineage["source_columns"].append(self.get_column_lineage(source_id))
        return lineage
        
    def extract_from_config(self, config, registry):
        filters = config.get("Filters", [])
        for i, filt in enumerate(filters, start=1):
            if len(filt) >= 3:
                col = filt[0]
                self.add_transformation(
                    col, 
                    "Filter", 
                    {"condition": filt[1], "value": filt[2]},
                    timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
        transformations = config.get("Transformations", {})
        for trans_name, params in transformations.items():
            if "column" in params:
                input_col = params["column"]
                self.add_transformation(input_col, trans_name, params)
                if "new_column" in params:
                    new_col = params["new_column"]
                    self.register_derived_column(new_col, input_col, trans_name, params)
            elif "columns" in params:
                if isinstance(params["columns"], dict):
                    for col_id, col_details in params["columns"].items():
                        self.add_transformation(col_id, trans_name, col_details)
                        if "new_column" in col_details:
                            new_col = col_details["new_column"]
                            self.register_derived_column(new_col, col_id, trans_name, col_details)
                else:
                    affected = params["columns"]
                    for col in affected:
                        self.add_transformation(col, trans_name, params)
                    if "new_columns" in params:
                        new_cols = params["new_columns"]
                        for new_col in new_cols:
                            self.register_derived_column(new_col, affected, trans_name, params)
            elif "columns_to_dedup" in params:
                for col in params["columns_to_dedup"]:
                    self.add_transformation(col, trans_name, params)
        adv_excel = config.get("Advanced Excel Functions", {})
        for key, params in adv_excel.items():
            if "column" in params:
                input_col = params["column"]
                self.add_transformation(input_col, f"Excel_{key}", params)
                if "new_column" in params:
                    new_col = params["new_column"]
                    self.register_derived_column(new_col, input_col, f"Excel_{key}", params)
            elif "columns" in params:
                affected = params["columns"]
                for col in affected:
                    self.add_transformation(col, f"Excel_{key}", params)
        column_rules = config.get("Column Rules", {})
        for col_id, rules in column_rules.items():
            for rule_info in rules:
                rule_name = rule_info.get("rule", "Custom Rule")
                rule_details = rule_info.get("details", {})
                self.add_transformation(
                    col_id,
                    rule_name,
                    rule_details,
                    timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                if "new_column" in rule_details:
                    new_col = rule_details["new_column"]
                    self.register_derived_column(new_col, col_id, rule_name, rule_details)

def convert_tuple_keys_to_str(obj):
    """
    Recursively converts dictionary keys that are tuples into strings.
    Tuple keys are joined with "::" (e.g., ("col_2", "count") becomes "col_2::count").
    """
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            if isinstance(k, tuple):
                new_key = "::".join(str(x) for x in k)
            else:
                new_key = k
            new_obj[new_key] = convert_tuple_keys_to_str(v)
        return new_obj
    elif isinstance(obj, list):
        return [convert_tuple_keys_to_str(item) for item in obj]
    else:
        return obj

def generate_enhanced_lineage_graph(config, registry, column_tracker=None, view_type="hierarchical", focus_column=None):
    """
    Generate an enhanced lineage graph visualization.
    
    Args:
        config (dict): Configuration dictionary with transformation details.
            It can include extra keys:
              - "file_upload": { "file_name": ..., "upload_timestamp": ..., "file_size": ..., "file_format": ... }
              - "header_selection": { "header_row": ..., "original_columns": [...] }
        registry (dict): Column registry mapping internal IDs to friendly names.
        column_tracker (ColumnTransformationTracker, optional): Tracker for column transformations.
        view_type (str): Type of view ("hierarchical", "network", or "column_focused").
        focus_column (str, optional): Column ID to focus on for column-focused view.
    
    Returns:
        Network: PyVis Network object with the generated graph.
    """
    # Create a new column tracker if none provided.
    if column_tracker is None:
        column_tracker = ColumnTransformationTracker()
        column_tracker.extract_from_config(config, registry)
    
    # Initialize network with modern template.
    net = Network(height="800px", width="100%", directed=True)
    net.template = Template(modern_template)
    
    # --- Set Layout Options Based on View Type ---
    if view_type == "hierarchical":
        options = {
            "layout": {
                "hierarchical": {
                    "enabled": True,
                    "direction": "UD",
                    "sortMethod": "directed",
                    "nodeSpacing": 200,
                    "treeSpacing": 300,
                    "levelSeparation": 150
                }
            },
            "physics": {
                "hierarchicalRepulsion": {"nodeDistance": 150, "avoidOverlap": 1},
                "minVelocity": 0.75
            }
        }
    elif view_type == "network":
        options = {
            "layout": {"hierarchical": {"enabled": False}},
            "physics": {
                "enabled": True,
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 100,
                    "springConstant": 0.08
                },
                "solver": "forceAtlas2Based",
                "stabilization": {"iterations": 100}
            }
        }
    elif view_type == "column_focused":
        # Force a strict sequential pipeline (left-to-right).
        options = {
            "layout": {
                "hierarchical": {
                    "enabled": True,
                    "direction": "LR",
                    "sortMethod": "directed",
                    "nodeSpacing": 250,
                    "treeSpacing": 0,
                    "levelSeparation": 150
                }
            },
            "physics": {"enabled": False}
        }
    common_options = {
        "interaction": {"hover": True, "tooltipDelay": 200, "zoomView": True, "dragView": True},
        "edges": {
            "smooth": {"type": "cubicBezier", "forceDirection": "vertical" if view_type == "hierarchical" else "horizontal" if view_type == "column_focused" else "none"},
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.5}},
            "color": {"color": "#2B7CE9", "highlight": "#FFA500", "hover": "#2B7CE9"}
        },
        "nodes": {
            "shape": "box",
            "font": {"face": "Segoe UI", "size": 14},
            "margin": 10,
            "shadow": {"enabled": True, "size": 3, "x": 3, "y": 3}
        }
    }
    options.update(common_options)
    net.set_options(json.dumps(options))
    
    # --- Add Initial Events: File Upload and Header Selection ---
    current_node = None

    # File Upload Node (if provided)
    file_upload = config.get("file_upload", None)
    if file_upload:
        upload_details = f"""
        <h3>File Upload</h3>
        <div><strong>File Name:</strong> {file_upload.get("file_name", "Unknown")}</div>
        <div><strong>Uploaded At:</strong> {file_upload.get("upload_timestamp", "Unknown")}</div>
        <div><strong>File Size:</strong> {file_upload.get("file_size", "Unknown")}</div>
        <div><strong>File Format:</strong> {file_upload.get("file_format", "Unknown")}</div>
        """
        upload_label = f"Upload: {file_upload.get('file_name', 'Unknown')}"
        net.add_node(upload_label,
                     label=upload_label,
                     title="File Upload",
                     shape="box",
                     color="#ADD8E6",
                     details=upload_details,
                     font={"size": 16, "face": "Segoe UI", "bold": True})
        current_node = upload_label

    # Header Selection Node (if provided)
    header_sel = config.get("header_selection", None)
    if header_sel:
        header_details = f"""
        <h3>Header Selection</h3>
        <div><strong>Header Row:</strong> {header_sel.get("header_row", "Not specified")}</div>
        <div><strong>Original Columns:</strong> {", ".join(header_sel.get("original_columns", []))}</div>
        """
        header_label = f"Header: Row {header_sel.get('header_row', 'N/A')}"
        net.add_node(header_label,
                     label=header_label,
                     title="Header Selection",
                     shape="box",
                     color="#FFD700",
                     details=header_details,
                     font={"size": 16, "face": "Segoe UI", "bold": True})
        if current_node:
            net.add_edge(current_node,
                         header_label,
                         title="Header Selected",
                         width=3,
                         color={"color": "#2B7CE9", "highlight": "#FFA500"})
        current_node = header_label

    # --- Source Dataset Node ---
    file_name = config.get("file_name", "Source Dataset")
    source_label = f"Dataset Loaded: {file_name}"
    
    # Track column nodes for direct connections in column-focused view.
    column_nodes = {}
    column_details = []
    for k in registry:
        friendly_name = internal_to_friendly(k, registry)
        column_history = column_tracker.get_column_history(k)
        transformation_count = len(column_history)
        badge = f'<span class="badge" style="background-color: #4CAF50;">{transformation_count}</span>' if transformation_count > 0 else ""
        column_details.append(f"<li>{friendly_name} {badge}</li>")
        
        # Create individual column nodes (if needed).
        if view_type in ["column_focused", "network"]:
            if focus_column is None or k == focus_column:
                column_node_id = f"Column: {friendly_name}"
                column_nodes[k] = column_node_id
                column_node_details = f"""
                <h3>Column: {friendly_name}</h3>
                <div style="margin-top: 10px;">
                    <p><strong>Internal ID:</strong> {k}</p>
                    <p><strong>Transformation Count:</strong> {transformation_count}</p>
                    <p><strong>Is Derived:</strong> {'Yes' if k in column_tracker.derived_columns else 'No'}</p>
                </div>
                """
                if transformation_count > 0:
                    column_node_details += """
                    <div style="margin-top: 15px;">
                        <h4>Transformation History:</h4>
                        <ul>
                    """
                    for entry in column_history:
                        column_node_details += f"<li><strong>{entry['transformation']}</strong> at {entry['timestamp']}</li>"
                    column_node_details += """
                        </ul>
                    </div>
                    """
                node_color = "#FFD700" if k == focus_column else "#FFA07A"
                border_width = 3 if k == focus_column else 1
                font_size = 16 if k == focus_column else 14
                net.add_node(column_node_id,
                             label=friendly_name,
                             title=f"Column: {friendly_name}",
                             shape="ellipse" if view_type == "network" else "box",
                             color=node_color,
                             borderWidth=border_width,
                             details=column_node_details,
                             font={"size": font_size, "face": "Segoe UI", "bold": k == focus_column})
    
    source_columns = "<ul>" + "\n".join(column_details) + "</ul>"
    source_details = f"""
    <h3>Source Dataset: {file_name}</h3>
    <div style="margin-top: 10px;">
        <h4>Columns:</h4>
        {source_columns}
    </div>
    <div style="margin-top: 10px;">
        <p><strong>Total Columns:</strong> {len(registry)}</p>
    </div>
    """
    source_title = f"File: {file_name}<br>Columns: {len(registry)}"
    net.add_node(source_label,
                 label=source_label,
                 title=source_title,
                 shape="box",
                 color="#A9A9A9",
                 details=source_details,
                 font={"size": 16, "face": "Segoe UI", "bold": True})
    if current_node:
        net.add_edge(current_node,
                     source_label,
                     title="Data Loaded",
                     width=3,
                     color={"color": "#2B7CE9", "highlight": "#FFA500"})
    current_node = source_label

    # For column-focused/network views, connect source to each column node.
    if view_type in ["column_focused", "network"] and column_nodes:
        for col_id, col_node_id in column_nodes.items():
            if view_type == "column_focused":
                edge_width = 3
                edge_color = {"color": "#FF4500", "highlight": "#FF6347"}
            else:
                edge_width = 2.5 if view_type == "column_focused" else 1.5
                edge_color = {"color": "#FF5733" if focus_column == col_id else "#A9A9A9", "highlight": "#FFA500"}
            net.add_edge(source_label,
                         col_node_id,
                         title="Contains Column",
                         width=edge_width,
                         color=edge_color)
    
    # --- Process Filters ---
    filters = config.get("Filters", [])
    for i, filt in enumerate(filters, start=1):
        col, cond, val = filt[0], filt[1], filt[2]
        metrics = filt[3] if len(filt) > 3 else {}
        friendly_col = internal_to_friendly(col, registry)
        rows_before = metrics.get('rows_before', '-')
        rows_after = metrics.get('rows_after', '-')
        row_reduction = ""
        if rows_before != '-' and rows_after != '-' and rows_before > rows_after:
            reduction_pct = ((rows_before - rows_after) / rows_before) * 100
            row_reduction = f"<span style='color: #FF5733;'>(-{reduction_pct:.1f}%)</span>"
        metric_info = f"Rows Before: {rows_before}, Rows After: {rows_after} {row_reduction}"
        filter_details_html = f"""
        <h3>Filter {i}: {friendly_col}</h3>
        <div style="margin-top: 10px;">
            <p><strong>Condition:</strong> {cond} {val}</p>
            <p><strong>Column:</strong> {friendly_col}</p>
            <p><strong>Impact:</strong> {metric_info}</p>
        </div>
        <div style="margin-top: 10px; padding: 10px; background-color: #f8f8f8; border-radius: 4px;">
            <h4>Column History:</h4>
            <ul>
        """
        column_history = column_tracker.get_column_history(col)
        for entry in column_history:
            filter_details_html += f"<li><strong>{entry['transformation']}</strong> at {entry['timestamp']}</li>"
        filter_details_html += """
            </ul>
        </div>
        """
        filter_tooltip = f"Filter {i}<br>{friendly_col}: {cond} {val}<br>{metric_info}"
        filter_node = f"Filter {i} - {friendly_col}"
        net.add_node(filter_node,
                     label=f"Filter {i}",
                     title=filter_tooltip,
                     shape="diamond",
                     color="#ADD8E6",
                     details=filter_details_html,
                     font={"size": 14, "face": "Segoe UI"})
        if view_type == "hierarchical":
            net.add_edge(current_node,
                         filter_node,
                         title="Apply Filter",
                         width=2,
                         color={"color": "#2B7CE9", "highlight": "#FFA500"})
            current_node = filter_node
        else:
            if view_type in ["column_focused", "network"] and col in column_nodes:
                net.add_edge(column_nodes[col],
                             filter_node,
                             title=f"Filter: {cond} {val}",
                             width=2,
                             color={"color": "#2B7CE9", "highlight": "#FFA500"})
                if view_type == "column_focused" and (focus_column is None or col == focus_column):
                    current_node = filter_node
            else:
                net.add_edge(current_node,
                             filter_node,
                             title="Apply Filter",
                             width=2,
                             color={"color": "#2B7CE9", "highlight": "#FFA500"})
                current_node = filter_node

    # --- Process Generic Transformations ---
    transformations = config.get("Transformations", {})
    sorted_trans = sorted(transformations.items(), key=lambda kv: kv[1].get("sequence", 9999))
    for trans_name, params in sorted_trans:
        # Convert tuple keys in params before dumping to JSON.
        serializable_params = convert_tuple_keys_to_str(params)
        trans_details = f"Transformation: {trans_name}\nParameters:\n{json.dumps(serializable_params, indent=2)}"
        trans_details_html = f"""
        <h3>Transformation: {trans_name}</h3>
        <div style="margin-top: 10px;">
        """
        affected_columns = []
        output_columns = []
        if "column" in params:
            input_col = params["column"]
            friendly_input = internal_to_friendly(input_col, registry)
            affected_columns.append(input_col)
            trans_details_html += f"<p><strong>Input Column:</strong> {friendly_input}</p>"
            if "new_column" in params:
                new_col = params["new_column"]
                friendly_new = internal_to_friendly(new_col, registry) if new_col in registry else new_col
                output_columns.append(new_col)
                trans_details_html += f"<p><strong>Output Column:</strong> {friendly_new}</p>"
        elif "columns" in params:
            if isinstance(params["columns"], dict):
                affected_cols = list(params["columns"].keys())
                affected_columns.extend(affected_cols)
                friendly_list = [internal_to_friendly(c, registry) for c in affected_cols]
                trans_details_html += f"<p><strong>Affected Columns:</strong> {', '.join(friendly_list)}</p>"
                trans_details_html += """
                <div style="margin-top: 10px;">
                    <h4>Column Operations:</h4>
                    <ul>
                """
                for col_id, col_details in params["columns"].items():
                    friendly_name = internal_to_friendly(col_id, registry)
                    if "operations" in col_details:
                        operations = ", ".join(col_details["operations"])
                        trans_details_html += f"<li><strong>{friendly_name}:</strong> {operations}</li>"
                    elif "old_sub" in col_details and "new_sub" in col_details:
                        trans_details_html += f"<li><strong>{friendly_name}:</strong> Replace '{col_details['old_sub']}' with '{col_details['new_sub']}'</li>"
                    else:
                        trans_details_html += f"<li><strong>{friendly_name}:</strong> Custom operation</li>"
                trans_details_html += """
                    </ul>
                </div>
                """
            else:
                affected = params["columns"]
                affected_columns.extend(affected)
                if set(affected) == set(registry.keys()):
                    trans_details_html += "<p><strong>Affected Columns:</strong> All columns</p>"
                else:
                    friendly_list = [internal_to_friendly(c, registry) for c in affected]
                    trans_details_html += f"<p><strong>Affected Columns:</strong> {', '.join(friendly_list)}</p>"
        elif "columns_to_dedup" in params:
            affected = params["columns_to_dedup"]
            affected_columns.extend(affected)
            friendly_list = [internal_to_friendly(c, registry) for c in affected]
            trans_details_html += f"<p><strong>Columns to Deduplicate:</strong> {', '.join(friendly_list)}</p>"
            trans_details_html += f"<p><strong>Keep:</strong> {params.get('keep', 'first')}</p>"
        else:
            affected_columns.extend(list(registry.keys()))
            trans_details_html += "<p><strong>Affected Columns:</strong> All columns</p>"
        
        if "metrics" in params:
            metrics = params["metrics"]
            rows_before = metrics.get('rows_before', '-')
            rows_after = metrics.get('rows_after', '-')
            change_html = ""
            if rows_before != '-' and rows_after != '-' and rows_before != rows_after:
                change_pct = ((rows_after - rows_before) / rows_before) * 100
                color = "#4CAF50" if change_pct >= 0 else "#FF5733"
                sign = "+" if change_pct >= 0 else ""
                change_html = f"<span style='color: {color};'>({sign}{change_pct:.1f}%)</span>"
            trans_details_html += f"""
            <div style="margin-top: 10px; padding: 8px; background-color: #f0f8ff; border-radius: 4px;">
                <p><strong>Data Impact:</strong></p>
                <p>Rows Before: {rows_before}</p>
                <p>Rows After: {rows_after} {change_html}</p>
            </div>
            """
        if "sample_data" in params:
            sample_data = params['sample_data']
            trans_details_html += f"""
            <div style="margin-top: 10px;">
                <h4>Data Sample:</h4>
                <pre style="background-color: #f8f8f8; padding: 10px; border-radius: 4px; overflow: auto; max-height: 200px;">{sample_data}</pre>
            </div>
            """
        if "timestamp" in params:
            trans_details_html += f"<p><strong>Timestamp:</strong> {params['timestamp']}</p>"
        
        trans_details_html += """
        <div style="margin-top: 15px;">
            <h4>Column Transformations:</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Column</th>
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Transformation Count</th>
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Latest Transformation</th>
                </tr>
        """
        for col in affected_columns:
            friendly_name = internal_to_friendly(col, registry)
            history = column_tracker.get_column_history(col)
            count = len(history)
            latest = history[-1]['transformation'] if history else "None"
            trans_details_html += f"""
                <tr>
                    <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{friendly_name}</td>
                    <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{count}</td>
                    <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{latest}</td>
                </tr>
            """
        trans_details_html += """
            </table>
        </div>
        """
        trans_details_html += "</div>"
        
        detailed_label = trans_name
        if trans_name == "Replace Substring" and "columns" in params and isinstance(params["columns"], dict):
            for col_id, col_details in params["columns"].items():
                if "old_sub" in col_details and "new_sub" in col_details:
                    friendly_name = internal_to_friendly(col_id, registry)
                    detailed_label = f"Replace '{col_details['old_sub']}'\nwith '{col_details['new_sub']}'\nin {friendly_name}"
                    break
        elif trans_name == "Trim" and "columns" in params and isinstance(params["columns"], dict):
            col_ops = []
            for col_id, col_details in params["columns"].items():
                if "operations" in col_details:
                    friendly_name = internal_to_friendly(col_id, registry)
                    ops = ", ".join(col_details["operations"])
                    col_ops.append(f"{friendly_name}: {ops}")
            if col_ops:
                detailed_label = f"Trim\n{col_ops[0]}"
                if len(col_ops) > 1:
                    detailed_label += f"\n(+{len(col_ops)-1} more)"
        elif trans_name == "Remove Duplicates" and "columns_to_dedup" in params:
            cols = params["columns_to_dedup"]
            friendly_cols = [internal_to_friendly(c, registry) for c in cols]
            keep = params.get("keep", "first")
            if len(friendly_cols) <= 2:
                cols_str = ", ".join(friendly_cols)
                detailed_label = f"Remove Duplicates\nColumns: {cols_str}\nKeep: {keep}"
            else:
                detailed_label = f"Remove Duplicates\nColumns: {len(friendly_cols)} cols\nKeep: {keep}"
        
        tooltip_text = f"{trans_name}"
        if "column" in params:
            tooltip_text += f"<br>Column: {internal_to_friendly(params['column'], registry)}"
        elif "columns" in params and isinstance(params["columns"], dict):
            friendly_list = [internal_to_friendly(c, registry) for c in params["columns"].keys()]
            tooltip_text += f"<br>Columns: {', '.join(friendly_list)}"
            for col_id, col_details in params["columns"].items():
                friendly_name = internal_to_friendly(col_id, registry)
                if "operations" in col_details:
                    ops = ", ".join(col_details["operations"])
                    tooltip_text += f"<br>{friendly_name}: {ops}"
                elif "old_sub" in col_details and "new_sub" in col_details:
                    tooltip_text += f"<br>{friendly_name}: Replace '{col_details['old_sub']}' with '{col_details['new_sub']}'"
        elif "columns" in params and len(params["columns"]) <= 3:
            friendly_list = [internal_to_friendly(c, registry) for c in params["columns"]]
            tooltip_text += f"<br>Columns: {', '.join(friendly_list)}"
        elif "columns_to_dedup" in params:
            friendly_list = [internal_to_friendly(c, registry) for c in params["columns_to_dedup"]]
            tooltip_text += f"<br>Columns to deduplicate: {', '.join(friendly_list)}"
            tooltip_text += f"<br>Keep: {params.get('keep', 'first')}"
        
        trans_node = f"Transform {trans_name}"
        node_color = "#90EE90"  # Light green for transformations
        net.add_node(trans_node,
                     label=detailed_label,
                     title=tooltip_text,
                     shape="ellipse",
                     color=node_color,
                     details=trans_details_html,
                     font={"size": 14, "face": "Segoe UI"})
        if view_type == "hierarchical":
            edge_title = "Apply Transformation"
            if "column" in params:
                edge_title = f"Transform {internal_to_friendly(params['column'], registry)}"
            net.add_edge(current_node,
                         trans_node,
                         title=edge_title,
                         width=2,
                         color={"color": "#2B7CE9", "highlight": "#FFA500"})
            current_node = trans_node
        else:
            if view_type in ["column_focused", "network"]:
                connected_to_column = False
                if "column" in params and params["column"] in column_nodes:
                    input_col = params["column"]
                    net.add_edge(column_nodes[input_col],
                                 trans_node,
                                 title=f"Input: {internal_to_friendly(input_col, registry)}" if "new_column" not in params 
                                       else f"Transform {internal_to_friendly(input_col, registry)} → {internal_to_friendly(params['new_column'], registry)}",
                                 width=2,
                                 color={"color": "#2B7CE9", "highlight": "#FFA500"})
                    connected_to_column = True
                    if "new_column" in params and params["new_column"] in column_nodes:
                        output_col = params["new_column"]
                        net.add_edge(trans_node,
                                     column_nodes[output_col],
                                     title=f"Output: {internal_to_friendly(output_col, registry)}",
                                     width=2,
                                     color={"color": "#4CAF50", "highlight": "#FFA500"})
                elif "columns" in params:
                    if isinstance(params["columns"], dict):
                        for col_id, col_details in params["columns"].items():
                            if col_id in column_nodes:
                                net.add_edge(column_nodes[col_id],
                                             trans_node,
                                             title=f"Transform {internal_to_friendly(col_id, registry)}",
                                             width=2,
                                             color={"color": "#2B7CE9", "highlight": "#FFA500"})
                                connected_to_column = True
                    else:
                        for col in params["columns"]:
                            if col in column_nodes:
                                net.add_edge(column_nodes[col],
                                             trans_node,
                                             title=f"Transform {internal_to_friendly(col, registry)}",
                                             width=2,
                                             color={"color": "#2B7CE9", "highlight": "#FFA500"})
                                connected_to_column = True
                elif "columns_to_dedup" in params:
                    for col in params["columns_to_dedup"]:
                        if col in column_nodes:
                            net.add_edge(column_nodes[col],
                                         trans_node,
                                         title=f"Deduplicate {internal_to_friendly(col, registry)} (Keep: {params.get('keep', 'first')})",
                                         width=2,
                                         color={"color": "#2B7CE9", "highlight": "#FFA500"})
                            connected_to_column = True
                    if "new_columns" in params:
                        for new_col in params["new_columns"]:
                            if new_col in column_nodes:
                                net.add_edge(trans_node,
                                             column_nodes[new_col],
                                             title=f"Output: {internal_to_friendly(new_col, registry)}",
                                             width=2,
                                             color={"color": "#4CAF50", "highlight": "#FFA500"})
                if view_type == "column_focused" and connected_to_column:
                    if focus_column is not None:
                        if (("column" in params and params["column"] == focus_column) or 
                            ("columns" in params and isinstance(params["columns"], dict) and focus_column in params["columns"]) or
                            ("columns" in params and not isinstance(params["columns"], dict) and focus_column in params["columns"]) or
                            ("columns_to_dedup" in params and focus_column in params["columns_to_dedup"])):
                            current_node = trans_node
                    else:
                        current_node = trans_node
                if not connected_to_column:
                    edge_title = "Apply Transformation"
                    net.add_edge(current_node,
                                 trans_node,
                                 title=edge_title,
                                 width=2,
                                 color={"color": "#2B7CE9", "highlight": "#FFA500"})
                    current_node = trans_node
            else:
                edge_title = "Apply Transformation"
                if "column" in params:
                    edge_title = f"Transform {internal_to_friendly(params['column'], registry)}"
                net.add_edge(current_node,
                             trans_node,
                             title=edge_title,
                             width=2,
                             color={"color": "#2B7CE9", "highlight": "#FFA500"})
                current_node = trans_node

    # --- Process Excel Functions ---
    adv_excel = config.get("Advanced Excel Functions", {})
    if adv_excel:
        for key, params in adv_excel.items():
            serializable_params = convert_tuple_keys_to_str(params)
            excel_details = f"Excel Function: {key}\nParameters:\n{json.dumps(serializable_params, indent=2)}"
            excel_details_html = f"""
            <h3>Excel Function: {key}</h3>
            <div style="margin-top: 10px;">
            """
            affected_columns = []
            output_columns = []
            if "column" in params:
                input_col = params["column"]
                friendly = internal_to_friendly(input_col, registry)
                affected_columns.append(input_col)
                excel_details_html += f"<p><strong>Input Column:</strong> {friendly}</p>"
                if "new_column" in params:
                    new_col = params["new_column"]
                    friendly_new = internal_to_friendly(new_col, registry) if new_col in registry else new_col
                    output_columns.append(new_col)
                    excel_details_html += f"<p><strong>Output Column:</strong> {friendly_new}</p>"
            elif "columns" in params:
                affected = params["columns"]
                affected_columns.extend(affected)
                if set(affected) == set(registry.keys()):
                    excel_details_html += "<p><strong>Affected Columns:</strong> All columns</p>"
                else:
                    friendly_list = [internal_to_friendly(c, registry) for c in affected]
                    excel_details_html += f"<p><strong>Affected Columns:</strong> {', '.join(friendly_list)}</p>"
            if "timestamp" in params:
                excel_details_html += f"<p><strong>Timestamp:</strong> {params['timestamp']}</p>"
            if "sample_data" in params:
                sample_data = params['sample_data']
                excel_details_html += f"""
                <div style="margin-top: 10px;">
                    <h4>Data Sample:</h4>
                    <pre style="background-color: #f8f8f8; padding: 10px; border-radius: 4px; overflow: auto; max-height: 200px;">{sample_data}</pre>
                </div>
                """
            excel_details_html += """
            <div style="margin-top: 15px;">
                <h4>Column Transformations:</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Column</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Transformation Count</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Latest Transformation</th>
                    </tr>
            """
            for col in affected_columns:
                friendly_name = internal_to_friendly(col, registry)
                history = column_tracker.get_column_history(col)
                count = len(history)
                latest = history[-1]['transformation'] if history else "None"
                excel_details_html += f"""
                    <tr>
                        <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{friendly_name}</td>
                        <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{count}</td>
                        <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{latest}</td>
                    </tr>
                """
            excel_details_html += """
                </table>
            </div>
            """
            excel_details_html += "</div>"
            tooltip_text = f"Excel: {key}"
            if "column" in params:
                tooltip_text += f"<br>Column: {internal_to_friendly(params['column'], registry)}"
            excel_node = f"Excel {key}"
            node_color = "#FFD700"
            net.add_node(excel_node,
                         label=f"Excel: {key}",
                         title=tooltip_text,
                         shape="box",
                         color=node_color,
                         details=excel_details_html,
                         font={"size": 14, "face": "Segoe UI"})
            if view_type == "hierarchical":
                edge_title = "Apply Excel Function"
                if "column" in params:
                    edge_title = f"Excel on {internal_to_friendly(params['column'], registry)}"
                net.add_edge(current_node,
                             excel_node,
                             title=edge_title,
                             width=2,
                             color={"color": "#2B7CE9", "highlight": "#FFA500"})
                current_node = excel_node
            else:
                if view_type in ["column_focused", "network"]:
                    connected_to_column = False
                    if "column" in params and params["column"] in column_nodes:
                        input_col = params["column"]
                        net.add_edge(column_nodes[input_col],
                                     excel_node,
                                     title=f"Input to Excel {key}",
                                     width=2,
                                     color={"color": "#2B7CE9", "highlight": "#FFA500"})
                        connected_to_column = True
                        if "new_column" in params and params["new_column"] in column_nodes:
                            output_col = params["new_column"]
                            net.add_edge(excel_node,
                                         column_nodes[output_col],
                                         title=f"Output of Excel {key}",
                                         width=2,
                                         color={"color": "#4CAF50", "highlight": "#FFA500"})
                    elif "columns" in params:
                        for col in params["columns"]:
                            if col in column_nodes:
                                net.add_edge(column_nodes[col],
                                             excel_node,
                                             title=f"Input to Excel {key}",
                                             width=2,
                                             color={"color": "#2B7CE9", "highlight": "#FFA500"})
                                connected_to_column = True
                    if view_type == "column_focused" and connected_to_column and (focus_column is None or 
                       (("column" in params and params["column"] == focus_column) or 
                        ("columns" in params and focus_column in params["columns"]))):
                        current_node = excel_node
                    if not connected_to_column:
                        edge_title = "Apply Excel Function"
                        net.add_edge(current_node,
                                     excel_node,
                                     title=edge_title,
                                     width=2,
                                     color={"color": "#2B7CE9", "highlight": "#FFA500"})
                        current_node = excel_node
                else:
                    edge_title = "Apply Excel Function"
                    if "column" in params:
                        edge_title = f"Excel on {internal_to_friendly(params['column'], registry)}"
                    net.add_edge(current_node,
                                 excel_node,
                                 title=edge_title,
                                 width=2,
                                 color={"color": "#2B7CE9", "highlight": "#FFA500"})
                    current_node = excel_node

    # --- Final Output Node ---
    final_node = "Final Dataset"
    final_details_html = f"""
    <h3>Final Transformed Dataset</h3>
    <div style="margin-top: 10px;">
        <p><strong>Total Columns:</strong> {len(registry)}</p>
        <p><strong>Transformations Applied:</strong> {len(filters) + len(transformations) + len(adv_excel)}</p>
    </div>
    <div style="margin-top: 15px;">
        <h4>Column Summary:</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Column</th>
                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Transformation Count</th>
                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Is Derived</th>
            </tr>
    """
    for col_id in registry:
        friendly_name = internal_to_friendly(col_id, registry)
        history = column_tracker.get_column_history(col_id)
        count = len(history)
        is_derived = "Yes" if col_id in column_tracker.derived_columns else "No"
        final_details_html += f"""
            <tr>
                <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{friendly_name}</td>
                <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{count}</td>
                <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{is_derived}</td>
            </tr>
        """
    final_details_html += """
        </table>
    </div>
    """
    final_title = "Transformed Data Ready for Use"
    net.add_node(final_node,
                 label=final_node,
                 title=final_title,
                 shape="box",
                 color="#FFFF00",
                 details=final_details_html,
                 font={"size": 16, "face": "Segoe UI", "bold": True})
    if view_type == "hierarchical":
        net.add_edge(current_node,
                     final_node,
                     title="Output Data",
                     width=3,
                     color={"color": "#2B7CE9", "highlight": "#FFA500"})
    elif view_type in ["column_focused", "network"]:
        for col_id, col_node_id in column_nodes.items():
            if len(column_tracker.get_column_history(col_id)) > 0:
                net.add_edge(col_node_id,
                             final_node,
                             title="Final Output",
                             width=2,
                             color={"color": "#4CAF50", "highlight": "#FFA500"})
        net.add_edge(current_node,
                     final_node,
                     title="Output Data",
                     width=3,
                     color={"color": "#2B7CE9", "highlight": "#FFA500"})
    else:
        net.add_edge(current_node,
                     final_node,
                     title="Output Data",
                     width=3,
                     color={"color": "#2B7CE9", "highlight": "#FFA500"})
    
    return net

class EnhancedLineageDialog(QDialog):
    """
    Enhanced dialog for displaying data lineage with interactive features and column-level information.
    """
    def __init__(self, config, registry, parent=None):
        super().__init__(parent)
        self.config = config
        self.registry = registry
        self.column_tracker = ColumnTransformationTracker()
        self.column_tracker.extract_from_config(config, registry)
        self.setWindowTitle("Enhanced Data Lineage")
        self.resize(1200, 900)
        self.initUI()
        
    def initUI(self):
        main_layout = QVBoxLayout(self)
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        help_action = QAction("Help", self)
        help_action.triggered.connect(self.showHelp)
        toolbar.addAction(help_action)
        export_action = QAction("Export", self)
        export_action.triggered.connect(self.exportLineage)
        toolbar.addAction(export_action)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("View Options:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Hierarchical View", "Network View", "Column-Focused View"])
        self.view_combo.currentIndexChanged.connect(self.changeView)
        toolbar.addWidget(self.view_combo)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Filter by Column:"))
        self.column_combo = QComboBox()
        self.column_combo.addItem("All Columns")
        for col_id in self.registry:
            friendly_name = internal_to_friendly(col_id, self.registry)
            self.column_combo.addItem(friendly_name)
        self.column_combo.currentIndexChanged.connect(self.filterByColumn)
        toolbar.addWidget(self.column_combo)
        main_layout.addWidget(toolbar)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.web_view = QWebEngineView()
        custom_page = CustomWebEnginePage(self.web_view, self.handleNodeClick)
        self.web_view.setPage(custom_page)
        details_frame = QFrame()
        details_frame.setFrameShape(QFrame.Shape.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        details_header = QLabel("Column Details")
        details_header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        details_layout.addWidget(details_header)
        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(True)
        details_layout.addWidget(self.details_browser)
        column_select_layout = QHBoxLayout()
        column_select_layout.addWidget(QLabel("Select Column:"))
        self.details_column_combo = QComboBox()
        for col_id in self.registry:
            friendly_name = internal_to_friendly(col_id, self.registry)
            self.details_column_combo.addItem(friendly_name)
        self.details_column_combo.currentIndexChanged.connect(self.updateColumnDetails)
        column_select_layout.addWidget(self.details_column_combo)
        details_layout.addLayout(column_select_layout)
        splitter.addWidget(self.web_view)
        splitter.addWidget(details_frame)
        splitter.setSizes([700, 300])
        main_layout.addWidget(splitter)
        self.generateLineageGraph()
        if self.details_column_combo.count() > 0:
            self.updateColumnDetails(0)
    
    def handleNodeClick(self, url):
        url_str = url.toString()
        if url_str.startswith("detail:"):
            import urllib.parse
            details_html = urllib.parse.unquote(url_str[7:])
            self.details_browser.setHtml(details_html)
    
    def generateLineageGraph(self, view_type="hierarchical", focus_column=None):
        net = generate_enhanced_lineage_graph(
            self.config, 
            self.registry, 
            self.column_tracker,
            view_type=view_type,
            focus_column=focus_column
        )
        html_content = net.generate_html()
        self.web_view.setHtml(html_content, QUrl("about:blank"))
    
    def updateColumnDetails(self, index):
        if index < 0 or self.details_column_combo.count() == 0:
            return
        friendly_name = self.details_column_combo.currentText()
        col_id = None
        for k, v in self.registry.items():
            if internal_to_friendly(k, self.registry) == friendly_name:
                col_id = k
                break
        if col_id is None:
            return
        lineage = self.column_tracker.get_column_lineage(col_id)
        html = f"""
        <h2 style="color: #2B7CE9;">{friendly_name}</h2>
        <div style="margin-top: 10px;">
            <p><strong>Internal ID:</strong> {col_id}</p>
            <p><strong>Transformation Count:</strong> {len(lineage['history'])}</p>
            <p><strong>Is Derived:</strong> {'Yes' if lineage['is_derived'] else 'No'}</p>
        </div>
        """
        if lineage['is_derived']:
            derivation = lineage['derivation']
            source_cols = [internal_to_friendly(src, self.registry) for src in derivation['sources']]
            html += f"""
            <div style="margin-top: 15px; padding: 10px; background-color: #f0f8ff; border-radius: 4px;">
                <h3>Derivation Information</h3>
                <p><strong>Transformation:</strong> {derivation['transformation']}</p>
                <p><strong>Source Columns:</strong> {', '.join(source_cols)}</p>
                <p><strong>Created At:</strong> {derivation['created_at']}</p>
            </div>
            """
        html += """
        <div style="margin-top: 15px;">
            <h3>Transformation History</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Transformation</th>
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Timestamp</th>
                </tr>
        """
        for entry in lineage['history']:
            html += f"""
                <tr>
                    <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{entry['transformation']}</td>
                    <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{entry['timestamp']}</td>
                </tr>
            """
        html += """
            </table>
        </div>
        """
        self.details_browser.setHtml(html)
    
    def changeView(self, index):
        if index == 0:
            self.generateLineageGraph(view_type="hierarchical")
        elif index == 1:
            self.generateLineageGraph(view_type="network")
        elif index == 2:
            if self.column_combo.currentIndex() > 0:
                self.filterByColumn(self.column_combo.currentIndex())
            else:
                self.generateLineageGraph(view_type="column_focused")
    
    def filterByColumn(self, index):
        if index == 0:
            self.generateLineageGraph(view_type="hierarchical")
        else:
            friendly_name = self.column_combo.itemText(index)
            col_id = None
            for k, v in self.registry.items():
                if internal_to_friendly(k, self.registry) == friendly_name:
                    col_id = k
                    break
            if col_id is None:
                return
            self.generateLineageGraph(view_type="column_focused", focus_column=col_id)
    
    def showHelp(self):
        help_text = """
        <h2>Data Lineage Visualization Help</h2>
        <p>This tool visualizes the transformations applied to your data throughout the processing pipeline.</p>
        <h3>Navigation:</h3>
        <ul>
            <li><strong>Zoom:</strong> Use mouse wheel or pinch gesture</li>
            <li><strong>Pan:</strong> Click and drag on empty space</li>
            <li><strong>Select Node:</strong> Click on any node to see details</li>
        </ul>
        <h3>Views:</h3>
        <ul>
            <li><strong>Hierarchical View:</strong> Shows transformations in processing order</li>
            <li><strong>Network View:</strong> Shows relationships between columns</li>
            <li><strong>Column-Focused View:</strong> Focuses on transformations for specific columns</li>
        </ul>
        <h3>Filtering:</h3>
        <p>Use the "Filter by Column" dropdown to focus on transformations affecting a specific column.</p>
        """
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Lineage Visualization Help")
        help_dialog.resize(600, 400)
        layout = QVBoxLayout(help_dialog)
        help_browser = QTextBrowser()
        help_browser.setHtml(help_text)
        layout.addWidget(help_browser)
        close_button = QPushButton("Close")
        close_button.clicked.connect(help_dialog.accept)
        layout.addWidget(close_button)
        help_dialog.exec()
    
    def exportLineage(self):
        pass

def show_enhanced_lineage_in_ui(config, registry):
    dlg = EnhancedLineageDialog(config, registry)
    dlg.exec()

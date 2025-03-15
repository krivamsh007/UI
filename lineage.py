import json
import datetime
from pyvis.network import Network
from ui_helpers import internal_to_friendly
from jinja2 import Template
from PyQt6.QtCore import QUrl, Qt, QSize,QPoint
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QToolBar, QSplitter,
    QFrame, QTextBrowser, QToolTip, 
)
from PyQt6.QtGui import QIcon, QPixmap, QFont,QAction

# Define a modern HTML template with enhanced styling and interactive features
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
      <div class="legend-item">
        <div class="legend-color" style="background-color: #FFA500;"></div>
        <span>Transformation</span>
      </div>
      <div class="legend-item">
        <div class="legend-color" style="background-color: #EE82EE;"></div>
        <span>Text Manipulation</span>
      </div>
      <div class="legend-item">
        <div class="legend-color" style="background-color: #008000;"></div>
        <span>Excel Function</span>
      </div>
      <div class="legend-item">
        <div class="legend-color" style="background-color: #FFFF00;"></div>
        <span>Final Output</span>
      </div>
    </div>
    
    <script type="text/javascript">
      var nodes = new vis.DataSet({{nodes}});
      var edges = new vis.DataSet({{edges}});
      var container = document.getElementById("mynetwork");
      var data = {nodes: nodes, edges: edges};
      var options = {{options}};
      var network = new vis.Network(container, data, options);
      
      // Show node details on click
      network.on("click", function(params) {
        if (params.nodes.length > 0) {
          var nodeId = params.nodes[0];
          var node = nodes.get(nodeId);
          var detailsDiv = document.getElementById("nodeDetails");
          
          if (node.details) {
            detailsDiv.innerHTML = node.details;
          } else {
            detailsDiv.innerHTML = "<h3>" + node.label + "</h3><p>No additional details available.</p>";
          }
        }
      });
      
      // Highlight connected nodes on hover
      network.on("hoverNode", function(params) {
        var nodeId = params.node;
        var connectedNodes = network.getConnectedNodes(nodeId);
        connectedNodes.push(nodeId);
        
        // Highlight connected nodes
        nodes.forEach(function(node) {
          if (connectedNodes.indexOf(node.id) > -1) {
            nodes.update({id: node.id, color: {opacity: 1.0}});
          } else {
            nodes.update({id: node.id, color: {opacity: 0.3}});
          }
        });
        
        // Highlight connected edges
        edges.forEach(function(edge) {
          if (connectedNodes.indexOf(edge.from) > -1 && connectedNodes.indexOf(edge.to) > -1) {
            edges.update({id: edge.id, color: {opacity: 1.0}});
          } else {
            edges.update({id: edge.id, color: {opacity: 0.3}});
          }
        });
      });
      
      // Reset highlights when not hovering
      network.on("blurNode", function() {
        nodes.forEach(function(node) {
          nodes.update({id: node.id, color: {opacity: 1.0}});
        });
        
        edges.forEach(function(edge) {
          edges.update({id: edge.id, color: {opacity: 1.0}});
        });
      });
      
      // Toggle legend visibility
      function toggleLegend() {
        var legend = document.getElementById("legend");
        if (legend.style.display === "none") {
          legend.style.display = "block";
        } else {
          legend.style.display = "none";
        }
      }
      
      // Export network as image
      function exportImage() {
        var canvas = container.getElementsByTagName('canvas')[0];
        var image = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
        var link = document.createElement('a');
        link.download = 'data_lineage_' + new Date().toISOString().slice(0,10) + '.png';
        link.href = image;
        link.click();
      }
      
      // Change layout
      function changeLayout() {
        var layoutSelect = document.getElementById("layoutSelect");
        var selectedLayout = layoutSelect.value;
        
        if (selectedLayout === "hierarchical") {
          network.setOptions({
            layout: {
              hierarchical: {
                enabled: true,
                direction: "UD",
                sortMethod: "directed",
                nodeSpacing: 200,
                treeSpacing: 300
              }
            }
          });
        } else {
          network.setOptions({
            layout: {
              hierarchical: {
                enabled: false
              }
            },
            physics: {
              enabled: true,
              barnesHut: {
                gravitationalConstant: -2000,
                centralGravity: 0.3,
                springLength: 150,
                springConstant: 0.04
              }
            }
          });
        }
      }
      
      // Search nodes
      function searchNodes() {
        var searchText = document.getElementById("searchBox").value.toLowerCase();
        
        if (searchText === "") {
          // Reset all nodes if search is empty
          nodes.forEach(function(node) {
            nodes.update({id: node.id, hidden: false});
          });
          return;
        }
        
        var matchingNodes = [];
        
        // Find matching nodes
        nodes.forEach(function(node) {
          var nodeLabel = node.label.toLowerCase();
          var nodeTitle = node.title ? node.title.toLowerCase() : "";
          
          if (nodeLabel.includes(searchText) || nodeTitle.includes(searchText)) {
            matchingNodes.push(node.id);
            nodes.update({id: node.id, hidden: false});
          } else {
            nodes.update({id: node.id, hidden: true});
          }
        });
        
        // If nodes were found, focus on them
        if (matchingNodes.length > 0) {
          network.fit({
            nodes: matchingNodes,
            animation: true
          });
        }
      }
    </script>
  </body>
</html>
"""

# Column transformation tracker to store detailed information about column changes
class ColumnTransformationTracker:
    """
    Tracks transformations applied to columns throughout the data processing pipeline.
    Maintains a history of operations and their effects on each column.
    """
    def __init__(self):
        self.column_history = {}  # Maps column_id to list of transformations
        self.derived_columns = {}  # Maps derived column_id to source column_id(s)
        
    def add_transformation(self, column_id, transformation_name, parameters, timestamp=None):
        """Add a transformation record for a specific column"""
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
        """Register a new column derived from one or more source columns"""
        self.derived_columns[new_column_id] = {
            "sources": source_column_ids if isinstance(source_column_ids, list) else [source_column_ids],
            "transformation": transformation_name,
            "parameters": parameters,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Initialize history for the new column
        if new_column_id not in self.column_history:
            self.column_history[new_column_id] = []
            
    def get_column_history(self, column_id):
        """Get the transformation history for a specific column"""
        return self.column_history.get(column_id, [])
        
    def get_column_lineage(self, column_id):
        """Get the complete lineage for a column, including source columns if derived"""
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
        """Extract column transformation information from a configuration dictionary"""
        # Process filters
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
        
        # Process transformations
        transformations = config.get("Transformations", {})
        for trans_name, params in transformations.items():
            if "column" in params:
                # Single column transformation
                input_col = params["column"]
                self.add_transformation(input_col, trans_name, params)
                
                # Check if creating a new column
                if "new_column" in params:
                    new_col = params["new_column"]
                    self.register_derived_column(new_col, input_col, trans_name, params)
            
            elif "columns" in params:
                # Multi-column transformation
                affected = params["columns"]
                for col in affected:
                    self.add_transformation(col, trans_name, params)
                
                # Check if creating new columns
                if "new_columns" in params:
                    new_cols = params["new_columns"]
                    for new_col in new_cols:
                        self.register_derived_column(new_col, affected, trans_name, params)
        
        # Process Excel functions
        adv_excel = config.get("Advanced Excel Functions", {})
        for key, params in adv_excel.items():
            if "column" in params:
                # Single column Excel function
                input_col = params["column"]
                self.add_transformation(input_col, f"Excel_{key}", params)
                
                # Check if creating a new column
                if "new_column" in params:
                    new_col = params["new_column"]
                    self.register_derived_column(new_col, input_col, f"Excel_{key}", params)
            
            elif "columns" in params:
                # Multi-column Excel function
                affected = params["columns"]
                for col in affected:
                    self.add_transformation(col, f"Excel_{key}", params)

def generate_enhanced_lineage_graph(config, registry, column_tracker=None):

    # Create a new column tracker if none provided
    if column_tracker is None:
        column_tracker = ColumnTransformationTracker()
        column_tracker.extract_from_config(config, registry)
    
    # Initialize network with modern template
    net = Network(height="800px", width="100%", directed=True)
    net.template = Template(modern_template)
    
    # Set enhanced hierarchical layout options
    hierarchical_options = {
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
            "hierarchicalRepulsion": {
                "nodeDistance": 150,
                "avoidOverlap": 1
            },
            "minVelocity": 0.75
        },
        "interaction": {
            "hover": True,
            "tooltipDelay": 200,
            "zoomView": True,
            "dragView": True
        },
        "edges": {
            "smooth": {
                "type": "cubicBezier",
                "forceDirection": "vertical"
            },
            "arrows": {
                "to": {
                    "enabled": True,
                    "scaleFactor": 0.5
                }
            },
            "color": {
                "color": "#2B7CE9",
                "highlight": "#FFA500",
                "hover": "#2B7CE9"
            }
        },
        "nodes": {
            "shape": "box",
            "font": {
                "face": "Segoe UI",
                "size": 14
            },
            "margin": 10,
            "shadow": {
                "enabled": True,
                "size": 3,
                "x": 3,
                "y": 3
            }
        }
    }
    net.set_options(json.dumps(hierarchical_options))
    
    # --- Source Node ---
    file_name = config.get("file_name", "Source Dataset")
    source_label = f"File: {file_name}"
    
    # Enhanced source node with column details
    column_details = []
    for k in registry:
        friendly_name = internal_to_friendly(k, registry)
        column_history = column_tracker.get_column_history(k)
        transformation_count = len(column_history)
        
        # Add badge if column has transformations
        badge = f'<span class="badge" style="background-color: #4CAF50;">{transformation_count}</span>' if transformation_count > 0 else ""
        column_details.append(f"<li>{friendly_name} {badge}</li>")
    
    source_columns = "<ul>" + "\n".join(column_details) + "</ul>"
    
    # Create HTML details for the node details panel
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
    
    # Create tooltip with basic information
    source_title = f"File: {file_name}<br>Columns: {len(registry)}"
    
    # Add source node with enhanced styling
    net.add_node(
        source_label, 
        label=source_label, 
        title=source_title, 
        shape="box", 
        color="#A9A9A9",
        details=source_details,
        font={"size": 16, "face": "Segoe UI", "bold": True}
    )
    current_node = source_label

    # --- Process Filters ---
    filters = config.get("Filters", [])
    for i, filt in enumerate(filters, start=1):
        # Expected format: (column, condition, value, [optional metrics])
        col, cond, val = filt[0], filt[1], filt[2]
        metrics = filt[3] if len(filt) > 3 else {}
        friendly_col = internal_to_friendly(col, registry)
        
        # Enhanced metrics display
        rows_before = metrics.get('rows_before', '-')
        rows_after = metrics.get('rows_after', '-')
        row_reduction = ""
        
        if rows_before != '-' and rows_after != '-':
            if rows_before > rows_after:
                reduction_pct = ((rows_before - rows_after) / rows_before) * 100
                row_reduction = f"<span style='color: #FF5733;'>(-{reduction_pct:.1f}%)</span>"
        
        metric_info = f"Rows Before: {rows_before}, Rows After: {rows_after} {row_reduction}"
        
        # Create HTML details for the node details panel
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
        
        # Add column transformation history
        column_history = column_tracker.get_column_history(col)
        for entry in column_history:
            filter_details_html += f"<li><strong>{entry['transformation']}</strong> at {entry['timestamp']}</li>"
        
        filter_details_html += """
            </ul>
        </div>
        """
        
        # Create tooltip with basic information
        filter_tooltip = f"Filter {i}<br>{friendly_col}: {cond} {val}<br>{metric_info}"
        
        # Add filter node with enhanced styling
        filter_node = f"Filter {i} - {friendly_col}"
        net.add_node(
            filter_node, 
            label=f"Filter {i}", 
            title=filter_tooltip, 
            shape="diamond", 
            color="#ADD8E6",
            details=filter_details_html,
            font={"size": 14, "face": "Segoe UI"}
        )
        net.add_edge(
            current_node, 
            filter_node, 
            title="Apply Filter",
            width=2,
            color={"color": "#2B7CE9", "highlight": "#FFA500"}
        )
        current_node = filter_node

    # --- Process Generic Transformations ---
    transformations = config.get("Transformations", {})
    sorted_trans = sorted(transformations.items(), key=lambda kv: kv[1].get("sequence", 9999))
    for trans_name, params in sorted_trans:
        # Basic transformation details
        trans_details = f"Transformation: {trans_name}\nParameters:\n{json.dumps(params, indent=2)}"
        
        # Enhanced HTML details for the node details panel
        trans_details_html = f"""
        <h3>Transformation: {trans_name}</h3>
        <div style="margin-top: 10px;">
        """
        
        # Track affected columns for visualization
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
            affected = params["columns"]
            affected_columns.extend(affected)
            
            if set(affected) == set(registry.keys()):
                trans_details_html += "<p><strong>Affected Columns:</strong> All columns</p>"
            else:
                friendly_list = [internal_to_friendly(c, registry) for c in affected]
                trans_details_html += f"<p><strong>Affected Columns:</strong> {', '.join(friendly_list)}</p>"
            
            if "new_columns" in params:
                affected_new = params["new_columns"]
                output_columns.extend(affected_new)
                
                if set(affected_new) == set(registry.keys()):
                    trans_details_html += "<p><strong>Output Columns:</strong> All columns</p>"
                else:
                    friendly_new = [internal_to_friendly(c, registry) for c in affected_new]
                    trans_details_html += f"<p><strong>Output Columns:</strong> {', '.join(friendly_new)}</p>"
        else:
            affected_columns.extend(list(registry.keys()))
            trans_details_html += "<p><strong>Affected Columns:</strong> All columns</p>"
        
        # Add metrics if available
        if "metrics" in params:
            metrics = params["metrics"]
            rows_before = metrics.get('rows_before', '-')
            rows_after = metrics.get('rows_after', '-')
            
            # Calculate and display percentage change
            change_html = ""
            if rows_before != '-' and rows_after != '-':
                if rows_before != rows_after:
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
        
        # Add sample data if available
        if "sample_data" in params:
            sample_data = params['sample_data']
            trans_details_html += f"""
            <div style="margin-top: 10px;">
                <h4>Data Sample:</h4>
                <pre style="background-color: #f8f8f8; padding: 10px; border-radius: 4px; overflow: auto; max-height: 200px;">{sample_data}</pre>
            </div>
            """
        
        # Add timestamp if available
        if "timestamp" in params:
            trans_details_html += f"<p><strong>Timestamp:</strong> {params['timestamp']}</p>"
        
        # Add column transformation history section
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
        
        # Add rows for each affected column
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
        
        # Close the main div
        trans_details_html += "</div>"
        
        # Create tooltip with basic information
        tooltip_text = f"{trans_name}"
        if "column" in params:
            tooltip_text += f"<br>Column: {internal_to_friendly(params['column'], registry)}"
        elif "columns" in params and len(params["columns"]) <= 3:
            cols = [internal_to_friendly(c, registry) for c in params["columns"]]
            tooltip_text += f"<br>Columns: {', '.join(cols)}"
        else:
            tooltip_text += "<br>Multiple columns affected"
        
        # Set node color and shape based on transformation type
        node_color = "#FFA500"  # Default orange
        node_shape = "ellipse"
        
        if trans_name.lower() in ["replace substring", "change case", "trim"]:
            node_color = "#EE82EE"  # Violet for text manipulations
        
        # Add transformation count badge to label if multiple columns affected
        label_text = trans_name
        if len(affected_columns) > 1:
            label_text = f"{trans_name} ({len(affected_columns)})"
        
        # Create unique node ID
        node_id = f"{trans_name}_{hash(json.dumps(params)) % 10000}"
        
        # Add transformation node with enhanced styling
        drilldown_url = params.get("drilldown_url", "")
        net.add_node(
            node_id, 
            label=label_text, 
            title=tooltip_text, 
            shape=node_shape, 
            color=node_color,
            details=trans_details_html,
            url=drilldown_url,
            font={"size": 14, "face": "Segoe UI"}
        )
        
        # Add edge with descriptive title
        edge_title = "Transformation Step"
        if "metrics" in params:
            metrics = params["metrics"]
            if "rows_before" in metrics and "rows_after" in metrics:
                edge_title += f" ({metrics['rows_after']} rows)"
        
        net.add_edge(
            current_node, 
            node_id, 
            title=edge_title,
            width=2,
            color={"color": "#2B7CE9", "highlight": "#FFA500"}
        )
        current_node = node_id

    # --- Process Advanced Excel Functions ---
    adv_excel = config.get("Advanced Excel Functions", {})
    if adv_excel:
        for key, params in adv_excel.items():
            # Basic Excel function details
            excel_details = f"Excel Function: {key}\nParameters:\n{json.dumps(params, indent=2)}"
            
            # Enhanced HTML details for the node details panel
            excel_details_html = f"""
            <h3>Excel Function: {key}</h3>
            <div style="margin-top: 10px;">
            """
            
            # Track affected columns for visualization
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
            
            # Add timestamp if available
            if "timestamp" in params:
                excel_details_html += f"<p><strong>Timestamp:</strong> {params['timestamp']}</p>"
            
            # Add sample data if available
            if "sample_data" in params:
                sample_data = params['sample_data']
                excel_details_html += f"""
                <div style="margin-top: 10px;">
                    <h4>Data Sample:</h4>
                    <pre style="background-color: #f8f8f8; padding: 10px; border-radius: 4px; overflow: auto; max-height: 200px;">{sample_data}</pre>
                </div>
                """
            
            # Add column transformation history section
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
            
            # Add rows for each affected column
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
            
            # Close the main div
            excel_details_html += "</div>"
            
            # Create tooltip with basic information
            tooltip_text = f"Excel: {key}"
            if "column" in params:
                tooltip_text += f"<br>Column: {internal_to_friendly(params['column'], registry)}"
            elif "columns" in params and len(params["columns"]) <= 3:
                cols = [internal_to_friendly(c, registry) for c in params["columns"]]
                tooltip_text += f"<br>Columns: {', '.join(cols)}"
            else:
                tooltip_text += "<br>Multiple columns affected"
            
            # Add transformation count badge to label if multiple columns affected
            label_text = key
            if len(affected_columns) > 1:
                label_text = f"{key} ({len(affected_columns)})"
            
            # Create unique node ID
            node_id = f"Excel_{key}_{hash(json.dumps(params)) % 10000}"
            
            # Add Excel function node with enhanced styling
            net.add_node(
                node_id, 
                label=label_text, 
                title=tooltip_text, 
                shape="ellipse", 
                color="#008000",
                details=excel_details_html,
                font={"size": 14, "face": "Segoe UI"}
            )
            
            # Add edge with descriptive title
            net.add_edge(
                current_node, 
                node_id, 
                title="Excel Transformation",
                width=2,
                color={"color": "#2B7CE9", "highlight": "#FFA500"}
            )
            current_node = node_id

    # --- Final Target Node ---
    final_node = "Final Output"
    
    # Create HTML details for the node details panel
    final_details_html = f"""
    <h3>Final Transformed Dataset</h3>
    <div style="margin-top: 10px;">
        <p><strong>Status:</strong> <span style="color: #4CAF50;">Ready for Use</span></p>
        <p><strong>Transformations Applied:</strong> {len(sorted_trans) + len(adv_excel) + len(filters)}</p>
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
    
    # Add rows for each column in the registry
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
    
    # Create tooltip with basic information
    final_title = "Transformed Data Ready for Use"
    
    # Add final node with enhanced styling
    net.add_node(
        final_node, 
        label=final_node, 
        title=final_title, 
        shape="box", 
        color="#FFFF00",
        details=final_details_html,
        font={"size": 16, "face": "Segoe UI", "bold": True}
    )
    
    # Add edge with descriptive title
    net.add_edge(
        current_node, 
        final_node, 
        title="Output Data",
        width=3,
        color={"color": "#2B7CE9", "highlight": "#FFA500"}
    )
    
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
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Add toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        
        # Add toolbar actions
        help_action = QAction("Help", self)
        help_action.triggered.connect(self.showHelp)
        toolbar.addAction(help_action)
        
        export_action = QAction("Export", self)
        export_action.triggered.connect(self.exportLineage)
        toolbar.addAction(export_action)
        
        # Add view options
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("View Options:"))
        
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Hierarchical View", "Network View", "Column-Focused View"])
        self.view_combo.currentIndexChanged.connect(self.changeView)
        toolbar.addWidget(self.view_combo)
        
        # Add column filter
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
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Web view for lineage graph
        self.web_view = QWebEngineView()
        
        # Details panel
        details_frame = QFrame()
        details_frame.setFrameShape(QFrame.Shape.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        
        details_header = QLabel("Column Details")
        details_header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        details_layout.addWidget(details_header)
        
        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(True)
        details_layout.addWidget(self.details_browser)
        
        # Add column selection for details
        column_select_layout = QHBoxLayout()
        column_select_layout.addWidget(QLabel("Select Column:"))
        
        self.details_column_combo = QComboBox()
        for col_id in self.registry:
            friendly_name = internal_to_friendly(col_id, self.registry)
            self.details_column_combo.addItem(friendly_name)
        self.details_column_combo.currentIndexChanged.connect(self.updateColumnDetails)
        column_select_layout.addWidget(self.details_column_combo)
        
        details_layout.addLayout(column_select_layout)
        
        # Add widgets to splitter
        splitter.addWidget(self.web_view)
        splitter.addWidget(details_frame)
        
        # Set initial splitter sizes (70% graph, 30% details)
        splitter.setSizes([700, 300])
        
        main_layout.addWidget(splitter)
        
        # Generate and display the lineage graph
        self.generateLineageGraph()
        
        # Update column details for the first column
        if self.details_column_combo.count() > 0:
            self.updateColumnDetails(0)
    
    def generateLineageGraph(self):
        """Generate and display the lineage graph"""
        net = generate_enhanced_lineage_graph(self.config, self.registry, self.column_tracker)
        html_content = net.generate_html()
        self.web_view.setHtml(html_content, QUrl("about:blank"))
    
    def updateColumnDetails(self, index):
        """Update the details panel with information about the selected column"""
        if index < 0 or self.details_column_combo.count() == 0:
            return
            
        friendly_name = self.details_column_combo.currentText()
        
        # Find the internal column ID
        col_id = None
        for k, v in self.registry.items():
            if internal_to_friendly(k, self.registry) == friendly_name:
                col_id = k
                break
        
        if col_id is None:
            return
            
        # Get column lineage
        lineage = self.column_tracker.get_column_lineage(col_id)
        
        # Create HTML content for details
        html = f"""
        <h2 style="color: #2B7CE9;">{friendly_name}</h2>
        <div style="margin-top: 10px;">
            <p><strong>Internal ID:</strong> {col_id}</p>
            <p><strong>Transformation Count:</strong> {len(lineage['history'])}</p>
            <p><strong>Is Derived:</strong> {'Yes' if lineage['is_derived'] else 'No'}</p>
        </div>
        """
        
        # Add derivation information if applicable
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
        
        # Add transformation history
        html += """
        <div style="margin-top: 15px;">
            <h3>Transformation History</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">#</th>
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Transformation</th>
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Timestamp</th>
                </tr>
        """
        
        for i, entry in enumerate(lineage['history'], 1):
            html += f"""
                <tr>
                    <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{i}</td>
                    <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{entry['transformation']}</td>
                    <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{entry['timestamp']}</td>
                </tr>
            """
        
        html += """
            </table>
        </div>
        """
        
        # Set the HTML content
        self.details_browser.setHtml(html)
    
    def changeView(self, index):
        """Change the lineage visualization view based on selection"""
        # This would modify the visualization based on the selected view
        # For now, we'll just regenerate the default view
        self.generateLineageGraph()
    
    def filterByColumn(self, index):
        """Filter the lineage visualization to focus on a specific column"""
        # This would modify the visualization to highlight paths related to the selected column
        # For now, we'll just regenerate the default view
        self.generateLineageGraph()
    
    def showHelp(self):
        """Show help information"""
        help_text = """
        <h2>Enhanced Data Lineage Visualization</h2>
        
        <p>This tool visualizes the flow of data through your transformation pipeline, 
        showing how columns are transformed and how data moves through the system.</p>
        
        <h3>Navigation</h3>
        <ul>
            <li><strong>Pan:</strong> Click and drag on empty space</li>
            <li><strong>Zoom:</strong> Use mouse wheel or pinch gesture</li>
            <li><strong>Select Node:</strong> Click on any node to see details</li>
            <li><strong>Hover:</strong> Hover over nodes to see basic information</li>
        </ul>
        
        <h3>Views</h3>
        <ul>
            <li><strong>Hierarchical View:</strong> Shows transformations in sequence from top to bottom</li>
            <li><strong>Network View:</strong> Shows relationships between transformations in a force-directed layout</li>
            <li><strong>Column-Focused View:</strong> Highlights transformations affecting a specific column</li>
        </ul>
        
        <h3>Column Details</h3>
        <p>The details panel shows information about the selected column, including:</p>
        <ul>
            <li>Transformation history</li>
            <li>Derivation information (if applicable)</li>
            <li>Relationships to other columns</li>
        </ul>
        """
        
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Lineage Visualization Help")
        help_dialog.resize(600, 500)
        
        layout = QVBoxLayout(help_dialog)
        
        help_browser = QTextBrowser()
        help_browser.setHtml(help_text)
        layout.addWidget(help_browser)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(help_dialog.accept)
        layout.addWidget(close_button)
        
        help_dialog.exec()
    
    def exportLineage(self):
        """Export the lineage visualization"""
        # This would implement export functionality
        # For now, we'll just show a message
        QToolTip.showText(self.mapToGlobal(QPoint(100, 100)), "Export functionality would be implemented here", self)

def show_enhanced_lineage_in_ui(config, registry):
    dlg = EnhancedLineageDialog(config, registry)
    dlg.exec()

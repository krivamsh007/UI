# -----------------------------------------------------------------------------
# Copyright (c) [2025] [Vamshi Krishna Nagabhyru]
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
import json
from pyvis.network import Network
from ui_helpers import internal_to_friendly
from jinja2 import Template
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QDialog, QVBoxLayout

# Define a minimal HTML template with an explicit container height.
minimal_template = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Data Lineage</title>
    <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/vis-network.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/vis-network.min.css" rel="stylesheet" type="text/css" />
    <style>
      html, body { width: 100%; height: 100%; margin: 0; padding: 0; }
      #mynetwork { width: 100%; height: 800px; }
    </style>
  </head>
  <body>
    <div id="mynetwork"></div>
    <script type="text/javascript">
      var nodes = new vis.DataSet({{nodes}});
      var edges = new vis.DataSet({{edges}});
      var container = document.getElementById("mynetwork");
      var data = {nodes: nodes, edges: edges};
      var options = {{options}};
      var network = new vis.Network(container, data, options);
    </script>
  </body>
</html>
"""

def generate_lineage_graph(config, registry):
    """
    Generates a pyvis Network with a hierarchical layout.
    The first (source) node shows the file name and lists its columns using friendly names.
    Subsequent nodes (if any) display transformation details in plain text.
    """
    net = Network(height="800px", width="100%", directed=True)
    net.template = Template(minimal_template)
    
    # Set hierarchical layout options.
    hierarchical_options = {
        "layout": {
            "hierarchical": {
                "enabled": True,
                "direction": "UD",   
                "sortMethod": "directed",
                "nodeSpacing": 200,
                "treeSpacing": 300
            }
        },
        "physics": {
            "hierarchicalRepulsion": {
                "nodeDistance": 150
            },
            "minVelocity": 0.75
        }
    }
    net.set_options(json.dumps(hierarchical_options))
    
    # --- Source Node ---
    # Use "file_name" from config if available; otherwise, use default.
    file_name = config.get("file_name", "Source Dataset")
    source_label = f"File: {file_name}"
    # List friendly column names.
    source_columns = "\n".join([internal_to_friendly(k, registry) for k in registry])
    source_title = f"File: {file_name}\nColumns:\n{source_columns}"
    net.add_node(source_label, label=source_label, title=source_title, shape="box", color="#A9A9A9")
    current_node = source_label

    # --- Process Filters ---
    filters = config.get("Filters", [])
    for i, filt in enumerate(filters, start=1):
        # Expected format: (column, condition, value, [optional metrics])
        col, cond, val = filt[0], filt[1], filt[2]
        metrics = filt[3] if len(filt) > 3 else {}
        friendly_col = internal_to_friendly(col, registry)
        metric_info = f"Rows Before: {metrics.get('rows_before', '-')}, Rows After: {metrics.get('rows_after', '-')}"
        filter_details = f"Filter {i}:\n{friendly_col}: {cond} {val}\n{metric_info}"
        filter_node = f"Filter {i} - {friendly_col}"
        net.add_node(filter_node, label=f"Filter {i}", title=filter_details, shape="diamond", color="#ADD8E6")
        net.add_edge(current_node, filter_node, title="Apply Filter")
        current_node = filter_node

    # --- Process Generic Transformations ---
    transformations = config.get("Transformations", {})
    sorted_trans = sorted(transformations.items(), key=lambda kv: kv[1].get("sequence", 9999))
    for trans_name, params in sorted_trans:
        details = f"Transformation: {trans_name}\nParameters:\n{json.dumps(params, indent=2)}"
        if "column" in params:
            input_col = params["column"]
            friendly_input = internal_to_friendly(input_col, registry)
            details += f"\nInput Column: {friendly_input}"
            if "new_column" in params:
                new_col = params["new_column"]
                friendly_new = internal_to_friendly(new_col, registry) if new_col in registry else new_col
                details += f"\nOutput Column: {friendly_new}"
        elif "columns" in params:
            affected = params["columns"]
            if set(affected) == set(registry.keys()):
                details += "\nAffected Columns: All columns"
            else:
                friendly_list = [internal_to_friendly(c, registry) for c in affected]
                details += "\nAffected Columns: " + ", ".join(friendly_list)
            if "new_columns" in params:
                affected_new = params["new_columns"]
                if set(affected_new) == set(registry.keys()):
                    details += "\nOutput Columns: All columns"
                else:
                    friendly_new = [internal_to_friendly(c, registry) for c in affected_new]
                    details += "\nOutput Columns: " + ", ".join(friendly_new)
        else:
            details += "\nAffected Columns: All columns"
        if "metrics" in params:
            metrics = params["metrics"]
            details += f"\nMetrics: Rows Before: {metrics.get('rows_before', '-')}, Rows After: {metrics.get('rows_after', '-')}"
        if "sample_data" in params:
            details += f"\nData Sample:\n{params['sample_data']}"
        if "timestamp" in params:
            details += f"\nTimestamp: {params['timestamp']}"
        
        node_color = "#FFA500"  # Orange.
        node_shape = "ellipse"
        if trans_name.lower() in ["replace substring", "change case", "trim"]:
            node_color = "#EE82EE"  # Violet.
        node_id = f"{trans_name}_{hash(json.dumps(params)) % 10000}"
        drilldown_url = params.get("drilldown_url", "")
        net.add_node(node_id, label=trans_name, title=details, shape=node_shape, color=node_color, url=drilldown_url)
        net.add_edge(current_node, node_id, title="Transformation Step")
        current_node = node_id

    # --- Process Advanced Excel Functions ---
    adv_excel = config.get("Advanced Excel Functions", {})
    if adv_excel:
        for key, params in adv_excel.items():
            details = f"Excel Function: {key}\nParameters:\n{json.dumps(params, indent=2)}"
            if "timestamp" in params:
                details += f"\nTimestamp: {params['timestamp']}"
            if "sample_data" in params:
                details += f"\nData Sample:\n{params['sample_data']}"
            if "column" in params:
                friendly = internal_to_friendly(params["column"], registry)
                details += f"\nInput Column: {friendly}"
                if "new_column" in params:
                    new_col = params["new_column"]
                    friendly_new = internal_to_friendly(new_col, registry) if new_col in registry else new_col
                    details += f"\nOutput Column: {friendly_new}"
            elif "columns" in params:
                affected = params["columns"]
                if set(affected) == set(registry.keys()):
                    details += "\nAffected Columns: All columns"
                else:
                    friendly_list = [internal_to_friendly(c, registry) for c in affected]
                    details += "\nAffected Columns: " + ", ".join(friendly_list)
            node_id = f"Excel_{key}_{hash(json.dumps(params)) % 10000}"
            net.add_node(node_id, label=key, title=details, shape="ellipse", color="#008000")
            net.add_edge(current_node, node_id, title="Excel Transformation")
            current_node = node_id

    # --- Final Target Node ---
    final_node = "Final Output"
    final_title = "Transformed Data Ready for Use"
    net.add_node(final_node, label=final_node, title=final_title, shape="box", color="#FFFF00")
    net.add_edge(current_node, final_node, title="Output Data")
    
    return net

def show_lineage_in_ui(config, registry):
    """
    Generates the lineage network and displays it in a QDialog using QWebEngineView.
    """
    net = generate_lineage_graph(config, registry)
    html_content = net.generate_html()  # Get the complete HTML content.
    
    dlg = QDialog()
    dlg.setWindowTitle("Data Lineage")
    dlg.resize(1000, 800)
    layout = QVBoxLayout(dlg)
    view = QWebEngineView()
    view.setHtml(html_content, QUrl("about:blank"))
    layout.addWidget(view)
    dlg.setLayout(layout)
    dlg.exec_()

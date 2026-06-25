"""Build the NovaBank Digital graph-investigation notebook.

Run with: uv run python notebooks/06_graph_network_fraud/_build_novabank_graph_notebook.py
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook


def build_notebook() -> nbf.NotebookNode:
    """Assemble the NovaBank Digital graph-investigation notebook."""
    nb = new_notebook()

    nb.cells.append(new_markdown_cell(
        "# NovaBank Digital Graph Investigation\n"
        "\n"
        "This notebook introduces relationship and network analysis for the "
        "**NovaBank Digital** digital-banking track. A learner builds a graph from "
        "the canonical generated tables, computes explainable network features, and "
        "investigates digital-banking network structures: mule rings, shared "
        "devices, shared beneficiaries, and pass-through clusters.\n"
        "\n"
        "Graph evidence **extends** the existing v0.4 digital-banking tabular "
        "investigation — it does not replace it. Every network signal is connected "
        "back to the session-risk, beneficiary-novelty, pass-through, and "
        "shared-device tabular signals and the v0.5 case context.\n"
        "\n"
        "The **User** (digital login identity) is distinct from the **Client** "
        "(legal customer): a Client owns the relationship, a User authenticates "
        "sessions. Both are nodes here, and the distinction matters when reading "
        "shared-device signals."
    ))

    nb.cells.append(new_code_cell(
        "import pandas as pd\n"
        "\n"
        "from banking_fraud_lab import (\n"
        "    build_all_graph_features,\n"
        "    build_banking_graph,\n"
        "    build_foundation_progressive_views,\n"
        "    generate_minimal_banking_world,\n"
        "    join_graph_features_to_view,\n"
        ")\n"
        "\n"
        "pd.set_option('display.max_columns', None)"
    ))

    nb.cells.append(new_markdown_cell(
        "## Build the Banking Graph\n"
        "\n"
        "The graph is derived purely from the canonical generated tables. "
        "Sessions and devices become nodes: a session authenticates a **User**, "
        "and a device is linked to every session observed on its fingerprint. "
        "Several **Users** sharing one device is the core shared-device signal."
    ))

    nb.cells.append(new_code_cell(
        "tables = generate_minimal_banking_world(seed=42, scale='tiny')\n"
        "graph = build_banking_graph(tables)\n"
        "\n"
        "print(f'Nodes: {graph.number_of_nodes()}')\n"
        "print(f'Edges: {graph.number_of_edges()}')\n"
        "\n"
        "node_type_counts = (\n"
        "    pd.Series([d['node_type'] for _, d in graph.nodes(data=True)])\n"
        "    .value_counts()\n"
        "    .sort_index()\n"
        ")\n"
        "node_type_counts"
    ))

    nb.cells.append(new_markdown_cell(
        "## Mule Rings and Connected Components\n"
        "\n"
        "A mule ring is a connected cluster of accounts, beneficiaries, and "
        "**Users** that move funds between each other. Connected-component "
        "membership sizes the clusters; large components spanning many "
        "**Users** or beneficiaries are the network signature of a ring."
    ))

    nb.cells.append(new_code_cell(
        "features = build_all_graph_features(graph)\n"
        "components = features['graph_connected_component']\n"
        "ring_candidates = (\n"
        "    components[components['component_size'] > 1]\n"
        "    .sort_values('component_size', ascending=False)\n"
        ")\n"
        "ring_candidates.head(10)"
    ))

    nb.cells.append(new_markdown_cell(
        "## Shared Devices\n"
        "\n"
        "Devices are derived from session telemetry: each distinct "
        "`device_fingerprint_hash` is one device node, and each session links its "
        "device to its **User**. A device with high degree (many **Users**) is a "
        "shared-device lead — the kind of signal that, combined with "
        "pass-through velocity, points at account takeover or mule coordination."
    ))

    nb.cells.append(new_code_cell(
        "degree = features['graph_node_degree']\n"
        "device_hubs = (\n"
        "    degree[degree['node_type'] == 'device']\n"
        "    .sort_values('node_degree', ascending=False)\n"
        "    .head(5)\n"
        ")\n"
        "device_hubs"
    ))

    nb.cells.append(new_markdown_cell(
        "## Shared Beneficiaries and Pass-Through\n"
        "\n"
        "Beneficiaries that receive funds from several otherwise-unrelated "
        "**Clients** or **Users** are a counterparty-network signal. Bridge nodes "
        "highlight single points through which funds pass between clusters — the "
        "structural core of a pass-through cluster."
    ))

    nb.cells.append(new_code_cell(
        "bridge = features['graph_bridge_node']\n"
        "beneficiary_bridges = bridge[\n"
        "    (bridge['node_type'] == 'beneficiary')\n"
        "    & (bridge['is_bridge_endpoint'] == 1)\n"
        "]\n"
        "print(f'Beneficiary bridge nodes: {len(beneficiary_bridges)}')\n"
        "beneficiary_bridges.head(10)"
    ))

    nb.cells.append(new_markdown_cell(
        "## Connect Graph Evidence to the Investigation\n"
        "\n"
        "Graph features are joined back to the foundation "
        "`foundation_alert_lifecycle` Progressive data view so network evidence "
        "supports the alert-level investigation. The join does not drop or "
        "duplicate any keyed row — it adds network context to the existing "
        "tabular alert lifecycle."
    ))

    nb.cells.append(new_code_cell(
        "views = build_foundation_progressive_views(tables)\n"
        "alert_view = views['foundation_alert_lifecycle']\n"
        "augmented = join_graph_features_to_view(degree, alert_view)\n"
        "network_columns = [c for c in augmented.columns if c.startswith('node_degree_')]\n"
        "view_keys = ['alert_id', 'user_id', 'session_id']\n"
        "augmented[[c for c in view_keys if c in augmented.columns] + network_columns].head()"
    ))

    nb.cells.append(new_markdown_cell(
        "## Interpretation and Limitations\n"
        "\n"
        "Network signals here are **investigative leads**, not proof of fraud. A "
        "large component, a high-degree device, or a bridge beneficiary is a "
        "reason to look more closely at the v0.4 digital-banking tabular signals "
        "(session risk, beneficiary novelty, pass-through, shared device) and the "
        "v0.5 case context — not a verdict. This notebook avoids headline accuracy "
        "claims and frames outputs for business, risk, and compliance discussion.\n"
        "\n"
        "- **Mule rings** (large components) are structural; confirm with "
        "beneficiary-change history and account age.\n"
        "- **Shared devices** are leads; confirm with session telemetry and auth "
        "method.\n"
        "- **Shared beneficiaries / pass-through** are leads; confirm with "
        "payment velocity and purpose.\n"
        "\n"
        "Remember the **User** (login identity) vs **Client** (legal customer) "
        "distinction when reading shared-device and counterparty signals.\n"
        "\n"
        "All data is synthetic (NovaBank Digital). No real client data, no "
        "reconstruction of real events, and no legal advice is provided."
    ))

    return nb


def main() -> None:
    """Write the notebook to disk next to this script."""
    out_path = Path(__file__).resolve().parent / "novabank_graph_investigation.ipynb"
    nb = build_notebook()
    nbf.write(nb, out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network


def render_collusion_graph(cluster_nodes: list, cluster_edges: list):
    st.markdown("### Document similarity network")
    st.caption(
        "A link represents a saved similarity report above the selected threshold. "
        "Documents in the same connected component are grouped into one cluster."
    )

    if not cluster_nodes or not cluster_edges:
        st.info(
            "No qualifying links found. Run plagiarism detection for one or more documents, "
            "or lower the similarity threshold."
        )
        return

    net = Network(
        height="620px",
        width="100%",
        bgcolor="#1e1e2e",
        font_color="#cdd6f4",
        directed=False,
        neighborhood_highlight=True,
        cdn_resources="in_line"
    )
    net.barnes_hut(gravity=-2500, central_gravity=0.15, spring_length=180)

    cluster_colors = ["#cba6f7", "#89b4fa", "#94e2d5", "#a6e3a1", "#fab387"]
    for node in cluster_nodes:
        node_id = str(node["id"])
        label = node.get("label") or node.get("doc_id", node_id)
        cluster_id = node.get("cluster_id", 0)
        net.add_node(
            node_id,
            label=label,
            title=f"{label}\nCluster {cluster_id + 1}",
            color={
                "background": cluster_colors[cluster_id % len(cluster_colors)],
                "border": "#f5e0dc",
                "highlight": {"background": "#f5c2e7", "border": "#cba6f7"}
            },
            size=26,
            borderWidth=2,
            font={"color": "#cdd6f4", "face": "monospace"}
        )

    for edge in cluster_edges:
        similarity = float(edge.get("weight", 0.0))
        net.add_edge(
            str(edge["source"]),
            str(edge["target"]),
            value=max(1.0, similarity * 8),
            title=f"Similarity: {similarity * 100:.1f}%",
            color={"color": "#585b70", "highlight": "#f5c2e7"},
            smooth={"type": "continuous"}
        )

    components.html(net.generate_html(), height=640, scrolling=False)

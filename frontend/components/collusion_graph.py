import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
import os

def render_collusion_graph(cluster_nodes: list, cluster_edges: list):
    st.markdown("### 🕸️ Collusion Network Analysis (Disjoint Set Union - DSU)")
    st.caption("Connected components represent student submission clusters identified via Path Compression DSU.")
    
    if not cluster_nodes:
        st.markdown("""
            <div class="empty-state-card">
                <div class="empty-state-icon">🕸️</div>
                <div class="empty-state-title">No Collusion Clusters Found</div>
                <div class="empty-state-desc">Upload submission batches to run Disjoint Set Union graph clustering. High similarity pairs will be rendered as connected graph networks.</div>
            </div>
        """, unsafe_allow_html=True)
        return

    net = Network(height="500px", width="100%", bgcolor="#0f172a", font_color="#f8fafc", directed=False)
    net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100)
    
    # Add Nodes
    for node in cluster_nodes:
        node_id = str(node["id"])
        label = node.get("label", node_id)
        cluster_id = node.get("cluster_id", 0)
        
        colors = ["#38bdf8", "#f43f5e", "#a855f7", "#34d399", "#fbbf24"]
        node_color = colors[cluster_id % len(colors)]
        
        net.add_node(
            node_id,
            label=label,
            title=f"Student: {label}\nCluster Root: #{cluster_id}",
            color=node_color,
            size=22
        )
        
    # Add Edges
    for edge in cluster_edges:
        net.add_edge(
            str(edge["source"]),
            str(edge["target"]),
            value=edge.get("weight", 1.0),
            title=f"Similarity: {edge.get('weight', 0):.1f}%",
            color="#475569"
        )
        
    # Render PyVis Graph in Memory (Avoid Windows Absolute Path Errno 22)
    try:
        html_content = net.generate_html()
        components.html(html_content, height=520, scrolling=False)
    except Exception:
        # Fallback to local relative file open if generate_html is unavailable
        filename = "temp_collusion_graph.html"
        try:
            net.save_graph(filename)
            with open(filename, "r", encoding="utf-8") as f:
                html_content = f.read()
            components.html(html_content, height=520, scrolling=False)
        finally:
            if os.path.exists(filename):
                os.remove(filename)
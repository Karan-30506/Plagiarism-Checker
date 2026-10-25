import streamlit as st

def render_metric_cards(similarity_pct: float, orig_bytes: int, comp_bytes: int, fingerprint_count: int):
    savings_pct = ((orig_bytes - comp_bytes) / orig_bytes * 100) if orig_bytes > 0 else 0.0
    saved_bytes = max(0, orig_bytes - comp_bytes)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Similarity Score Card
    with col1:
        score_class = "metric-sub-warning" if similarity_pct > 30 else "metric-sub"
        badge_text = "⚠️ High Match" if similarity_pct > 50 else ("⚡ Moderate" if similarity_pct > 20 else "✅ Low Match")
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Max Similarity Score</div>
                <div class="metric-value">{similarity_pct:.1f}%</div>
                <div class="{score_class}">{badge_text}</div>
            </div>
        """, unsafe_allow_html=True)
        
    # 2. Huffman Compression Savings
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Cold Archival Savings</div>
                <div class="metric-value">{savings_pct:.1f}%</div>
                <div class="metric-sub">💾 {saved_bytes / 1024:.1f} KB Saved (Huffman)</div>
            </div>
        """, unsafe_allow_html=True)

    # 3. Fingerprints Indexing Card
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Winnowing Fingerprints</div>
                <div class="metric-value">{fingerprint_count:,}</div>
                <div class="metric-sub">🌲 Compressed Trie Index</div>
            </div>
        """, unsafe_allow_html=True)

    # 4. Engine Data Structures Card
    with col4:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-title">Algorithmic Engine</div>
                <div class="metric-value" style="font-size: 1.35rem; padding-top: 6px;">Binomial + DSU</div>
                <div class="metric-sub">⚡ Kasai LCP & KMP Match</div>
            </div>
        """, unsafe_allow_html=True)
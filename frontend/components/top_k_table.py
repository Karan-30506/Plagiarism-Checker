import streamlit as st

def render_top_k_table(matches: list, on_select_match_callback=None):
    st.markdown("### 🏆 Top-K Ranked Matches (Max-Binomial Heap)")
    st.caption("Matches extracted from the Hot Compressed Trie Hash Index and ranked using a Binomial Heap.")
    
    if not matches:
        st.markdown("""
            <div class="empty-state-card">
                <div class="empty-state-icon">📄</div>
                <div class="empty-state-title">No Candidate Matches</div>
                <div class="empty-state-desc">No existing corpus documents matched above the similarity threshold.</div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    cols = st.columns([1, 3, 2, 2, 2])
    cols[0].markdown("**Rank**")
    cols[1].markdown("**Matched Document**")
    cols[2].markdown("**Similarity**")
    cols[3].markdown("**Matching Hashes**")
    cols[4].markdown("**Action**")
    
    st.divider()
    
    for idx, match in enumerate(matches, 1):
        c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
        score = match.get("similarity_score", 0.0)
        
        if score >= 50.0:
            badge_html = f"<span class='badge-danger'>{score:.1f}% Match</span>"
        elif score >= 20.0:
            badge_html = f"<span class='badge-warning'>{score:.1f}% Match</span>"
        else:
            badge_html = f"<span class='badge-success'>{score:.1f}% Match</span>"
            
        c1.markdown(f"**#{idx}**")
        c2.markdown(f"📄 `{match.get('filename', 'submission.cpp')}`")
        c3.markdown(badge_html, unsafe_allow_html=True)
        c4.markdown(f"`{match.get('matched_hash_count', 0)}` / `{match.get('total_hashes', 0)}`")
        
        if c5.button("🔍 View Diff", key=f"btn_diff_{idx}"):
            if on_select_match_callback:
                on_select_match_callback(match)
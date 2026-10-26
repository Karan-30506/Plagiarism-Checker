import streamlit as st

def render_top_k_table(matches: list, on_select_match_callback=None):
    st.markdown("### 🏆 Top-K Ranked Matches")
    st.caption(
        "Candidates share Winnowing fingerprints and are ranked by set-based Jaccard similarity."
    )
    
    if not matches:
        st.markdown("""
            <div class="empty-state-card">
                <div class="empty-state-icon">📄</div>
                <div class="empty-state-title">No Candidate Matches</div>
                <div class="empty-state-desc">No other document shared a Winnowing fingerprint with this source.</div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    cols = st.columns([1, 4, 2, 2])
    cols[0].markdown("**Rank**")
    cols[1].markdown("**Matched Document**")
    cols[2].markdown("**Similarity**")
    cols[3].markdown("**Action**")
    
    st.divider()
    
    for idx, match in enumerate(matches, 1):
        c1, c2, c3, c4 = st.columns([1, 4, 2, 2])
        score = match.get("similarity_score", 0.0) * 100
        
        if score >= 50.0:
            badge_html = f"<span class='badge-danger'>{score:.1f}% Match</span>"
        elif score >= 20.0:
            badge_html = f"<span class='badge-warning'>{score:.1f}% Match</span>"
        else:
            badge_html = f"<span class='badge-success'>{score:.1f}% Match</span>"
            
        c1.markdown(f"**#{idx}**")
        c2.markdown(f"📄 `{match.get('filename', 'submission.cpp')}`")
        c3.markdown(badge_html, unsafe_allow_html=True)
        
        if c4.button("🔍 View Diff", key=f"btn_diff_{match.get('report_id', idx)}"):
            if on_select_match_callback:
                on_select_match_callback(match)
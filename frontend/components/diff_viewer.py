import streamlit as st

def render_diff_viewer(source_filename: str, source_code: str, matched_filename: str, matched_code: str, matched_lines: set):
    st.markdown("### 🔀 Side-by-Side Code Diff Alignment (KMP + Suffix Tree)")
    st.caption("Highlighted red lines indicate exact or structural code segment matches across documents.")
    
    if not source_code and not matched_code:
        st.markdown("""
            <div class="empty-state-card">
                <div class="empty-state-icon">🔀</div>
                <div class="empty-state-title">No Code Diff Selected</div>
                <div class="empty-state-desc">Select a document match from the table above to view side-by-side line comparisons.</div>
            </div>
        """, unsafe_allow_html=True)
        return

    col1, col2 = st.columns(2)
    
    source_lines = source_code.splitlines() if source_code else ["// Source document empty or unavailable"]
    target_lines = matched_code.splitlines() if matched_code else ["// Target document empty or unavailable"]
    
    with col1:
        st.markdown(f"**Source Document:** `{source_filename}`")
        html_content = "<div class='diff-box'>"
        for idx, line in enumerate(source_lines, 1):
            is_match = idx in matched_lines
            line_cls = "diff-matched" if is_match else "diff-unmatched"
            escaped_line = line.replace("<", "&lt;").replace(">", "&gt;")
            html_content += f"<div class='diff-line {line_cls}'><span class='diff-line-number'>{idx}</span><span class='diff-line-content'>{escaped_line}</span></div>"
        html_content += "</div>"
        st.markdown(html_content, unsafe_allow_html=True)

    with col2:
        st.markdown(f"**Corpus Match:** `{matched_filename}`")
        html_content = "<div class='diff-box'>"
        for idx, line in enumerate(target_lines, 1):
            is_match = idx in matched_lines
            line_cls = "diff-matched" if is_match else "diff-unmatched"
            escaped_line = line.replace("<", "&lt;").replace(">", "&gt;")
            html_content += f"<div class='diff-line {line_cls}'><span class='diff-line-number'>{idx}</span><span class='diff-line-content'>{escaped_line}</span></div>"
        html_content += "</div>"
        st.markdown(html_content, unsafe_allow_html=True)
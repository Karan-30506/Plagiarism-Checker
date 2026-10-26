import streamlit as st
import requests
import os
import extra_streamlit_components as stx

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
API_REQUEST_TIMEOUT = (10, 300)
API_DIFF_TIMEOUT = (10, 180)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Plagiarism Engine Platform",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD CATPPUCCIN MOCHA CUSTOM CSS ---
css_path = os.path.join(os.path.dirname(__file__), "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from components.auth_ui import clear_auth_cookies, render_auth_ui, save_auth_cookies
from components.collusion_graph import render_collusion_graph
from components.diff_viewer import render_diff_viewer
from components.top_k_table import render_top_k_table

# --- COOKIE MANAGER FOR PERSISTENT AUTHENTICATION ---
cookie_manager = stx.CookieManager()

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "auth_restore_checked" not in st.session_state:
    st.session_state["auth_restore_checked"] = False
if "user_token" not in st.session_state:
    st.session_state["user_token"] = None
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0
if "last_ingested_results" not in st.session_state:
    st.session_state["last_ingested_results"] = None
if "detection_result" not in st.session_state:
    st.session_state["detection_result"] = None
if "detection_source_id" not in st.session_state:
    st.session_state["detection_source_id"] = None
if "selected_diff" not in st.session_state:
    st.session_state["selected_diff"] = None
if "detection_error" not in st.session_state:
    st.session_state["detection_error"] = None
if "show_diff_dialog" not in st.session_state:
    st.session_state["show_diff_dialog"] = False
if "auth_restore_error" not in st.session_state:
    st.session_state["auth_restore_error"] = None

# --- AUTO-LOGIN PERSISTENCE CHECK FROM BROWSER COOKIES ---
def set_authenticated_session(token, email, user_id):
    st.session_state["authenticated"] = True
    st.session_state["user_token"] = token
    st.session_state["user_email"] = email
    st.session_state["user_id"] = user_id


def get_auth_headers(token=None):
    auth_token = token or st.session_state.get("user_token")
    return {"Authorization": f"Bearer {auth_token}"} if auth_token else {}


def restore_authentication(saved_cookies):
    saved_token = saved_cookies.get("auth_token")
    saved_refresh_token = saved_cookies.get("refresh_token")
    saved_email = saved_cookies.get("user_email")
    saved_id = saved_cookies.get("user_id")

    if not saved_token or not saved_email:
        return

    try:
        validation = requests.get(
            f"{API_BASE_URL.rstrip('/')}/auth/me",
            headers=get_auth_headers(saved_token),
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        st.session_state["auth_restore_error"] = f"Could not verify the saved session: {e}"
        return

    if validation.ok:
        validated_user = validation.json()
        set_authenticated_session(
            saved_token,
            validated_user.get("email") or saved_email,
            validated_user.get("id") or saved_id
        )
        return

    if validation.status_code != 401:
        st.session_state["auth_restore_error"] = (
            f"Session validation failed with HTTP {validation.status_code}."
        )
        return

    if not saved_refresh_token:
        clear_auth_cookies(cookie_manager)
        return

    try:
        refresh_response = requests.post(
            f"{API_BASE_URL.rstrip('/')}/auth/refresh",
            json={"refresh_token": saved_refresh_token},
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        st.session_state["auth_restore_error"] = f"Could not refresh the saved session: {e}"
        return

    if not refresh_response.ok:
        if refresh_response.status_code == 401:
            clear_auth_cookies(cookie_manager)
        else:
            st.session_state["auth_restore_error"] = (
                f"Session refresh failed with HTTP {refresh_response.status_code}."
            )
        return

    refreshed_auth = refresh_response.json()
    save_auth_cookies(cookie_manager, refreshed_auth, saved_email)
    set_authenticated_session(
        refreshed_auth["access_token"],
        saved_email,
        refreshed_auth["user_id"]
    )


if not st.session_state["authenticated"] and not st.session_state["auth_restore_checked"]:
    saved_cookies = cookie_manager.get_all()
    if saved_cookies.get("auth_token") and saved_cookies.get("user_email"):
        restore_authentication(saved_cookies)
        st.session_state["auth_restore_checked"] = True

# Navigation callbacks
def navigate_to_vault():
    st.session_state["nav_selection"] = "💾 Storage Vault"

def navigate_to_inspection():
    st.session_state["nav_selection"] = "📊 Plagiarism Inspection"

# --- SIDEBAR & NAVIGATION ---
st.sidebar.markdown("## 🔎 Plagiarism Engine")
st.sidebar.caption("Two-Tier C++ Ingestion Architecture")

if st.session_state["authenticated"]:
    st.sidebar.markdown(f"👤 **Logged in as:**\n`{st.session_state.get('user_email', 'User')}`")
    st.sidebar.divider()
    
    page = st.sidebar.radio(
        "Navigation",
        ["📤 Document Ingestion", "💾 Storage Vault", "📊 Plagiarism Inspection", "🕸️ Collusion Analysis"],
        key="nav_selection"
    )
    
    st.sidebar.divider()
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        clear_auth_cookies(cookie_manager)
        st.session_state["authenticated"] = False
        st.session_state["user_token"] = None
        st.session_state["user_email"] = None
        st.session_state["user_id"] = None
        st.session_state["auth_restore_checked"] = True
        st.session_state["last_ingested_results"] = None
        st.session_state["selected_diff"] = None
        st.session_state["show_diff_dialog"] = False
        st.rerun()
else:
    page = "Auth"

if st.session_state["auth_restore_error"] and not st.session_state["authenticated"]:
    st.error(st.session_state["auth_restore_error"])
    if st.button("Retry session restoration"):
        st.session_state["auth_restore_error"] = None
        st.session_state["auth_restore_checked"] = False
        st.rerun()

# --- MODAL COMPONENT 1: VIEW CONTENT ---
def render_document_modal_content(doc_id: str, filename: str):
    st.caption(f"Document UUID: `{doc_id}` | Bucket: `Supabase Storage (compressed_docs)`")
    with st.spinner("Downloading binary payload & executing C++ Huffman Decompression..."):
        try:
            res = requests.get(
                f"{API_BASE_URL}/documents/{doc_id}/content",
                headers=get_auth_headers(),
                timeout=API_REQUEST_TIMEOUT
            )
            if res.status_code == 200:
                data = res.json()
                orig_kb = data["original_size"] / 1024
                comp_kb = data["compressed_size"] / 1024
                savings = ((data["original_size"] - data["compressed_size"]) / data["original_size"] * 100) if data["original_size"] > 0 else 0.0
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Original Size", f"{orig_kb:.2f} KB")
                c2.metric("Cold Storage (.bin)", f"{comp_kb:.2f} KB")
                c3.metric("Huffman Compression", f"{savings:.1f}% Saved")
                
                st.divider()
                st.markdown(f"**Filename:** `{filename}`")
                
                ext = filename.split(".")[-1].lower() if "." in filename else "text"
                lang_map = {
                    "cpp": "cpp", "hpp": "cpp", "c": "c", "h": "c", 
                    "py": "python", "java": "java", "cs": "csharp", 
                    "js": "javascript", "ts": "typescript", "sql": "sql", 
                    "json": "json", "html": "html", "css": "css"
                }
                st.code(data["content"], language=lang_map.get(ext, "text"), line_numbers=True)
            else:
                st.error(f"Failed to fetch content: {res.json().get('detail', 'Server error')}")
        except Exception as e:
            st.error(f"Backend Connection Error: {str(e)}")

# --- MODAL COMPONENT 2: RENAME DOCUMENT ---
def render_rename_modal_content(doc_id: str, current_filename: str):
    st.markdown("### ✏️ Rename Document")
    st.caption(f"Updating database record for `{current_filename}`")
    
    new_name = st.text_input("New Filename", value=current_filename, key=f"input_rename_{doc_id}")
    
    if st.button("💾 Save Changes", type="primary", use_container_width=True):
        if not new_name.strip():
            st.error("Filename cannot be empty.")
        else:
            try:
                res = requests.patch(
                    f"{API_BASE_URL}/documents/{doc_id}",
                    headers=get_auth_headers(),
                    json={"new_filename": new_name.strip()},
                    timeout=10
                )
                if res.status_code == 200:
                    st.success("Filename updated!")
                    st.rerun()
                else:
                    st.error(f"Update failed: {res.json().get('detail', 'Error')}")
            except Exception as e:
                st.error(f"Error connecting to backend: {str(e)}")

@st.dialog("📄 Decompressed Document Content", width="large")
def open_view_modal(doc_id: str, filename: str):
    render_document_modal_content(doc_id, filename)


@st.dialog("✏️ Edit Document Name", width="medium")
def open_rename_modal(doc_id: str, current_filename: str):
    render_rename_modal_content(doc_id, current_filename)


@st.dialog("Code comparison", width="large")
def open_diff_dialog(diff_payload):
    render_diff_viewer(
        diff_payload["source_filename"],
        diff_payload["source_text"],
        diff_payload["matched_filename"],
        diff_payload["matched_text"],
        set(diff_payload["matched_source_lines"]),
        set(diff_payload["matched_target_lines"])
    )


# --- ROUTING LOGIC ---

if not st.session_state["authenticated"]:
    render_auth_ui(cookie_manager)

# -----------------------------------------------------------------------------
# PAGE 1: DOCUMENT INGESTION
# -----------------------------------------------------------------------------
elif page == "📤 Document Ingestion":
    st.title("📤 Document Ingestion Pipeline")
    st.caption("Upload source code, text documents, or submission archives (.ZIP) for simultaneous C++ Huffman compression and Winnowing fingerprinting.")
    
    uploader_key = f"file_uploader_{st.session_state['uploader_key']}"
    
    uploaded_files = st.file_uploader(
        "Drop files or a .ZIP archive for dual-stream processing",
        type=["cpp", "hpp", "c", "h", "py", "java", "cs", "js", "ts", "html", "css", "txt", "md", "sql", "json", "pdf", "docx", "zip"],
        accept_multiple_files=True,
        key=uploader_key
    )
    
    col1, col2 = st.columns([2.5, 1])
    
    with col1:
        if uploaded_files:
            st.success(f"📁 **{len(uploaded_files)} file(s)** staged in ingestion buffer.")
            
            staged_info = []
            for f in uploaded_files:
                staged_info.append({
                    "Filename": f.name,
                    "Size": f"{f.size / 1024:.2f} KB",
                    "MIME Type": f.type or "Text/Source"
                })
            st.dataframe(staged_info, use_container_width=True)
            
            if st.button("🚀 Execute C++ Dual-Stream Ingestion", type="primary", use_container_width=True):
                files_payload = [
                    ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
                    for f in uploaded_files
                ]
                
                with st.spinner("Processing: Running C++ Huffman Compression & Winnowing Fingerprinting..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/documents/upload",
                            headers=get_auth_headers(),
                            files=files_payload,
                            timeout=(10, 600)
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.balloons()
                            st.session_state["last_ingested_results"] = data.get("documents", [])
                            st.session_state["uploader_key"] += 1
                            st.rerun()
                        else:
                            st.error(f"Ingestion Failed: {response.json().get('detail', 'Error')}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Backend Connection Error: {str(e)}")

        if st.session_state["last_ingested_results"]:
            st.success("✅ **Batch Ingestion Complete!** Staged buffer cleared and records persisted.")
            st.markdown("### ⚡ Latest Ingestion Stream Results")
            
            formatted_results = []
            for doc in st.session_state["last_ingested_results"]:
                orig_sz = doc["original_size"]
                comp_sz = doc["compressed_size"]
                savings = ((orig_sz - comp_sz) / orig_sz * 100) if orig_sz > 0 else 0.0
                
                formatted_results.append({
                    "Document ID": doc["document_id"][:8] + "...",
                    "Filename": doc["filename"],
                    "Original Size": f"{orig_sz / 1024:.2f} KB",
                    "Compressed (.bin)": f"{comp_sz / 1024:.2f} KB",
                    "Huffman Savings": f"{savings:.1f}%",
                    "Winnowing Hashes": doc["fingerprint_count"],
                    "Status": "Persisted in Postgres & Storage"
                })
            
            st.dataframe(formatted_results, use_container_width=True)
            
            btn_c1, btn_c2 = st.columns(2)
            btn_c1.button("💾 View Storage Vault Records", on_click=navigate_to_vault, use_container_width=True)
            btn_c2.button("📊 Proceed to Plagiarism Inspection", on_click=navigate_to_inspection, use_container_width=True)

    with col2:
        st.info("""
        **Dual-Stream Ingestion Flow:**
        
        1. **Text Normalization:** Strips comments, whitespaces & extracts text from PDF/DOCX/ZIP.
        2. **Stream A (Huffman):** Constructs Min-Heap prefix tree & packs text into binary `.bin` uploaded to Supabase Storage.
        3. **Stream B (Winnowing):** Generates Rabin-Karp rolling hashes & picks window minima inserted into PostgreSQL.
        """)

# -----------------------------------------------------------------------------
# PAGE 2: STORAGE VAULT (VIEW, RENAME & DELETE)
# -----------------------------------------------------------------------------
elif page == "💾 Storage Vault":
    st.title("💾 Storage & Database Vault")
    st.caption("Live metrics and records fetched from PostgreSQL tables and Supabase Storage bucket.")
    
    with st.spinner("Fetching database records..."):
        try:
            res = requests.get(f"{API_BASE_URL}/documents/my-documents", headers=get_auth_headers(), timeout=10)
            
            if res.status_code == 200:
                docs = res.json()
                
                if not docs:
                    st.markdown("""
                        <div class="empty-state-card">
                            <div class="empty-state-icon">💾</div>
                            <div class="empty-state-title">Storage Vault Empty</div>
                            <div class="empty-state-desc">No compressed documents found in your record. Go to <b>Document Ingestion</b> to upload files.</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    total_orig = sum(d["original_size"] for d in docs)
                    total_comp = sum(d["compressed_size"] for d in docs)
                    total_saved = max(0, total_orig - total_comp)
                    savings_pct = (total_saved / total_orig * 100) if total_orig > 0 else 0.0
                    
                    # Storage Metrics Header
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Indexed Documents", f"{len(docs)} Files")
                        st.caption("Persisted in PostgreSQL `documents` table")
                    with col2:
                        st.metric("Cold Storage Size (.bin)", f"{total_comp / 1024:.2f} KB", delta=f"-{savings_pct:.1f}% Savings")
                        st.caption("Stored in Supabase `compressed_docs` bucket")
                    with col3:
                        st.metric("Total Raw Uncompressed Size", f"{total_orig / 1024:.2f} KB")
                        st.caption(f"💾 {total_saved / 1024:.2f} KB total space saved")
                    
                    st.divider()
                    st.markdown("### 📜 Persisted Document Inventory")
                    
                    # High-Legibility Column Headers
                    header_cols = st.columns([1.5, 3.5, 1.8, 1.8, 1.8, 1.2, 1.2, 1.2])
                    header_cols[0].markdown("<span class='vault-header-text'>ID</span>", unsafe_allow_html=True)
                    header_cols[1].markdown("<span class='vault-header-text'>FILENAME</span>", unsafe_allow_html=True)
                    header_cols[2].markdown("<span class='vault-header-text'>RAW SIZE</span>", unsafe_allow_html=True)
                    header_cols[3].markdown("<span class='vault-header-text'>COMPRESSED</span>", unsafe_allow_html=True)
                    header_cols[4].markdown("<span class='vault-header-text'>HUFFMAN SAVINGS</span>", unsafe_allow_html=True)
                    header_cols[5].markdown("<span class='vault-header-text'>VIEW</span>", unsafe_allow_html=True)
                    header_cols[6].markdown("<span class='vault-header-text'>EDIT</span>", unsafe_allow_html=True)
                    header_cols[7].markdown("<span class='vault-header-text'>DELETE</span>", unsafe_allow_html=True)
                    st.divider()
                    
                    # Row Rendering
                    for idx, d in enumerate(docs, 1):
                        orig = d["original_size"]
                        comp = d["compressed_size"]
                        sav = ((orig - comp) / orig * 100) if orig > 0 else 0.0
                        
                        r_col1, r_col2, r_col3, r_col4, r_col5, r_col6, r_col7, r_col8 = st.columns([1.5, 3.5, 1.8, 1.8, 1.8, 1.2, 1.2, 1.2])
                        
                        r_col1.markdown(f"<span class='vault-cell-text'><code>{d['id'][:8]}...</code></span>", unsafe_allow_html=True)
                        r_col2.markdown(f"<span class='vault-cell-text'>📄 <b>{d['filename']}</b></span>", unsafe_allow_html=True)
                        r_col3.markdown(f"<span class='vault-cell-text'><code>{orig:,} B</code></span>", unsafe_allow_html=True)
                        r_col4.markdown(f"<span class='vault-cell-text'><code>{comp:,} B</code></span>", unsafe_allow_html=True)
                        r_col5.markdown(f"<span class='badge-mocha-green'>-{sav:.1f}%</span>", unsafe_allow_html=True)
                        
                        # View Code
                        if r_col6.button("👁️", key=f"btn_view_{d['id']}", help="View Decompressed Code"):
                            open_view_modal(d["id"], d["filename"])
                            
                        # Rename Document
                        if r_col7.button("✏️", key=f"btn_edit_{d['id']}", help="Rename Document"):
                            open_rename_modal(d["id"], d["filename"])
                            
                        # Delete Document
                        if r_col8.button("🗑️", key=f"btn_del_{d['id']}", help="Delete Document"):
                            try:
                                del_res = requests.delete(f"{API_BASE_URL}/documents/{d['id']}", headers=get_auth_headers(), timeout=10)
                                if del_res.status_code == 200:
                                    st.toast(f"Deleted {d['filename']}", icon="🗑️")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete document.")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            else:
                st.error("Failed to fetch document inventory from database.")
        except requests.exceptions.RequestException as e:
            st.error(f"Database Connection Error: {str(e)}")

# -----------------------------------------------------------------------------
# PAGE 3: PLAGIARISM INSPECTION
# -----------------------------------------------------------------------------
elif page == "📊 Plagiarism Inspection":
    st.title("📊 Plagiarism Inspection & Code Diffs")
    st.caption("Compare an uploaded document against the indexed corpus using Winnowing fingerprints, the compressed trie, and Top-K ranking.")

    documents_load_failed = False
    try:
        documents_response = requests.get(
            f"{API_BASE_URL}/documents/my-documents",
            headers=get_auth_headers(),
            timeout=15
        )
        documents_response.raise_for_status()
        documents = documents_response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not load your documents: {e}")
        documents = []
        documents_load_failed = True

    if not documents and not documents_load_failed:
        st.info("Upload at least one document before running plagiarism detection.")
    elif documents:
        documents_by_id = {document["id"]: document for document in documents}
        source_doc_id = st.selectbox(
            "Document to check",
            options=list(documents_by_id),
            format_func=lambda doc_id: (
                f"{documents_by_id[doc_id]['filename']} ({doc_id[:8]})"
            )
        )
        maximum_matches = max(len(documents) - 1, 1)
        top_k = st.number_input(
            "Maximum number of matches",
            min_value=1,
            max_value=maximum_matches,
            value=maximum_matches,
            step=1
        )
        st.caption("The default returns all candidate matches. Lower this value to limit results.")

        if st.button("Run plagiarism detection", type="primary"):
            st.session_state["detection_result"] = None
            st.session_state["selected_diff"] = None
            st.session_state["show_diff_dialog"] = False
            st.session_state["detection_error"] = None
            with st.spinner("Building the fingerprint index and ranking candidates..."):
                try:
                    check_payload: dict[str, str | int] = {
                        "source_doc_id": source_doc_id
                    }
                    if top_k < maximum_matches:
                        check_payload["top_k"] = top_k
                    response = requests.post(
                        f"{API_BASE_URL}/reports/check",
                        headers=get_auth_headers(),
                        json=check_payload,
                        timeout=API_REQUEST_TIMEOUT
                    )
                    response.raise_for_status()
                    st.session_state["detection_result"] = response.json()
                    st.session_state["detection_source_id"] = source_doc_id
                except requests.exceptions.RequestException as e:
                    detail = e
                    if e.response is not None:
                        try:
                            detail = e.response.json().get("detail", e)
                        except ValueError:
                            detail = e.response.text or e
                    st.session_state["detection_error"] = str(detail)

        if st.session_state["detection_error"]:
            st.error(f"Plagiarism detection failed: {st.session_state['detection_error']}")

        detection_result = st.session_state["detection_result"]
        if detection_result and st.session_state["detection_source_id"] == source_doc_id:
            if detection_result.get("message"):
                st.info(detection_result["message"])

            matches = detection_result.get("top_k_matches", [])
            if matches:
                st.subheader(f"Matches for {detection_result['source_filename']}")

                def load_diff(match):
                    st.session_state["selected_diff"] = None
                    st.session_state["detection_error"] = None
                    try:
                        diff_response = requests.get(
                            f"{API_BASE_URL}/reports/diff",
                            headers=get_auth_headers(),
                            params={"report_id": match["report_id"]},
                            timeout=API_DIFF_TIMEOUT
                        )
                        diff_response.raise_for_status()
                        st.session_state["selected_diff"] = diff_response.json()
                        st.session_state["show_diff_dialog"] = True
                    except requests.exceptions.RequestException as e:
                        detail = e
                        if e.response is not None:
                            try:
                                detail = e.response.json().get("detail", e)
                            except ValueError:
                                detail = e.response.text or e
                        st.session_state["detection_error"] = str(detail)

                render_top_k_table(matches, on_select_match_callback=load_diff)

                if st.session_state["detection_error"]:
                    st.error(f"Could not load the document diff: {st.session_state['detection_error']}")

                selected_diff = st.session_state["selected_diff"]
                if selected_diff and st.session_state["show_diff_dialog"]:
                    st.session_state["show_diff_dialog"] = False
                    open_diff_dialog(selected_diff)
            elif not detection_result.get("message"):
                st.info("No matching documents were found in the indexed corpus.")

# -----------------------------------------------------------------------------
# PAGE 4: COLLUSION ANALYSIS
# -----------------------------------------------------------------------------
elif page == "🕸️ Collusion Analysis":
    st.title("🕸️ Collusion Network Analysis")
    st.caption(
        "Explore groups of documents connected by high-similarity reports. "
        "Each edge is a saved source-to-match result; DSU groups documents into connected clusters. "
        "Rebuild reports to compare every document you own, not just documents checked previously."
    )
    if st.button("Rebuild reports for all my documents", type="primary"):
        with st.spinner("Comparing your documents and refreshing graph links..."):
            try:
                rebuild_response = requests.post(
                    f"{API_BASE_URL}/reports/collusion-graph/rebuild",
                    headers=get_auth_headers(),
                    timeout=API_REQUEST_TIMEOUT
                )
                rebuild_response.raise_for_status()
                rebuild_summary = rebuild_response.json()
                st.success(
                    f"Compared {rebuild_summary['source_documents_compared']} documents; "
                    f"created {rebuild_summary['reports_created']} links, "
                    f"updated {rebuild_summary['reports_updated']}, and removed "
                    f"{rebuild_summary['stale_reports_removed']} stale links."
                )
            except requests.exceptions.RequestException as e:
                detail = e
                if e.response is not None:
                    try:
                        detail = e.response.json().get("detail", e)
                    except ValueError:
                        detail = e.response.text or e
                st.error(f"Could not rebuild document comparisons: {detail}")
            else:
                st.rerun()

    threshold = st.slider(
        "Minimum similarity for a collusion link",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.05,
        format="%.2f"
    )
    try:
        graph_response = requests.get(
            f"{API_BASE_URL}/reports/collusion-graph",
            headers=get_auth_headers(),
            params={"threshold": threshold},
            timeout=API_REQUEST_TIMEOUT
        )
        graph_response.raise_for_status()
        graph_data = graph_response.json()
        st.caption(
            f"{graph_data.get('num_clusters', 0)} connected cluster(s), "
            f"{len(graph_data.get('nodes', []))} document(s), "
            f"{len(graph_data.get('edges', []))} qualifying link(s)."
        )
        render_collusion_graph(
            graph_data.get("nodes", []),
            graph_data.get("edges", [])
        )
    except requests.exceptions.RequestException as e:
        detail = e
        if e.response is not None:
            try:
                detail = e.response.json().get("detail", e)
            except ValueError:
                detail = e.response.text or e
        st.error(f"Could not load collusion analysis: {detail}")
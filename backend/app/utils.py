import io
import re
import zipfile
from pypdf import PdfReader
from docx import Document as DocxDocument

SUPPORTED_EXTENSIONS = {
    ".cpp", ".c", ".hpp", ".h", ".py", ".java", ".js", ".ts", ".cs", 
    ".html", ".css", ".txt", ".md", ".sql", ".json", ".pdf", ".docx"
}

def normalize_text(raw_text: str) -> str:
    """Strips comments, extra whitespaces, and normalizes text for clean fingerprinting."""
    if not raw_text:
        return ""
    # Remove C/C++/Java single-line and multi-line comments
    text = re.sub(r'//.*?\n|/\*.*?\*/', ' ', raw_text, flags=re.DOTALL)
    # Remove Python single-line comments
    text = re.sub(r'#.*?\n', ' ', text)
    # Collapse multiple whitespace characters into a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_text_from_bytes(filename: str, file_bytes: bytes) -> str:
    """Extracts raw text content based on file extension."""
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    
    if ext in {".pdf"}:
        reader = PdfReader(io.BytesIO(file_bytes))
        extracted_pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_pages.append(text)
        return "\n".join(extracted_pages)

    elif ext in {".docx"}:
        doc = DocxDocument(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    else:
        # Standard source code and plain text files
        return file_bytes.decode("utf-8", errors="ignore")


def process_uploaded_payload(filename: str, file_bytes: bytes) -> list[dict]:
    """
    Handles single files or unpacks .zip archives recursively.
    Returns list of dicts: [{"filename": "main.cpp", "raw_text": "...", "normalized_text": "..."}, ...]
    """
    results = []
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""

    if ext == ".zip":
        with zipfile.ZipFile(io.BytesIO(file_bytes), 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    continue
                inner_name = file_info.filename
                inner_ext = "." + inner_name.split(".")[-1].lower() if "." in inner_name else ""
                
                if inner_ext in SUPPORTED_EXTENSIONS:
                    inner_bytes = zip_ref.read(file_info)
                    raw_text = extract_text_from_bytes(inner_name, inner_bytes)
                    if raw_text.strip():
                        results.append({
                            "filename": inner_name,
                            "raw_text": raw_text,
                            "normalized_text": normalize_text(raw_text)
                        })
    elif ext in SUPPORTED_EXTENSIONS:
        raw_text = extract_text_from_bytes(filename, file_bytes)
        if raw_text.strip():
            results.append({
                "filename": filename,
                "raw_text": raw_text,
                "normalized_text": normalize_text(raw_text)
            })

    return results
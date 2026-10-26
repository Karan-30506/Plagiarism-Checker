import subprocess
import os
import tempfile

BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build", "bin"))
CLI_EXE = os.path.join(BUILD_DIR, "plagiarism_cli.exe" if os.name == "nt" else "plagiarism_cli")


def compress_text_huffman(text: str) -> tuple[bytes, int, int]:
    """Invokes compiled C++ Huffman CLI to compress text."""
    if not os.path.exists(CLI_EXE):
        raise FileNotFoundError(f"C++ Engine executable not found at '{CLI_EXE}'.")

    fd_in, in_path = tempfile.mkstemp(suffix=".txt")
    fd_out, out_path = tempfile.mkstemp(suffix=".bin")

    try:
        with os.fdopen(fd_in, "wb") as f_in:
            f_in.write(text.encode("utf-8"))
        os.close(fd_out)

        cmd = [CLI_EXE, "compress", in_path, out_path]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        with open(out_path, "rb") as f_out:
            compressed_bytes = f_out.read()

        orig_size = len(text.encode("utf-8"))
        comp_size = len(compressed_bytes)

        return compressed_bytes, orig_size, comp_size
    finally:
        if os.path.exists(in_path): os.remove(in_path)
        if os.path.exists(out_path): os.remove(out_path)


def decompress_text_huffman(compressed_bytes: bytes) -> str:
    """Invokes compiled C++ Huffman CLI to decompress binary back to text."""
    if not os.path.exists(CLI_EXE):
        raise FileNotFoundError(f"C++ Engine executable not found at '{CLI_EXE}'.")

    fd_in, in_path = tempfile.mkstemp(suffix=".bin")
    fd_out, out_path = tempfile.mkstemp(suffix=".txt")

    try:
        with os.fdopen(fd_in, "wb") as f_in:
            f_in.write(compressed_bytes)
        os.close(fd_out)

        cmd = [CLI_EXE, "decompress", in_path, out_path]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        with open(out_path, "rb") as f_out:
            decompressed_bytes = f_out.read()

        return decompressed_bytes.decode("utf-8")
    finally:
        if os.path.exists(in_path): os.remove(in_path)
        if os.path.exists(out_path): os.remove(out_path)


def get_winnow_fingerprints(text: str, k: int = 10, w: int = 4) -> list[dict]:
    """
    Invokes compiled C++ Winnowing CLI to extract Rabin-Karp fingerprints.
    Returns list of dicts: [{"hash": 1234567, "position": 0}, ...]
    """
    if not os.path.exists(CLI_EXE):
        raise FileNotFoundError(f"C++ Engine executable not found at '{CLI_EXE}'.")

    fd_in, in_path = tempfile.mkstemp(suffix=".txt")
    fd_out, out_path = tempfile.mkstemp(suffix=".hashes")

    try:
        with os.fdopen(fd_in, "wb") as f_in:
            f_in.write(text.encode("utf-8"))
        os.close(fd_out)

        cmd = [CLI_EXE, "winnow", in_path, out_path, str(k), str(w)]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        fingerprints = []
        with open(out_path, "r", encoding="utf-8") as f_out:
            for line in f_out:
                parts = line.strip().split()
                if len(parts) == 2:
                    fingerprints.append({
                        "hash": int(parts[0]),
                        "position": int(parts[1])
                    })

        return fingerprints
    finally:
        if os.path.exists(in_path): os.remove(in_path)
        if os.path.exists(out_path): os.remove(out_path)


def query_trie_top_k(
    query_fingerprints: list[dict],
    corpus_index: dict[str, list[int]],
    top_k: int = 10
) -> list[dict]:
    """
    Invokes compiled C++ CLI 'query' mode which:
      1. Builds a Compressed Radix Trie from all corpus fingerprint hashes.
      2. Looks up each query hash in O(L) time.
      3. Ranks candidate documents by Jaccard similarity using a Max-Binomial Heap.
      4. Returns the Top-K matches.

    Args:
        query_fingerprints: list of {"hash": int, "position": int} dicts from winnowing.
        corpus_index: {doc_id: [hash1, hash2, ...]} mapping for all corpus documents.
        top_k: number of top candidates to return.

    Returns:
        list of {"doc_id": str, "similarity_score": float} sorted descending by score.
    """
    if not os.path.exists(CLI_EXE):
        raise FileNotFoundError(f"C++ Engine executable not found at '{CLI_EXE}'.")

    if not query_fingerprints or not corpus_index:
        return []

    import json

    # Write query hashes file: "hash position\n" per line
    fd_q, query_path = tempfile.mkstemp(suffix=".hashes")
    # Write corpus index file: "doc_id hash1 hash2 ...\n" per line
    fd_c, corpus_path = tempfile.mkstemp(suffix=".corpus")
    # Output JSON file
    fd_o, output_path = tempfile.mkstemp(suffix=".json")

    try:
        with os.fdopen(fd_q, "w", encoding="utf-8") as fq:
            for fp in query_fingerprints:
                fq.write(f"{fp['hash']} {fp['position']}\n")

        with os.fdopen(fd_c, "w", encoding="utf-8") as fc:
            for doc_id, hashes in corpus_index.items():
                hash_str = " ".join(str(h) for h in hashes)
                fc.write(f"{doc_id} {hash_str}\n")

        os.close(fd_o)

        cmd = [CLI_EXE, "query", query_path, corpus_path, output_path, str(top_k)]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        with open(output_path, "r", encoding="utf-8") as fo:
            results = json.load(fo)

        return results  # list of {"doc_id": ..., "similarity_score": ...}

    finally:
        if os.path.exists(query_path):  os.remove(query_path)
        if os.path.exists(corpus_path): os.remove(corpus_path)
        if os.path.exists(output_path): os.remove(output_path)

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
```bash
├── README.md                       # Documentation, architecture breakdown & setup guide
├── .gitignore                      # Git ignore rules (build dirs, .env, __pycache__)
│
├── backend/                        # Complete Backend Service (FastAPI + C++ Core Engine)
│   ├── CMakeLists.txt              # CMake build configuration for C++ core engine
│   ├── alembic.ini                 # Alembic database migration configuration
│   ├── .env.example                # Template for Supabase credentials & JWT secrets
│   ├── requirements.txt            # Python dependencies (FastAPI, Alembic, Supabase, PyVis, etc.)
│   │
│   ├── alembic/                    # Alembic Database Migrations
│   │   ├── env.py                  # Migration environment setup script
│   │   ├── script.py.mako          # Migration script template
│   │   └── versions/               # Schema version migration scripts
│   │       └── 0001_initial_schema.py
│   │
│   ├── cpp_engine/                 # Core C++ Data Structures Engine
│   │   ├── include/                # Header files
│   │   │   ├── huffman.hpp         # Min-Heap & Huffman Tree (Cold Archival Compression)
│   │   │   ├── winnowing.hpp       # Rabin-Karp Rolling Hash & Winnowing Fingerprinting
│   │   │   ├── compressed_trie.hpp # Compressed Trie (Radix Tree) for Hot Hash Indexing
│   │   │   ├── suffix_tree.hpp     # Generalized Suffix Tree, Suffix Array & LCP Array
│   │   │   ├── kmp.hpp             # KMP Matcher with LPS Array for Exact Line Alignment
│   │   │   ├── binomial_heap.hpp   # Max-Binomial Heap for Top-K Candidate Ranking
│   │   │   └── dsu.hpp             # Disjoint Set Union (Path Compression/Rank) & Graph
│   │   │
│   │   ├── src/                    # C++ Implementation source files
│   │   │   ├── huffman.cpp
│   │   │   ├── winnowing.cpp
│   │   │   ├── compressed_trie.cpp
│   │   │   ├── suffix_tree.cpp
│   │   │   ├── kmp.cpp
│   │   │   ├── binomial_heap.cpp
│   │   │   └── dsu.cpp
│   │   │
│   │   └── main_cli.cpp            # CLI Engine Interface (JSON IPC Bridge)
│   │
│   └── app/                        # FastAPI Application Modules
│       ├── __init__.py
│       ├── main.py                 # FastAPI application entry point
│       ├── config.py               # Environment configuration & Settings loader
│       ├── database.py             # DB connection engine (SQLAlchemy/Alembic bridge)
│       ├── models.py               # ORM Models (Documents, Reports, Fingerprints)
│       ├── schemas.py              # Pydantic request/response validation schemas
│       ├── auth.py                 # Supabase Auth / JWT verification middleware
│       ├── supabase_client.py      # Supabase Client setup (DB Queries + Storage Bucket API)
│       ├── engine_bridge.py        # Python-to-C++ subprocess & JSON IPC wrapper
│       ├── utils.py                # Text normalization & ZIP archive extraction helpers
│       └── routes/                 # FastAPI REST API Endpoints
│           ├── __init__.py
│           ├── auth.py             # Login, Signup, Session routes
│           ├── upload.py           # Document upload & batch checking route
│           └── reports.py          # Plagiarism reports, diff views & collusion graphs
│
├── frontend/                       # Python Streamlit User Interface
│   ├── app.py                      # Streamlit entry point (Page routing & Session state)
│   ├── components/                 # UI Visualizers & Rendering Modules
│   │   ├── auth_ui.py              # Login & Signup Streamlit components
│   │   ├── metrics.py              # Plagiarism Score & Huffman Storage Savings cards
│   │   ├── top_k_table.py          # Binomial Heap Top-K match table component
│   │   ├── diff_viewer.py          # Side-by-Side KMP/Suffix Tree highlighted diff view
│   │   └── collusion_graph.py      # PyVis dynamic DSU network graph visualizer
│   │
│   └── styles/
│       └── custom.css              # Custom CSS for highlighted code diffs & score cards
│
└── database/                       # Raw SQL Backup & Schema Reference
    └── schema.sql                  # Initial raw SQL schema reference for Supabase SQL Editor
```

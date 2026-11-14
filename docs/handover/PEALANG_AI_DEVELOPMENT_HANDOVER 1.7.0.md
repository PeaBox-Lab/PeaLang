# PeaLang v1.7.0 — ONNX model export and vector/RAG primitives

## Milestone: v1.7.0

### What was done
- Added `pealang/vector_rag.py` with ONNX export and vector/RAG primitives
- `model_to_onnx`, `tree_to_onnx`, `onnx_export_json` — ONNX model export
- `create_vector`, `cosine_similarity`, `euclidean_distance`, `dot_product` — vector embeddings
- `chunk_text`, `chunk_by_sentences` — semantic chunking
- `bm25_score`, `hybrid_search` — hybrid search
- `VectorStore` — in-memory vector store for RAG
- Registered in `analysis` and `stats`/`std.stats` namespaces
- Added `tests/test_vector_rag_v170.py` (14 tests) and `tests/test_use_cases_v170.py` (1 test)
- Added `docs/VECTOR_RAG.md` and `help/VECTOR_RAG.md`
- Added `examples/use_cases/41_vector_rag.pea`
- Version bumped to 1.7.0

### Test status
- 1075 tests passing

### Next steps (v1.8.0)
- Interactive Web Data IDE and reactive notebook server
- Reactive cell execution, visual SQL/DataFrame inspectors
- One-click publishing of .pea scripts as interactive web apps
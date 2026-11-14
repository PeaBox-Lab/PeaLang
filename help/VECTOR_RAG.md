# ONNX model export and vector/RAG primitives (v1.7.0)

PeaLang provides ONNX model export and vector/RAG primitives.

## Key functions

- `analysis.model_to_onnx(model, model_type)` — ONNX export
- `analysis.tree_to_onnx(tree, feature_names)` — tree to ONNX
- `analysis.onnx_export_json(model, path)` — export to file
- `analysis.create_vector(values, metadata)` — vector embedding
- `analysis.cosine_similarity(a, b)` — cosine similarity
- `analysis.chunk_text(text, chunk_size, overlap)` — text chunking
- `analysis.bm25_score(query, document)` — BM25 scoring
- `analysis.hybrid_search(query, documents, ...)` — hybrid search
- `analysis.VectorStore()` — vector store
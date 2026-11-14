# ONNX model export and vector/RAG primitives (v1.7.0)

PeaLang provides ONNX model export and vector/RAG primitives.

## ONNX export

- `model_to_onnx(model, model_type)` — convert model to ONNX representation
- `tree_to_onnx(tree, feature_names)` — convert decision tree to ONNX
- `onnx_export_json(model, path)` — export model as ONNX JSON

## Vector embeddings

- `create_vector(values, metadata)` — create a vector embedding
- `cosine_similarity(a, b)` — cosine similarity
- `euclidean_distance(a, b)` — euclidean distance
- `dot_product(a, b)` — dot product

## Semantic chunking

- `chunk_text(text, chunk_size, overlap)` — split text into chunks
- `chunk_by_sentences(text, max_sentences)` — split by sentences

## Hybrid search

- `bm25_score(query, document)` — BM25 scoring
- `hybrid_search(query, documents, embeddings, query_embedding, alpha, top_k)` — hybrid search

## Vector store

- `VectorStore()` — in-memory vector store
- `.add(text, embedding, metadata)` — add vector
- `.search(query_embedding, top_k)` — search
- `.hybrid_search(query, query_embedding, top_k, alpha)` — hybrid search
- `.size()` — store size
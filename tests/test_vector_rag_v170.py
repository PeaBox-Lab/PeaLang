"""Regression coverage for v1.7.0 ONNX/vector/RAG."""

from pealang.vector_rag import (
    build_vector_rag_namespace,
    Vector,
    create_vector,
    cosine_similarity,
    euclidean_distance,
    dot_product,
    chunk_text,
    chunk_by_sentences,
    bm25_score,
    hybrid_search,
    VectorStore,
    model_to_onnx,
    tree_to_onnx,
    onnx_export_json,
)


def test_cosine_similarity():
    a = [1, 0, 0]
    b = [1, 0, 0]
    assert cosine_similarity(a, b) == 1.0
    assert cosine_similarity([1, 0], [0, 1]) == 0.0


def test_euclidean_distance():
    assert euclidean_distance([0, 0], [3, 4]) == 5.0


def test_dot_product():
    assert dot_product([1, 2, 3], [4, 5, 6]) == 32


def test_chunk_text():
    text = "Hello world. This is a test. Another sentence here."
    chunks = chunk_text(text, chunk_size=30, overlap=5)
    assert len(chunks) >= 1
    assert all("text" in c for c in chunks)


def test_chunk_by_sentences():
    text = "First sentence. Second sentence. Third sentence."
    chunks = chunk_by_sentences(text, max_sentences=2)
    assert len(chunks) >= 1


def test_bm25_score():
    score = bm25_score("hello world", "hello world foo bar")
    assert score > 0


def test_hybrid_search():
    docs = ["hello world", "foo bar", "hello foo"]
    results = hybrid_search("hello", docs, top_k=2)
    assert len(results) == 2
    assert results[0]["score"] >= results[1]["score"]


def test_vector_store():
    vs = VectorStore()
    vs.add("hello world", [1.0, 0.0, 0.0])
    vs.add("foo bar", [0.0, 1.0, 0.0])
    results = vs.search([1.0, 0.0, 0.0], top_k=1)
    assert len(results) == 1
    assert results[0]["text"] == "hello world"
    assert vs.size() == 2


def test_vector_store_hybrid():
    vs = VectorStore()
    vs.add("hello world", [1.0, 0.0])
    vs.add("foo bar", [0.0, 1.0])
    results = vs.hybrid_search("hello", [1.0, 0.0], top_k=1)
    assert len(results) == 1


def test_create_vector():
    v = create_vector([1.0, 2.0, 3.0], {"label": "test"})
    assert v["dim"] == 3
    assert v["metadata"]["label"] == "test"


def test_model_to_onnx():
    model = {"kind": "tree", "features": ["a", "b"], "params": {"depth": 3}}
    onnx = model_to_onnx(model)
    assert onnx["format"] == "onnx"
    assert onnx["version"] == "1.7.0"


def test_tree_to_onnx():
    tree = {"feature": 0, "threshold": 5.0, "left": {"value": 1}, "right": {"value": 2}}
    onnx = tree_to_onnx(tree, ["a", "b"])
    assert onnx["format"] == "onnx"
    assert "nodes" in onnx["graph"]


def test_onnx_export_json(tmp_path):
    model = {"kind": "tree", "features": ["a"]}
    path = str(tmp_path / "model.onnx.json")
    result = onnx_export_json(model, path)
    assert result == path
    import json
    with open(path) as f:
        data = json.load(f)
    assert data["format"] == "onnx"


def test_build_vector_rag_namespace():
    ns = build_vector_rag_namespace()
    assert "Vector" in ns
    assert "create_vector" in ns
    assert "cosine_similarity" in ns
    assert "chunk_text" in ns
    assert "VectorStore" in ns
    assert "model_to_onnx" in ns
    assert len(ns) == 13

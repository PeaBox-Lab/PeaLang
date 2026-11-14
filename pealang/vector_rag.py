"""ONNX model export and vector/RAG primitives for PeaLang (v1.7.0).

Provides dependency-free ONNX graph generation for tree/boosting/GLM models,
vector embedding types, semantic chunking, and hybrid search for RAG workflows.
"""

from __future__ import annotations

import re

import hashlib
import json
import math
from typing import Any, Sequence


# ---------------------------------------------------------------------------
# ONNX model export
# ---------------------------------------------------------------------------

def tree_to_onnx(tree_model: dict[str, Any], feature_names: list[str] | None = None) -> dict[str, Any]:
    """Convert a decision tree model to an ONNX-like graph representation."""
    feature_names = feature_names or [f"f{i}" for i in range(len(tree_model.get("features", [])))]
    nodes = []

    def _convert(node, node_id=0):
        if node is None:
            return node_id
        if "leaf" in node or "value" in node and "feature" not in node:
            # Leaf node
            val = node.get("value", node.get("prediction", 0))
            nodes.append({"id": node_id, "type": "leaf", "value": val})
            return node_id
        feat = node.get("feature", 0)
        thresh = node.get("threshold", 0)
        left_id = node_id + 1
        right_id = _convert(node.get("left"), left_id + 1) if node.get("left") else None
        # Actually, let's do it iteratively
        nodes.append({"id": node_id, "type": "split", "feature": feat, "threshold": thresh,
                      "feature_name": feature_names[feat] if feat < len(feature_names) else f"f{feat}"})
        if node.get("left"):
            _convert(node["left"], node_id + 1)
        if node.get("right"):
            _convert(node["right"], node_id + 2)
        return node_id

    _convert(tree_model)
    return {
        "format": "onnx",
        "version": "1.7.0",
        "model_type": "tree",
        "graph": {"nodes": nodes, "inputs": feature_names, "outputs": ["prediction"]},
        "metadata": {"feature_count": len(feature_names), "node_count": len(nodes)},
    }


def model_to_onnx(model: dict[str, Any], model_type: str = "auto") -> dict[str, Any]:
    """Convert a PeaLang model to an ONNX-like representation."""
    if model_type == "auto":
        model_type = model.get("kind", model.get("estimator", "unknown"))
    if "tree" in str(model_type).lower() or "forest" in str(model_type).lower():
        return tree_to_onnx(model, model.get("features", []))
    # Generic model export
    return {
        "format": "onnx",
        "version": "1.7.0",
        "model_type": model_type,
        "graph": {"nodes": [], "inputs": model.get("features", []), "outputs": ["prediction"]},
        "parameters": model.get("params", {}),
        "metadata": {"feature_count": len(model.get("features", []))},
    }


def onnx_export_json(model: dict[str, Any], path: str) -> str:
    """Export a model as ONNX JSON to a file."""
    onnx = model_to_onnx(model)
    with open(path, "w") as f:
        json.dump(onnx, f, indent=2, default=str)
    return path


# ---------------------------------------------------------------------------
# Vector embedding types
# ---------------------------------------------------------------------------

class Vector:
    """A vector embedding with metadata."""

    def __init__(self, values: list[float], metadata: dict[str, Any] | None = None):
        self.values = list(values)
        self.metadata = metadata or {}
        self.dim = len(values)

    def to_dict(self) -> dict[str, Any]:
        return {"values": self.values, "dim": self.dim, "metadata": self.metadata}

    def __repr__(self):
        return f"Vector(dim={self.dim})"


def create_vector(values: list[float], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    v = Vector(values, metadata)
    return v.to_dict()


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = list(a)
    b = list(b)
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def euclidean_distance(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def dot_product(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# ---------------------------------------------------------------------------
# Semantic chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[dict[str, Any]]:
    """Split text into overlapping chunks for RAG."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Try to break at sentence boundary
        if end < len(text):
            # Look for period, newline, or space near end
            for boundary in (". ", "\n", " "):
                idx = text.rfind(boundary, start + chunk_size // 2, end)
                if idx != -1:
                    end = idx + len(boundary)
                    break
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({"text": chunk_text, "start": start, "end": end, "index": len(chunks)})
        start = end - overlap if end - overlap > start else end
        if start >= len(text):
            break
    return chunks


def chunk_by_sentences(text: str, max_sentences: int = 5) -> list[dict[str, Any]]:
    """Split text into chunks of N sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    for i in range(0, len(sentences), max_sentences):
        chunk = " ".join(sentences[i:i + max_sentences])
        if chunk.strip():
            chunks.append({"text": chunk.strip(), "index": len(chunks), "sentence_count": min(max_sentences, len(sentences) - i)})
    return chunks


import re


# ---------------------------------------------------------------------------
# Hybrid search (cosine + BM25)
# ---------------------------------------------------------------------------

def bm25_score(query: str, document: str, k1: float = 1.5, b: float = 0.75,
               avg_doc_len: float = 100.0) -> float:
    """Compute BM25 score for a query against a document."""
    query_terms = query.lower().split()
    doc_terms = document.lower().split()
    doc_len = len(doc_terms)
    term_freq = {}
    for t in doc_terms:
        term_freq[t] = term_freq.get(t, 0) + 1
    # Document frequency (simplified - assume 1 for single doc)
    score = 0.0
    for term in query_terms:
        tf = term_freq.get(term, 0)
        if tf == 0:
            continue
        idf = math.log(2.0)  # simplified
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
        score += idf * numerator / denominator
    return score


def hybrid_search(query: str, documents: list[str], embeddings: list[list[float]] | None = None,
                  query_embedding: list[float] | None = None,
                  alpha: float = 0.5, top_k: int = 5) -> list[dict[str, Any]]:
    """Hybrid search combining BM25 and cosine similarity."""
    results = []
    for i, doc in enumerate(documents):
        bm25 = bm25_score(query, doc)
        cos = 0.0
        if embeddings and query_embedding and i < len(embeddings):
            cos = cosine_similarity(query_embedding, embeddings[i])
        # Normalize BM25 (simple min-max not possible single doc, use raw)
        combined = alpha * cos + (1 - alpha) * (bm25 / (bm25 + 1))  # normalize bm25 to 0-1
        results.append({"index": i, "document": doc, "bm25": round(bm25, 4),
                        "cosine": round(cos, 4), "score": round(combined, 4)})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


# ---------------------------------------------------------------------------
# Vector store
# ---------------------------------------------------------------------------

class VectorStore:
    """Simple in-memory vector store for RAG."""

    def __init__(self):
        self.vectors: list[Vector] = []
        self.documents: list[str] = []

    def add(self, text: str, embedding: list[float], metadata: dict[str, Any] | None = None) -> int:
        v = Vector(embedding, metadata or {})
        v.metadata["text"] = text
        self.vectors.append(v)
        self.documents.append(text)
        return len(self.vectors) - 1

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        scores = []
        for i, v in enumerate(self.vectors):
            cos = cosine_similarity(query_embedding, v.values)
            scores.append({"index": i, "text": self.documents[i], "score": round(cos, 4),
                          "metadata": v.metadata})
        scores.sort(key=lambda r: r["score"], reverse=True)
        return scores[:top_k]

    def hybrid_search(self, query: str, query_embedding: list[float], top_k: int = 5, alpha: float = 0.5) -> list[dict[str, Any]]:
        return hybrid_search(query, self.documents, [v.values for v in self.vectors], query_embedding, alpha, top_k)

    def size(self) -> int:
        return len(self.vectors)


def build_vector_rag_namespace() -> dict[str, Any]:
    return {
        "Vector": Vector,
        "create_vector": create_vector,
        "cosine_similarity": cosine_similarity,
        "euclidean_distance": euclidean_distance,
        "dot_product": dot_product,
        "chunk_text": chunk_text,
        "chunk_by_sentences": chunk_by_sentences,
        "bm25_score": bm25_score,
        "hybrid_search": hybrid_search,
        "VectorStore": VectorStore,
        "model_to_onnx": model_to_onnx,
        "tree_to_onnx": tree_to_onnx,
        "onnx_export_json": onnx_export_json,
    }

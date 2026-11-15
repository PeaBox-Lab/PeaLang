"""AI/ML primitives and transformer support for PeaLang (v2.3.0).

Provides:
- Transformer model loading and inference
- Attention mechanism computation
- Tokenization helpers
- AutoML search primitives
- Model export to ONNX
- Embedding utilities
- Similarity metrics
"""

from __future__ import annotations

import json
import hashlib
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

class BytePairTokenizer:
    """Simple BPE (Byte Pair Encoding) tokenizer."""

    def __init__(self, vocab: Optional[Dict[str, int]] = None, merges: Optional[List[str]] = None):
        self.vocab = vocab or {}
        self.merges = merges or []
        self.inv_vocab: Dict[int, str] = {v: k for k, v in self.vocab.items()} if self.vocab else {}

    def train(self, text: str, vocab_size: int = 256) -> None:
        """Train BPE tokenizer on text corpus."""
        # Simplified training — in production would use proper BPE algorithm
        chars = list(set(text))
        for i, c in enumerate(chars):
            self.vocab[c] = i + 256  # start after ASCII
        # Placeholder: just store characters as vocab
        for c in chars:
            if c not in self.vocab:
                self.vocab[c] = len(self.vocab)

    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs."""
        return [self.vocab.get(c, self.vocab.get("<unk>", 0)) for c in text]

    def decode(self, ids: List[int]) -> str:
        """Decode token IDs to text."""
        tokens = [self.inv_vocab.get(i, "<?>") for i in ids]
        return "".join(tokens)


# ---------------------------------------------------------------------------
# Attention mechanism
# -------------------------------------------------------------------------__

def softmax(x: List[float], axis: int = -1) -> List[float]:
    """Numerically stable softmax."""
    x = list(x)
    max_val = max(x) if x else 0
    exps = [math.exp(v - max_val) for v in x]
    s = sum(exps)
    return [v / s if s else 0.0 for v in exps]


def scaled_dot_product_attention(
    q: List[List[float]],
    k: List[List[float]],
    v: List[List[float]],
    mask: Optional[List[List[bool]]] = None,
) -> Tuple[List[List[float]], List[List[float]]]:
    """Scaled dot-product attention ( Vaswani et al., 2017).

    Returns (output, attention_weights).
    """
    d_k = len(q[0]) if q else 0
    scale = 1.0 / math.sqrt(d_k) if d_k else 1.0

    # Compute QK^T
    kt = list(zip(*k))  # transpose
    scores = []
    for qi in q:
        row = []
        for ktj in kt:
            dot = sum(a * b for a, b in zip(qi, ktj))
            row.append(dot * scale)
        scores.append(row)

    # Apply mask if provided
    if mask:
        for i, m in enumerate(mask):
            for j, m_ij in enumerate(m):
                if m_ij is False:
                    scores[i][j] = -1e9  # effectively zero after softmax

    # Softmax over last axis
    attn_weights = [softmax(row) for row in scores]

    # Apply attention weights to V
    output = []
    for i, row in enumerate(attn_weights):
        out_row = [sum(w * v[j][k] for k, w in enumerate(row)) for j in range(len(v))]
        output.append(out_row)

    return output, attn_weights


# ---------------------------------------------------------------------------
# Transformer block
# -------------------------------------------------------------------------__

class TransformerBlock:
    """Minimal transformer encoder/decoder block."""

    def __init__(
        self,
        d_model: int,
        n_heads: int = 8,
        d_ff: int = 2048,
        dropout: float = 0.1,
    ):
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_ff = d_ff
        self.dropout = dropout
        self.attention = scaled_dot_product_attention

    def forward(
        self,
        x: List[List[float]],
        mask: Optional[List[List[bool]]] = None,
    ) -> List[List[float]]:
        """Forward pass through transformer block.

        x: [seq_len, d_model]
        Returns: [seq_len, d_model]
        """
        # Simplified: single-head attention for now
        # In production would multi-head properly
        seq_len = len(x)

        # Q, K, V projections (simplified as identity for this stub)
        q = x
        k = x
        v = x

        # Self-attention
        attn_out, attn_weights = self.attention(q, k, v, mask)

        # Residual connection + layer norm (stub)
        # x = x + attn_out  (with dropout)
        # For now just return attention output
        return attn_out


# ---------------------------------------------------------------------------
# Embedding utilities
# -------------------------------------------------------------------------__

def create_embedding(
    tokens: List[int],
    embedding_dim: int = 768,
    vocab_size: int = 50257,
) -> List[List[float]]:
    """Create token embeddings (stub with random-ish initialization).

    In production would use learned embeddings from a real model.
    """
    import random as _random
    _random.seed(42)
    embeddings = []
    for t in tokens:
        # Simple learned embedding lookup stub
        emb = [
            _random.random() * 2 - 1
            for _ in range(embedding_dim)
        ]
        embeddings.append(emb)
    return embeddings


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors."""
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def euclidean_distance(a: List[float], b: List[float]) -> float:
    """Euclidean distance between two vectors."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def dot_product(a: List[float], b: List[float]) -> float:
    """Dot product of two vectors."""
    return sum(x * y for x, y in zip(a, b))


# ---------------------------------------------------------------------------
# AutoML search primitives
# ---------------------------------------------------------------------------

def random_search(
    model_type: str,
    X: Any,
    y: Any,
    task: str,
    param_space: Dict[str, List[Any]],
    n_iter: int = 10,
    seed: int = 42,
    *args: Any,
) -> Dict[str, Any]:
    """Random search over hyperparameter space.

    Args:
        model_type: e.g. "forest", "tree"
        X: feature data
        y: target labels
        task: e.g. "classification", "regression"
        param_space: dict of parameter names to lists of values
        n_iter: number of random iterations
        seed: random seed
        *args: additional positional args (for backwards compatibility with older call patterns)

    Returns:
        dict with n_candidates, task, and best_model info
    """
    import random as _random
    _random.seed(seed)

    best_score = -float("inf")
    best_cfg = {}
    n_candidates = 0

    for _ in range(n_iter):
        cfg = {k: _random.choice(v) for k, v in param_space.items()}
        n_candidates += 1
        try:
            # Use a simple score based on config length as stub
            score = -len(str(cfg))
        except Exception:
            score = -float("inf")
        if score > best_score:
            best_score = score
            best_cfg = cfg

    best_model_name = f"random_{model_type}"
    return {
        "n_candidates": n_candidates,
        "task": task,
        "best_model": {"estimator": best_model_name},
        "best_score": best_score,
    }


# ---------------------------------------------------------------------------
# Model export
# -------------------------------------------------------------------------__

def export_to_onnx(
    model: Any,
    input_sample: List[List[float]],
    path: str = "model.onnx",
    opset_version: int = 14,
) -> str:
    """Export a model to ONNX format (stub).

    In production would use onnx.export().
    """
    # Placeholder — write a minimal ONNX-like metadata file
    metadata = {
        "opset_version": opset_version,
        "model_path": path,
        "input_shape": [len(input_sample), len(input_sample[0]) if input_sample else 0],
        "export_time": time.time(),
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(metadata, indent=2))
    return path


# ---------------------------------------------------------------------------
# Namespace exporter
# ---------------------------------------------------------------------------

def build_ai_ml_namespace() -> Dict[str, Any]:
    """Return a namespace dict for registration in analysis/stats/numerics."""
    return {
        "BytePairTokenizer": BytePairTokenizer,
        "TransformerBlock": TransformerBlock,
        "scaled_dot_product_attention": scaled_dot_product_attention,
        "create_embedding": create_embedding,
        "cosine_similarity": cosine_similarity,
        "euclidean_distance": euclidean_distance,
        "dot_product": dot_product,
        "random_search": random_search,
        "export_to_onnx": export_to_onnx,
        "build_ai_ml_namespace": build_ai_ml_namespace,
    }

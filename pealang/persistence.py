"""Portable persistence for fitted models and pipeline transformers.

Fitted estimators and fitted pipelines are ordinary records. This module turns
them into a versioned JSON document so they can be written to disk, stored in a
database or shipped to another process, then loaded back and used for scoring.

Nothing here depends on third-party libraries. The file format is deliberately
plain so a saved model is inspectable with any text editor::

    {
      "format": "pealang.model",
      "version": 1,
      "kind": "model",
      "payload": {"estimator": "random_forest", "task": "classification", ...}
    }
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

FORMAT = "pealang.model"
VERSION = 1

# Training-only payloads that compact documents drop.
_TRAINING_KEYS = ("train_predictions", "oob_predictions")


def _kind(model: Any) -> str:
    if not isinstance(model, dict):
        raise ValueError("model must be a record")
    if "estimator" in model:
        return "model"
    if "steps" in model and "input_names" in model:
        return "pipeline"
    raise ValueError(
        "model must be fitted by a stats estimator, a stats pipeline or "
        "analysis.model_pipeline"
    )


def _check(value: Any, where: str = "model") -> None:
    """Reject values that would not survive a JSON round trip."""
    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("cannot persist a non-finite number at " + where)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _check(item, where + "[" + str(index) + "]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(
                    "record keys must be strings at " + where + ": "
                    + repr(key)
                )
            _check(item, where + "." + key)
        return
    raise ValueError(
        "cannot persist " + type(value).__name__ + " at " + where
    )


def export_model(model: Any, compact: bool = False) -> dict[str, Any]:
    """Wrap a fitted model or transformer in a versioned, JSON-safe document.

    With ``compact = true`` the training predictions and out-of-bag predictions
    are dropped; everything needed for scoring is kept.
    """
    kind = _kind(model)
    if compact:
        payload = {
            key: value for key, value in model.items()
            if key not in _TRAINING_KEYS
        }
    else:
        payload = dict(model)
    _check(payload)
    return {
        "format": FORMAT,
        "version": VERSION,
        "kind": kind,
        "payload": payload,
    }


def import_model(document: Any) -> dict[str, Any]:
    """Validate a document produced by :func:`export_model`."""
    if not isinstance(document, dict):
        raise ValueError("model document must be a record")
    if document.get("format") != FORMAT:
        raise ValueError(
            "unsupported model format: " + repr(document.get("format"))
        )
    version = document.get("version")
    if version != VERSION:
        raise ValueError("unsupported model version: " + repr(version))
    payload = document.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("model document has no payload")
    kind = document.get("kind")
    actual = _kind(payload)
    if kind != actual:
        raise ValueError(
            "model document kind does not match its payload: "
            + repr(kind) + " vs " + actual
        )
    _check(payload)
    return payload


def save_model(path: str, model: Any, indent: int = 2,
               compact: bool = False) -> str:
    """Write a fitted model or transformer to a JSON file.

    Parent directories are created as needed. Returns the written path.
    """
    document = export_model(model, compact)
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    pretty = None if int(indent) == 0 else int(indent)
    target.write_text(
        json.dumps(document, ensure_ascii=False, indent=pretty) + "\n",
        encoding="utf-8",
    )
    return str(target)


def load_model(path: str) -> dict[str, Any]:
    """Read a model or transformer written by :func:`save_model`."""
    target = Path(path).expanduser()
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError("cannot read model file: " + str(error)) from None
    try:
        document = json.loads(text)
    except ValueError as error:
        raise ValueError("model file is not valid JSON: " + str(error)) from None
    return import_model(document)


def _metrics(model: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key in ("train_accuracy", "train_r2", "train_rmse", "train_log_loss",
                "oob_score"):
        value = model.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            out[key] = float(value)
    return out


def model_summary(model: Any) -> dict[str, Any]:
    """Return a small record describing a fitted model or transformer."""
    kind = _kind(model)
    if kind == "pipeline":
        steps = [
            str(step.get("op", "")) for step in (model.get("steps") or [])
            if isinstance(step, dict)
        ]
        return {
            "kind": "pipeline",
            "steps": steps,
            "input_names": list(model.get("input_names") or []),
            "names": list(model.get("names") or []),
            "n_features": len(model.get("names") or []),
            "n": model.get("n"),
        }
    entries = model.get("importance") or []
    top = [
        {"feature": entry.get("feature"), "importance": entry.get("importance")}
        for entry in entries[:5] if isinstance(entry, dict)
    ]
    features = list(model.get("features") or [])
    return {
        "kind": "model",
        "estimator": model.get("estimator"),
        "task": model.get("task"),
        "features": features,
        "output_features": list(model.get("output_features") or []),
        "n_features": len(features) or model.get("n_features"),
        "classes": list(model.get("classes") or []),
        "n": model.get("n_used", model.get("n")),
        "metrics": _metrics(model),
        "top_features": top,
        "has_preprocessor": "preprocessor" in model,
    }


def build_persistence_namespace() -> dict[str, Any]:
    return {
        "export_model": export_model,
        "import_model": import_model,
        "save_model": save_model,
        "load_model": load_model,
        "model_summary": model_summary,
    }

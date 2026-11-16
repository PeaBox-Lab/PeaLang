"""Built-in help for PeaLang: callable inside programs and the REPL.

`help("topic")` returns a short reference for the given topic.
`help()` returns an overview listing all known topics.

Reference content is loaded from the shared ``help_spec.json`` spec file.
"""

from __future__ import annotations

import json
from pathlib import Path

_SPEC_PATH = Path(__file__).with_name("help_spec.json")


def _load_spec() -> dict[str, str]:
    try:
        with _SPEC_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {"overview": "PeaLang help\nusage:\n  help()              list all topics\n  help(\"topic\")       detailed help for a topic"}


_HELP = _load_spec()


def help(topic: str | None = None) -> str:
    """Return reference information for *topic*, or an overview if omitted."""
    if topic is None:
        return _HELP.get("overview", "")
    key = str(topic).lower()
    # exact or prefix match first
    for name, text in _HELP.items():
        if name == key or name.startswith(key):
            return text
    # fall back to substring only for longer queries
    if len(key) >= 3:
        for name, text in _HELP.items():
            if key in name:
                return text
    return f"Unknown topic '{topic}'. Available topics: {', '.join(sorted(_HELP))}"
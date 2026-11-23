"""PeaLang Language Extension Registry (v2.35.0).

Provides a pluggable extension system so that libraries and applications can
extend the PeaLang language with:

* Custom functions callable from PeaLang source
* Custom types with methods
* Custom infix operators
* Stdlib extension namespaces (e.g. ``std.myextension``)

Extensions are declared in ``pea.toml`` under the ``[extensions]`` table and
loaded at interpreter startup time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .errors import PeaError


@dataclass
class ExtensionFunction:
    """A user-defined function exposed to PeaLang."""

    name: str
    func: Callable[..., Any]
    arg_count: Optional[int] = None  # None = variadic
    doc: str = ""


@dataclass
class ExtensionType:
    """A user-defined type with methods."""

    name: str
    constructor: Callable[..., Any]
    methods: Dict[str, Callable[..., Any]] = field(default_factory=dict)
    doc: str = ""


@dataclass
class ExtensionOperator:
    """A user-defined infix operator."""

    symbol: str
    func: Callable[[Any, Any], Any]
    precedence: int = 10  # Default precedence, higher = binds tighter
    doc: str = ""


@dataclass
class ExtensionNamespace:
    """A namespace (e.g. ``std.myextension``) containing functions/types."""

    name: str
    symbols: Dict[str, Any] = field(default_factory=dict)


class ExtensionRegistry:
    """Central registry for all language extensions.

    Extensions can be registered programmatically or loaded from a
    ``pea.toml`` ``[extensions]`` section. The interpreter consults this
    registry when resolving function calls, operator applications, and
    namespace lookups.
    """

    def __init__(self) -> None:
        self.functions: Dict[str, ExtensionFunction] = {}
        self.types: Dict[str, ExtensionType] = {}
        self.operators: Dict[str, ExtensionOperator] = {}
        self.namespaces: Dict[str, ExtensionNamespace] = {}
        self._loaded_modules: List[str] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_function(
        self,
        name: str,
        func: Callable[..., Any],
        arg_count: Optional[int] = None,
        doc: str = "",
    ) -> None:
        """Register a function callable from PeaLang."""
        self.functions[name] = ExtensionFunction(name, func, arg_count, doc)

    def register_type(
        self,
        name: str,
        constructor: Callable[..., Any],
        methods: Optional[Dict[str, Callable[..., Any]]] = None,
        doc: str = "",
    ) -> None:
        """Register a custom type with methods."""
        self.types[name] = ExtensionType(name, constructor, methods or {}, doc)

    def register_operator(
        self,
        symbol: str,
        func: Callable[[Any, Any], Any],
        precedence: int = 10,
        doc: str = "",
    ) -> None:
        """Register a custom infix operator."""
        self.operators[symbol] = ExtensionOperator(symbol, func, precedence, doc)

    def register_namespace(
        self,
        name: str,
        symbols: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a namespace (e.g. ``std.myextension``)."""
        self.namespaces[name] = ExtensionNamespace(name, symbols or {})

    def register_module(self, module_name: str, module: Any) -> None:
        """Register all public symbols from a Python module as extensions."""
        self._loaded_modules.append(module_name)
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue
            attr = getattr(module, attr_name)
            if callable(attr):
                self.register_function(attr_name, attr, doc=getattr(attr, "__doc__", "") or "")
            elif isinstance(attr, (int, float, str, bool)):
                self.register_function(attr_name, lambda _a=attr: _a, doc=f"Constant: {attr_name}")

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_function(self, name: str) -> Optional[ExtensionFunction]:
        return self.functions.get(name)

    def get_type(self, name: str) -> Optional[ExtensionType]:
        return self.types.get(name)

    def get_operator(self, symbol: str) -> Optional[ExtensionOperator]:
        return self.operators.get(symbol)

    def get_namespace(self, name: str) -> Optional[ExtensionNamespace]:
        return self.namespaces.get(name)

    def list_functions(self) -> List[str]:
        return sorted(self.functions.keys())

    def list_types(self) -> List[str]:
        return sorted(self.types.keys())

    def list_operators(self) -> List[str]:
        return sorted(self.operators.keys())

    def list_namespaces(self) -> List[str]:
        return sorted(self.namespaces.keys())

    def list_all(self) -> Dict[str, List[str]]:
        return {
            "functions": self.list_functions(),
            "types": self.list_types(),
            "operators": self.list_operators(),
            "namespaces": self.list_namespaces(),
            "loaded_modules": list(self._loaded_modules),
        }

    # ------------------------------------------------------------------
    # Loading from pea.toml
    # ------------------------------------------------------------------

    def load_from_manifest(self, manifest: Dict[str, Any]) -> None:
        """Load extensions declared in a ``pea.toml`` manifest."""
        ext = manifest.get("library", {}).get("extensions", {})
        if not ext:
            return

        # Register function names (they must be resolvable at import time)
        for fn_name in ext.get("functions", []):
            self.functions.setdefault(
                fn_name,
                ExtensionFunction(fn_name, None, doc=f"External function: {fn_name}"),
            )

        # Register type names
        for type_name in ext.get("types", []):
            self.types.setdefault(
                type_name,
                ExtensionType(type_name, None, doc=f"External type: {type_name}"),
            )

        # Register operator symbols
        for op_symbol in ext.get("operators", []):
            self.operators.setdefault(
                op_symbol,
                ExtensionOperator(op_symbol, None, doc=f"External operator: {op_symbol}"),
            )

        # Register namespace names
        for ns_name in ext.get("namespaces", []):
            self.namespaces.setdefault(
                ns_name,
                ExtensionNamespace(ns_name, doc=f"External namespace: {ns_name}"),
            )

    def resolve_function(self, name: str) -> Optional[Callable[..., Any]]:
        """Resolve a function name to a callable, or None."""
        ext_func = self.get_function(name)
        if ext_func is None or ext_func.func is None:
            return None
        return ext_func.func

    def resolve_operator(self, symbol: str) -> Optional[Callable[[Any, Any], Any]]:
        """Resolve an operator symbol to a callable, or None."""
        ext_op = self.get_operator(symbol)
        if ext_op is None or ext_op.func is None:
            return None
        return ext_op.func

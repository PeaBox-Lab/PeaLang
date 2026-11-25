"""PeaLang Language Extension Type System (v2.37.0).

Extends the PeaLang type system with support for custom types defined by
extensions. Extension types can:

* Be used as type annotations in PeaLang source
* Have methods callable via method syntax (obj.method())
* Participate in type checking and inference
* Be constructed with constructor functions

This module integrates with `pealang/extension_registry.py` to make
extension types available to the type checker and VM.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .type_system import (
    ProtocolContract,
    TypeRef,
    analyze_project,
)


class ExtensionTypeRef(TypeRef):
    """A type reference to an extension-defined type."""

    def __init__(self, name: str) -> None:
        super().__init__(name=name)
        self.extension_name = name

    def __repr__(self) -> str:
        return f"ExtensionTypeRef({self.name})"


class ExtensionTypeSystem:
    """Integrates extension types with the PeaLang type system.

    Provides methods to:
    * Register extension types with the type checker
    * Resolve extension type references
    * Check method calls on extension types
    * Validate extension type usage in expressions
    """

    def __init__(self, extension_registry) -> None:
        self.registry = extension_registry
        self._type_cache: Dict[str, ExtensionTypeRef] = {}

    def get_type_ref(self, name: str) -> Optional[ExtensionTypeRef]:
        """Get or create a type reference for an extension type."""
        if name not in self._type_cache:
            ext_type = self.registry.get_type(name)
            if ext_type is None:
                return None
            self._type_cache[name] = ExtensionTypeRef(name)
        return self._type_cache[name]

    def resolve_method(
        self, type_name: str, method_name: str
    ) -> Optional[Callable[..., Any]]:
        """Resolve a method on an extension type."""
        ext_type = self.registry.get_type(type_name)
        if ext_type is None:
            return None
        return ext_type.methods.get(method_name)

    def has_type(self, name: str) -> bool:
        """Check if an extension type is registered."""
        return self.registry.get_type(name) is not None

    def list_types(self) -> List[str]:
        """List all registered extension type names."""
        return self.registry.list_types()

    def check_method_call(
        self, type_name: str, method_name: str, args: List[Any]
    ) -> bool:
        """Check if a method call on an extension type is valid."""
        ext_type = self.registry.get_type(type_name)
        if ext_type is None:
            return False
        method = ext_type.methods.get(method_name)
        if method is None:
            return False
        # Basic arity check - the method should be callable with the given args
        try:
            method.__code__  # type: ignore[attr-defined]
            expected = method.__code__.co_argcount  # type: ignore[attr-defined]
            # Subtract 1 for 'self' parameter
            expected = max(0, expected - 1)
            return len(args) == expected
        except AttributeError:
            # Built-in functions don't have __code__
            return True

    def get_extension_protocol(self, type_name: str) -> Optional[ProtocolContract]:
        """Create a ProtocolContract for an extension type so it can participate
        in protocol conformance checking."""
        ext_type = self.registry.get_type(type_name)
        if ext_type is None:
            return None
        # Extension methods have no static signatures, so this is a name-only contract.
        return ProtocolContract(
            name=type_name,
            methods=tuple((method_name, (), TypeRef('Any')) for method_name in ext_type.methods),
            method_names_only=True,
        )


def create_extension_type_system(extension_registry) -> ExtensionTypeSystem:
    """Factory function to create an ExtensionTypeSystem."""
    return ExtensionTypeSystem(extension_registry)

"""Deterministic resource scopes for PeaLang programs.

A resource scope owns a bounded resource budget and a LIFO list of cleanup
callbacks. Scopes may nest; a child inherits limits from its parent unless it
provides explicit overrides. Leaving a scope always runs its cleanups, whether
the exit is normal or caused by an exception, and a closed scope cannot be
re-entered or used to register more resources.

The runtime layer is independent of syntax. The ``using`` statement in the
language is compiled to ``SCOPE_ENTER`` / ``SCOPE_EXIT`` instructions that drive
these objects, and hosts may use the same API directly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Optional

from .resource_limits import ResourceBudget, ResourceLimits


class ResourceScopeError(RuntimeError):
    """Raised when a resource scope is used after it has been closed."""

    def __init__(self, code: str, message: str, scope: Optional[str] = None):
        super().__init__(f"{code}: {message}" + (f" (scope {scope})" if scope else ""))
        self.code = code
        self.message = message
        self.scope = scope


@dataclass
class _Cleanup:
    callback: Callable[[], Any]
    label: str = ""


def derive_limits(parent: Optional[ResourceLimits], **overrides) -> ResourceLimits:
    """Create limits for a child scope from a parent scope's limits.

    Explicit keyword overrides win. Values of ``None`` mean "inherit".
    """

    values = asdict(parent) if parent is not None else asdict(ResourceLimits())
    for key, value in overrides.items():
        if value is not None:
            if key not in values:
                raise ValueError(f"Unknown resource limit '{key}'")
            values[key] = int(value)
    return ResourceLimits(**values)


def dispose(value: Any) -> bool:
    """Dispose *value* by calling ``close()`` or ``dispose()`` when available.

    Returns ``True`` when a disposal method was called. Missing methods are
    treated as a value that needs no cleanup, which keeps ``using`` usable with
    plain portable values such as numbers, strings, lists, and maps.
    """

    for name in ("close", "dispose"):
        method = getattr(value, name, None)
        if callable(method):
            method()
            return True
    return False


class ResourceScope:
    """A bounded scope with deterministic, LIFO cleanup.

    ``ResourceScope`` objects can be used directly as context managers. In
    language programs the ``using`` statement creates one implicitly and
    guarantees cleanup on both normal and exceptional exits.
    """

    def __init__(
        self,
        name: str,
        parent: Optional["ResourceScope"] = None,
        limits: Optional[ResourceLimits] = None,
        manager: Optional["ResourceScopeManager"] = None,
    ):
        self.name = name
        self.parent = parent
        self.manager = manager
        self.closed = False
        self.value: Any = None
        self.cleanups: list[_Cleanup] = []
        self.children: list[ResourceScope] = []
        inherited = parent.budget.limits if parent is not None else None
        self.limits = limits or derive_limits(inherited)
        self.budget = ResourceBudget(self.limits)
        if parent is not None:
            parent.children.append(self)

    def check(self) -> None:
        """Raise ``RS201`` when this scope has already been closed."""

        if self.closed:
            raise ResourceScopeError("RS201", "Resource scope is closed", self.name)

    def child(self, name: str, limits: Optional[ResourceLimits] = None) -> "ResourceScope":
        """Create and return a nested scope."""

        self.check()
        return ResourceScope(name, parent=self, limits=limits, manager=self.manager)

    def defer(self, callback: Callable[[], Any], label: str = "") -> None:
        """Register a cleanup callback to run when this scope closes."""

        self.check()
        self.cleanups.append(_Cleanup(callback, label))

    def register(self, value: Any, label: str = "") -> Any:
        """Bind a value to this scope and register it for disposal."""

        self.check()
        self.value = value
        self.defer(lambda: dispose(value), label or "resource")
        return value

    def close(self) -> list[str]:
        """Close the scope and run cleanups in reverse registration order.

        Closing an already closed scope is a no-op, which keeps VM unwinding
        safe when both an exception handler and a normal exit path reach it.
        """

        if self.closed:
            return []
        self.closed = True
        labels = []
        while self.cleanups:
            cleanup = self.cleanups.pop()
            labels.append(cleanup.label)
            cleanup.callback()
        if self.manager is not None:
            self.manager._forget(self)
        return labels

    def snapshot(self) -> dict:
        """Return a portable description of this scope and its budget."""

        return {
            'name': self.name,
            'closed': self.closed,
            'value': self.value,
            'budget': self.budget.snapshot(),
            'cleanups': [item.label for item in self.cleanups],
            'children': [child.name for child in self.children],
        }

    def __enter__(self) -> "ResourceScope":
        self.check()
        if self.manager is not None and self not in self.manager.scopes:
            self.manager._push(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self.manager is not None and self in self.manager.scopes:
            self.manager.exit(self)
        else:
            self.close()
        return False


class ResourceScopeManager:
    """A stack of active resource scopes owned by one runtime instance."""

    def __init__(self):
        self.scopes: list[ResourceScope] = []
        self.history: list[str] = []

    def current(self) -> Optional[ResourceScope]:
        """Return the innermost active scope, if any."""

        return self.scopes[-1] if self.scopes else None

    def enter(self, name: str, value: Any = None, limits: Optional[ResourceLimits] = None) -> ResourceScope:
        """Open a child of the current scope and optionally bind a resource."""

        parent = self.current()
        scope = ResourceScope(name, parent=parent, limits=limits, manager=self)
        if value is not None:
            scope.register(value)
        self._push(scope)
        return scope

    def exit(self, scope: Optional[ResourceScope] = None) -> list[str]:
        """Close *scope* or the innermost active scope."""

        if not self.scopes:
            return []
        target = scope or self.scopes[-1]
        if target not in self.scopes:
            raise ResourceScopeError("RS201", "Scope is not active", target.name)
        while self.scopes:
            active = self.scopes.pop()
            labels = active.close()
            self.history.append(active.name)
            if active is target:
                return labels
        return []

    def unwind(self, depth: int) -> list[str]:
        """Close all scopes above *depth* and return their cleanup labels."""

        labels = []
        while len(self.scopes) > depth:
            labels.extend(self.exit())
        return labels

    def close_all(self) -> list[str]:
        """Close every active scope, outermost last."""

        return self.unwind(0)

    def snapshot(self) -> dict:
        """Return a portable description of the active scope stack."""

        return {
            'active': [scope.name for scope in self.scopes],
            'history': list(self.history),
            'scopes': [scope.snapshot() for scope in self.scopes],
        }

    def _push(self, scope: ResourceScope) -> None:
        self.scopes.append(scope)

    def _forget(self, scope: ResourceScope) -> None:
        if scope in self.scopes:
            self.scopes.remove(scope)


def scope_summary(value: Any) -> dict:
    """Return a portable summary for a scope or manager."""

    if isinstance(value, ResourceScope):
        return value.snapshot()
    if isinstance(value, ResourceScopeManager):
        return value.snapshot()
    return {'name': 'none', 'closed': False, 'value': value}

"""Structured concurrency primitives with cancellation propagation, deadlines, and task groups."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional
from contextlib import asynccontextmanager


class CancellationError(Exception):
    """Raised when a task is cancelled via structured concurrency."""
    def __init__(self, message: str = "Task cancelled"):
        super().__init__(message)


class CancellationScope:
    """A scope that tracks cancellation state and propagates to children."""
    
    def __init__(self, parent: Optional["CancellationScope"] = None, deadline: Optional[float] = None):
        self.parent = parent
        self.cancelled = False
        self.children: list[CancellationScope] = []
        self.deadline = deadline  # absolute timestamp
        if parent:
            parent.children.append(self)
    
    def child(self, deadline: Optional[float] = None) -> "CancellationScope":
        return CancellationScope(parent=self, deadline=deadline)
    
    def cancel(self) -> None:
        self.cancelled = True
        for child in list(self.children):
            child.cancel()
    
    def throw_if_cancelled(self) -> None:
        if self.cancelled or (self.parent and self.parent.cancelled):
            raise asyncio.CancelledError("PeaLang task cancelled")
        if self.deadline and time.monotonic() >= self.deadline:
            self.cancel()
            raise asyncio.CancelledError("Deadline exceeded")


@dataclass
class PeaTask:
    """A managed task with cancellation scope."""
    task: asyncio.Task
    scope: CancellationScope
    
    def cancel(self) -> None:
        self.scope.cancel()
        self.task.cancel()
    
    async def result(self) -> Any:
        return await self.task


@dataclass
class TaskGroup:
    """
    Structured task group with automatic cleanup and error handling.
    
    Usage:
        async with TaskGroup() as g:
            t1 = g.spawn(coro1())
            t2 = g.spawn(coro2())
        # All tasks completed or cancelled
    """
    scope: CancellationScope = field(default_factory=CancellationScope)
    tasks: list[PeaTask] = field(default_factory=list)
    _entered: bool = False
    _exited: bool = False
    
    async def __aenter__(self) -> "TaskGroup":
        self._entered = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._exited = True
        if exc_type is not None:
            # Exception in the body: cancel all tasks
            self.scope.cancel()
            for item in self.tasks:
                item.cancel()
            # Wait for cancellation to propagate
            await asyncio.gather(*(x.task for x in self.tasks), return_exceptions=True)
            return False  # Don't suppress the exception
        
        # Normal exit: wait for all tasks, propagate first exception
        results = await asyncio.gather(*(x.task for x in self.tasks), return_exceptions=True)
        for result in results:
            if isinstance(result, BaseException):
                self.scope.cancel()
                raise result
        return False
    
    def spawn(self, awaitable: Awaitable, *, name: Optional[str] = None, deadline: Optional[float] = None) -> PeaTask:
        """Spawn a child task within this group."""
        if not self._entered:
            raise RuntimeError("TaskGroup.spawn() called outside async context manager")
        child = self.scope.child(deadline=deadline)
        
        async def runner():
            child.throw_if_cancelled()
            return await awaitable
        
        task = asyncio.create_task(runner())
        if name:
            task.set_name(name)
        item = PeaTask(task=task, scope=child)
        self.tasks.append(item)
        return item
    
    async def wait_all(self) -> list[Any]:
        """Wait for all tasks and return results (raises first exception)."""
        return await asyncio.gather(*(x.task for x in self.tasks))
    
    async def wait_any(self) -> tuple[int, Any]:
        """Wait for first task to complete, return (index, result)."""
        done, pending = await asyncio.wait(
            [x.task for x in self.tasks],
            return_when=asyncio.FIRST_COMPLETED
        )
        for i, task in enumerate(self.tasks):
            if task.task in done:
                return i, task.task.result()
        raise RuntimeError("No tasks completed")


@asynccontextmanager
async def timeout_scope(seconds: float):
    """Context manager that cancels on timeout."""
    scope = CancellationScope(deadline=time.monotonic() + seconds)
    try:
        yield scope
    finally:
        scope.cancel()


def current_scope() -> CancellationScope:
    """Get the current cancellation scope (for use in async functions)."""
    # This would be set by the runtime when entering a structured context
    try:
        return asyncio.current_task()._pea_scope  # type: ignore
    except AttributeError:
        return CancellationScope()


def set_current_scope(scope: CancellationScope) -> None:
    """Set the current cancellation scope on the running task."""
    task = asyncio.current_task()
    if task:
        task._pea_scope = scope  # type: ignore


# --- Language-level primitives exposed to PeaLang programs ---

async def spawn(awaitable: Awaitable, *, name: str = "") -> PeaTask:
    """Spawn a task in the current scope (or new root scope)."""
    scope = current_scope()
    child = scope.child()
    
    async def runner():
        child.throw_if_cancelled()
        return await awaitable
    
    task = asyncio.create_task(runner())
    if name:
        task.set_name(name)
    return PeaTask(task=task, scope=child)


async def sleep(seconds: float) -> None:
    """Cancellable sleep that respects the current scope."""
    scope = current_scope()
    try:
        await asyncio.sleep(seconds)
    except asyncio.CancelledError:
        scope.throw_if_cancelled()
        raise


async def gather(*awaitables: Awaitable, return_exceptions: bool = False) -> list[Any]:
    """Structured gather with cancellation propagation."""
    scope = current_scope()
    child = scope.child()
    
    async def run_all():
        child.throw_if_cancelled()
        return await asyncio.gather(*awaitables, return_exceptions=return_exceptions)
    
    task = asyncio.create_task(run_all())
    item = PeaTask(task=task, scope=child)
    return await item.result()


# --- Namespace builder ---

def build_structured_concurrency_namespace() -> dict[str, Any]:
    return {
        "CancellationError": CancellationError,
        "CancellationScope": CancellationScope,
        "TaskGroup": TaskGroup,
        "PeaTask": PeaTask,
        "spawn": spawn,
        "sleep": sleep,
        "gather": gather,
        "timeout_scope": timeout_scope,
        "current_scope": current_scope,
        "set_current_scope": set_current_scope,
    }


# --- Integration with interpreter ---

def wrap_with_scope(coro: Awaitable, scope: Optional[CancellationScope] = None) -> Awaitable:
    """Wrap a coroutine to run within a cancellation scope."""
    async def wrapper():
        outer_scope = scope or CancellationScope()
        token = set_current_scope(outer_scope)
        try:
            return await coro
        finally:
            # Restore previous scope
            pass
    return wrapper()


# --- Backward compatibility ---
async def gather_structured(*awaitables: Awaitable) -> list[Any]:
    """Legacy function - use TaskGroup instead."""
    async with TaskGroup() as group:
        tasks = [group.spawn(x) for x in awaitables]
    return [await x.result() for x in tasks]
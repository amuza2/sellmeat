import asyncio
import functools
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


class ViewModelBase:
    """Base class for all ViewModels. Provides property change notification."""

    def __init__(self):
        self._listeners: list[Callable] = []

    def add_listener(self, callback: Callable):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify(self, property_name: str = ""):
        for listener in self._listeners:
            listener(property_name)


class ObservableProperty(Generic[T]):
    """Descriptor that auto-notifies on set, like [ObservableProperty] in CommunityToolkit.Mvvm."""

    def __init__(self, default: T | None = None):
        self.default = default
        self.attr_name: str = ""

    def __set_name__(self, owner, name: str):
        self.attr_name = f"_{name}"

    def __get__(self, obj, objtype=None) -> T | None:
        if obj is None:
            return self.default
        return getattr(obj, self.attr_name, self.default)

    def __set__(self, obj, value: T):
        old = getattr(obj, self.attr_name, self.default)
        if old != value:
            setattr(obj, self.attr_name, value)
            if isinstance(obj, ViewModelBase):
                obj.notify(self.attr_name)


class Command:
    """Sync command wrapper, like ICommand / [RelayCommand] in CommunityToolkit."""

    def __init__(self, execute: Callable, can_execute: Callable[[], bool] | None = None):
        self._execute = execute
        self._can_execute = can_execute or (lambda: True)

    def __call__(self, *args, **kwargs):
        if self._can_execute():
            return self._execute(*args, **kwargs)

    def can_execute(self) -> bool:
        return self._can_execute()


class AsyncCommand:
    """Async command wrapper for API calls, with is_running observable state."""

    def __init__(self, execute: Callable, can_execute: Callable[[], bool] | None = None):
        self._execute = execute
        self._can_execute = can_execute or (lambda: True)
        self.is_running = False
        self._listeners: list[Callable] = []

    def add_listener(self, callback: Callable):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def _set_running(self, value: bool):
        self.is_running = value
        for listener in self._listeners:
            listener("is_running")

    def can_execute(self) -> bool:
        return self._can_execute() and not self.is_running

    async def __call__(self, *args, **kwargs):
        if not self.can_execute():
            return
        self._set_running(True)
        try:
            result = self._execute(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            return result
        finally:
            self._set_running(False)

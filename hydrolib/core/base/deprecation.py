"""Reusable building blocks for deprecating public Python API surface.

This module is intended for cases where a public symbol on a class is renamed,
moved, or scheduled for removal but must keep working — with a clear
``DeprecationWarning`` — until the announced removal version.

Currently exposes:

- :class:`DeprecatedAttributeAlias` — a property subclass that proxies
  attribute reads and writes to a renamed attribute on the same instance.

Add new helpers here rather than re-implementing deprecation plumbing in each
module, and document the user-facing implications in ``docs/migration.md``.
"""

import warnings
from typing import Any, Optional


class DeprecatedAttributeAlias(property):
    """Property subclass that proxies access to a renamed instance attribute.

    Reading or writing the attribute under the deprecated name forwards to
    ``new_name`` on the same instance and emits a ``DeprecationWarning``. The
    deprecated name is discovered automatically from the class body via
    ``__set_name__`` so callers do not need to repeat it.

    Inheriting from :class:`property` is deliberate: Pydantic v2 only routes
    ``__setattr__`` through descriptors that are instances of :class:`property`,
    so a plain ``__get__``/``__set__`` descriptor would silently swallow writes
    on Pydantic models.

    Example::

        class Meteo(BaseModel):
            extrapolationallowed: Optional[bool] = ...

            extrapolationAllowed = DeprecatedAttributeAlias(
                "extrapolationallowed", removed_in="2.0.0", since="1.1.0"
            )

    Args:
        new_name: Canonical attribute name reads and writes are forwarded to.
        removed_in: Version in which the deprecated name will be removed.
            Surfaced in the warning message; pass a concrete version string
            so users can act on it.
        since: Version in which the deprecation was introduced. Optional;
            included in the warning when supplied.
        message: Optional fully-formed message that overrides the
            auto-generated one. Use this when the default phrasing does not
            fit (for example, when there is no direct replacement).
    """

    def __init__(
        self,
        new_name: str,
        *,
        removed_in: str = "a future release",
        since: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """See class docstring for parameter semantics."""
        self._new_name = new_name
        self._removed_in = removed_in
        self._since = since
        self._custom_message = message
        self._owner_name: Optional[str] = None
        self._old_name: Optional[str] = None
        super().__init__(self._read, self._write)

    def __set_name__(self, owner: type, name: str) -> None:
        """Capture the owning class and deprecated attribute name at class-creation time."""
        self._owner_name = owner.__name__
        self._old_name = name

    @property
    def new_name(self) -> str:
        """Name this alias forwards to."""
        return self._new_name

    @property
    def old_name(self) -> Optional[str]:
        """Deprecated name, discovered from the class body."""
        return self._old_name

    def _build_message(self) -> str:
        if self._custom_message is not None:
            result = self._custom_message
        else:
            qualified_old = self._qualified(self._old_name)
            qualified_new = self._qualified(self._new_name)
            since_part = f" since {self._since}" if self._since else ""
            result = (
                f"`{qualified_old}` is deprecated{since_part} and will be "
                f"removed in {self._removed_in}; use `{qualified_new}` instead."
            )
        return result

    def _qualified(self, name: Optional[str]) -> str:
        if self._owner_name and name:
            result = f"{self._owner_name}.{name}"
        else:
            result = name or "<unknown>"
        return result

    def _read(self, obj: Any) -> Any:
        warnings.warn(self._build_message(), DeprecationWarning, stacklevel=3)
        return getattr(obj, self._new_name)

    def _write(self, obj: Any, value: Any) -> None:
        warnings.warn(self._build_message(), DeprecationWarning, stacklevel=3)
        setattr(obj, self._new_name, value)

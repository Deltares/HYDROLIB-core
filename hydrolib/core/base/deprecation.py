"""Reusable building blocks for deprecating public Python API surface.

This module is intended for cases where a public symbol on a class is renamed,
moved, or scheduled for removal but must keep working — with a clear
`DeprecationWarning` — until the announced removal version.

Currently exposes:

- :class:`DeprecatedAttributeAlias` — a property subclass that proxies
  attribute reads and writes to a renamed attribute on the same instance.

Add new helpers here rather than re-implementing deprecation plumbing in each
module, and document the user-facing implications in `docs/migration.md`.
"""

import warnings
from typing import Any


class DeprecatedAttributeAlias(property):
    """Property subclass that proxies access to a renamed instance attribute.

    Reading or writing the attribute under the deprecated name forwards to
    `new_name` on the same instance and emits a `DeprecationWarning`. The
    deprecated name is discovered automatically from the class body via
    `__set_name__` so callers do not need to repeat it.

    Inheriting from :class:`property` is deliberate: Pydantic v2 only routes
    `__setattr__` through descriptors that are instances of :class:`property`,
    so a plain `__get__`/`__set__` descriptor would silently swallow writes
    on Pydantic models.

    Args:
        new_name: Canonical attribute name reads and writes are forwarded to.
        removed_in: Version in which the deprecated name will be removed.
            Defaults to `"a future release"`. Pass a concrete version string
            so users can act on it.
        since: Version in which the deprecation was introduced. Defaults to
            `None`. When supplied it appears in the warning message.
        message: Fully-formed message that overrides the auto-generated one.
            Defaults to `None`. Use this when the default phrasing does not
            fit (for example, when there is no direct replacement).

    Examples:
        - Define a class with a deprecated alias and read through it:
            ```python
            >>> import warnings
            >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
            >>> class Config:
            ...     timeout_seconds = 30
            ...     timeoutSeconds = DeprecatedAttributeAlias("timeout_seconds", removed_in="2.0.0")
            ...
            >>> cfg = Config()
            >>> with warnings.catch_warnings():
            ...     warnings.simplefilter("ignore")
            ...     value = cfg.timeoutSeconds
            >>> value
            30

            ```
        - Writing via the deprecated name updates the canonical attribute:
            ```python
            >>> import warnings
            >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
            >>> class Settings:
            ...     batch_size = 10
            ...     batchSize = DeprecatedAttributeAlias("batch_size", removed_in="2.0.0")
            ...
            >>> s = Settings()
            >>> with warnings.catch_warnings():
            ...     warnings.simplefilter("ignore")
            ...     s.batchSize = 50
            >>> s.batch_size
            50

            ```
        - Inspect alias metadata directly from the class:
            ```python
            >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
            >>> class Service:
            ...     host = "localhost"
            ...     hostName = DeprecatedAttributeAlias("host", removed_in="3.0.0", since="1.5.0")
            ...
            >>> alias = Service.__dict__["hostName"]
            >>> alias.new_name
            'host'
            >>> alias.old_name
            'hostName'

            ```

    See Also:
        :mod:`warnings`: Standard library used to emit the deprecation signal.
    """

    def __init__(
        self,
        new_name: str,
        *,
        removed_in: str = "a future release",
        since: str | None = None,
        message: str | None = None,
    ) -> None:
        """Store the alias configuration and chain into `property.__init__`.

        Args:
            new_name: Canonical attribute name reads and writes forward to.
            removed_in: Version in which the deprecated name will be removed.
                Defaults to `"a future release"`.
            since: Version in which the deprecation was introduced. Defaults
                to `None`.
            message: Fully-formed override for the default warning text.
                Defaults to `None`.

        Examples:
            - Construct with only the required `new_name`:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> alias = DeprecatedAttributeAlias("new_field")
                >>> alias.new_name
                'new_field'

                ```
            - Construct with a removal version and since-version:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> alias = DeprecatedAttributeAlias("real_name", removed_in="2.0.0", since="1.1.0")
                >>> alias.new_name
                'real_name'

                ```
        """
        self._new_name = new_name
        self._removed_in = removed_in
        self._since = since
        self._custom_message = message
        self._owner_name: str | None = None
        self._old_name: str | None = None
        super().__init__(self._read, self._write)

    def __set_name__(self, owner: type, name: str) -> None:
        """Capture the owning class and deprecated attribute name on class creation.

        Python calls this hook automatically when a descriptor is assigned in
        a class body. The descriptor records both the owner class name and
        the attribute name it was bound to so warning messages can reference
        fully qualified names.

        Args:
            owner: Class object that owns this descriptor.
            name: Attribute name under which the descriptor was bound.

        Examples:
            - The deprecated attribute name is discovered automatically:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> class Widget:
                ...     color = "red"
                ...     colour = DeprecatedAttributeAlias("color")
                ...
                >>> Widget.__dict__["colour"].old_name
                'colour'

                ```
            - The owner class name is also captured for use in warnings:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> class Engine:
                ...     speed = 0
                ...     velocity = DeprecatedAttributeAlias("speed")
                ...
                >>> Engine.__dict__["velocity"]._owner_name
                'Engine'

                ```
        """
        self._owner_name = owner.__name__
        self._old_name = name

    @property
    def new_name(self) -> str:
        """Canonical attribute name reads and writes are forwarded to.

        Returns:
            The canonical attribute name supplied at construction.

        Examples:
            - Inspect the forwarding target on a standalone alias:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> alias = DeprecatedAttributeAlias("snake_name")
                >>> alias.new_name
                'snake_name'

                ```
            - Inspect the target from a class-bound alias:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> class Box:
                ...     width = 100
                ...     widthPx = DeprecatedAttributeAlias("width")
                ...
                >>> Box.__dict__["widthPx"].new_name
                'width'

                ```
        """
        return self._new_name

    @property
    def old_name(self) -> str | None:
        """Deprecated name, discovered from the class body via `__set_name__`.

        Returns:
            The deprecated attribute name, or `None` if the descriptor was
            created but never bound to a class.

        Examples:
            - A class-bound alias reports its class-body attribute name:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> class User:
                ...     full_name = ""
                ...     fullName = DeprecatedAttributeAlias("full_name")
                ...
                >>> User.__dict__["fullName"].old_name
                'fullName'

                ```
            - An unbound descriptor reports `None`:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> orphan = DeprecatedAttributeAlias("real_name")
                >>> orphan.old_name is None
                True

                ```
        """
        return self._old_name

    def _build_message(self) -> str:
        """Build the deprecation warning text emitted on every access.

        Returns:
            The custom message if one was supplied at construction, otherwise
            a rendered default that references the deprecated and canonical
            names, the deprecation version (if any), and the removal version.

        Examples:
            - Default message references qualified names and removal version:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> class Order:
                ...     total_cents = 0
                ...     totalCents = DeprecatedAttributeAlias(
                ...         "total_cents", removed_in="2.0.0", since="1.1.0"
                ...     )
                ...
                >>> Order.__dict__["totalCents"]._build_message()
                '`Order.totalCents` is deprecated since 1.1.0 and will be removed in 2.0.0; use `Order.total_cents` instead.'

                ```
            - A custom `message` overrides the default formatter verbatim:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> class Account:
                ...     id_ = 0
                ...     account_id = DeprecatedAttributeAlias(
                ...         "id_", message="account_id has moved to id_"
                ...     )
                ...
                >>> Account.__dict__["account_id"]._build_message()
                'account_id has moved to id_'

                ```
        """
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

    def _qualified(self, name: str | None) -> str:
        """Format an attribute name with its owner class prefix when available.

        Args:
            name: Attribute name to qualify, or `None`.

        Returns:
            `"<owner>.<name>"` when both the owner class name and `name` are
            known. The bare `name` when only the owner is missing. The
            literal `"<unknown>"` when `name` itself is `None`.

        Examples:
            - A class-bound alias qualifies with the owner class name:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> class Server:
                ...     port = 8080
                ...     portNumber = DeprecatedAttributeAlias("port")
                ...
                >>> Server.__dict__["portNumber"]._qualified("port")
                'Server.port'

                ```
            - An unbound descriptor returns the bare name:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> alias = DeprecatedAttributeAlias("port")
                >>> alias._qualified("port")
                'port'

                ```
            - Passing `None` falls back to the unknown sentinel:
                ```python
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> alias = DeprecatedAttributeAlias("port")
                >>> alias._qualified(None)
                '<unknown>'

                ```
        """
        if self._owner_name and name:
            result = f"{self._owner_name}.{name}"
        else:
            result = name or "<unknown>"
        return result

    def _read(self, obj: Any) -> Any:
        """Emit a deprecation warning and forward the read to `new_name`.

        Bound by :class:`property` as the `fget` callable. Invoked when the
        deprecated attribute is read from a class instance.

        Args:
            obj: Instance whose attribute is being read.

        Returns:
            The current value of `getattr(obj, new_name)`.

        Examples:
            - Reading via the deprecated alias returns the canonical value:
                ```python
                >>> import warnings
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> class Profile:
                ...     full_name = "Ada"
                ...     fullName = DeprecatedAttributeAlias("full_name")
                ...
                >>> p = Profile()
                >>> with warnings.catch_warnings():
                ...     warnings.simplefilter("ignore")
                ...     value = p.fullName
                >>> value
                'Ada'

                ```
            - Each access emits its own `DeprecationWarning`:
                ```python
                >>> import warnings
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> class Item:
                ...     unit_price = 19.99
                ...     unitPrice = DeprecatedAttributeAlias("unit_price")
                ...
                >>> item = Item()
                >>> with warnings.catch_warnings(record=True) as captured:
                ...     warnings.simplefilter("always")
                ...     _ = item.unitPrice
                >>> len(captured)
                1
                >>> captured[0].category.__name__
                'DeprecationWarning'

                ```
        """
        warnings.warn(self._build_message(), DeprecationWarning, stacklevel=3)
        return getattr(obj, self._new_name)

    def _write(self, obj: Any, value: Any) -> None:
        """Emit a deprecation warning and forward the write to `new_name`.

        Bound by :class:`property` as the `fset` callable. Invoked when the
        deprecated attribute is assigned on a class instance.

        Args:
            obj: Instance whose attribute is being written.
            value: New value to store on `obj.<new_name>`.

        Examples:
            - Writing via the deprecated alias updates the canonical attribute:
                ```python
                >>> import warnings
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> class Cache:
                ...     max_size = 0
                ...     maxSize = DeprecatedAttributeAlias("max_size")
                ...
                >>> c = Cache()
                >>> with warnings.catch_warnings():
                ...     warnings.simplefilter("ignore")
                ...     c.maxSize = 1024
                >>> c.max_size
                1024

                ```
            - Each write triggers its own `DeprecationWarning`:
                ```python
                >>> import warnings
                >>> from hydrolib.core.base.deprecation import DeprecatedAttributeAlias
                >>> class Buffer:
                ...     length = 0
                ...     bufferLength = DeprecatedAttributeAlias("length")
                ...
                >>> b = Buffer()
                >>> with warnings.catch_warnings(record=True) as captured:
                ...     warnings.simplefilter("always")
                ...     b.bufferLength = 1
                ...     b.bufferLength = 2
                >>> len(captured)
                2

                ```
        """
        warnings.warn(self._build_message(), DeprecationWarning, stacklevel=3)
        setattr(obj, self._new_name, value)

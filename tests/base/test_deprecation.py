"""Tests for the generic deprecation helpers in `hydrolib.core.base._deprecation`."""

import warnings
from typing import Optional

import pytest

from hydrolib.core.base._deprecation import DeprecatedAttributeAlias


class _SampleHolder:
    """Plain class with a canonical attribute and a deprecated alias."""

    canonical_name: Optional[int] = None

    deprecatedName = DeprecatedAttributeAlias(
        "canonical_name", removed_in="9.9.9", since="1.0.0"
    )

    def __init__(self, canonical_name: Optional[int] = None) -> None:
        self.canonical_name = canonical_name


class TestDeprecatedAttributeAlias:
    """Tests for the `DeprecatedAttributeAlias` property-subclass descriptor."""

    def test_read_forwards_to_new_name_and_warns(self):
        """Reading the deprecated name yields the canonical value and warns."""
        holder = _SampleHolder(canonical_name=42)
        with pytest.warns(DeprecationWarning, match="deprecatedName"):
            result = holder.deprecatedName
        assert result == 42, f"Expected forwarded value 42, got {result}"

    def test_write_forwards_to_new_name_and_warns(self):
        """Writing the deprecated name updates the canonical attribute and warns."""
        holder = _SampleHolder()
        with pytest.warns(DeprecationWarning, match="deprecatedName"):
            holder.deprecatedName = 7
        assert holder.canonical_name == 7, (
            f"Expected canonical_name to be 7 after write, got {holder.canonical_name}"
        )

    def test_warning_mentions_owner_and_removal_version(self):
        """Default warning text includes qualified names, since-version, and removal-version."""
        holder = _SampleHolder()
        with pytest.warns(DeprecationWarning) as captured:
            holder.deprecatedName = 1
        message = str(captured[0].message)
        assert "_SampleHolder.deprecatedName" in message, message
        assert "_SampleHolder.canonical_name" in message, message
        assert "9.9.9" in message, message
        assert "since 1.0.0" in message, message

    def test_class_access_returns_descriptor(self):
        """Accessing the alias on the class (not an instance) returns the descriptor itself."""
        descriptor = _SampleHolder.__dict__["deprecatedName"]
        assert isinstance(descriptor, DeprecatedAttributeAlias)
        assert descriptor.old_name == "deprecatedName"
        assert descriptor.new_name == "canonical_name"

    def test_class_access_via_getattr_returns_descriptor(self):
        """`Class.alias` (rather than via `__dict__`) also returns the descriptor."""
        result = _SampleHolder.deprecatedName
        assert isinstance(result, DeprecatedAttributeAlias)

    def test_custom_message_overrides_default(self):
        """A `message=` override is emitted verbatim in place of the default text."""

        class Custom:
            canonical_name: Optional[int] = None
            old = DeprecatedAttributeAlias(
                "canonical_name", message="use something else"
            )

        holder = Custom()
        holder.canonical_name = 5
        with pytest.warns(DeprecationWarning, match="use something else"):
            _ = holder.old

    def test_default_removed_in_phrasing_when_unspecified(self):
        """If `removed_in` is omitted the message falls back to 'a future release'."""

        class Defaults:
            canonical_name: Optional[int] = None
            old = DeprecatedAttributeAlias("canonical_name")

        holder = Defaults()
        with pytest.warns(DeprecationWarning) as captured:
            holder.old = 1
        assert "a future release" in str(captured[0].message)

    def test_default_message_without_since_omits_segment(self):
        """When `since` is None the message must not contain the 'since' clause."""

        class NoSince:
            canonical_name: Optional[int] = None
            old = DeprecatedAttributeAlias("canonical_name", removed_in="2.0.0")

        holder = NoSince()
        with pytest.warns(DeprecationWarning) as captured:
            holder.old = 1
        message = str(captured[0].message)
        assert "since" not in message, f"Did not expect 'since' segment: {message}"
        assert "2.0.0" in message, message

    def test_no_warning_when_using_new_name_directly(self):
        """Read/write via the canonical name emits no `DeprecationWarning`."""
        holder = _SampleHolder()
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            holder.canonical_name = 3
            value = holder.canonical_name
        deprecations = [
            w for w in captured if issubclass(w.category, DeprecationWarning)
        ]
        assert deprecations == [], (
            f"Did not expect any DeprecationWarning, got {len(deprecations)}"
        )
        assert value == 3

    def test_each_access_emits_its_own_warning(self):
        """The warning is not de-duplicated by the descriptor: each access re-warns."""
        holder = _SampleHolder(canonical_name=1)
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            _ = holder.deprecatedName
            _ = holder.deprecatedName
            holder.deprecatedName = 2
        deprecations = [
            w for w in captured if issubclass(w.category, DeprecationWarning)
        ]
        assert len(deprecations) == 3, (
            f"Expected one warning per access, got {len(deprecations)}"
        )

    def test_descriptor_is_property_subclass(self):
        """Subclassing `property` is a load-bearing invariant for Pydantic compatibility."""
        assert issubclass(DeprecatedAttributeAlias, property), (
            "DeprecatedAttributeAlias must subclass property so Pydantic v2 routes"
            " __setattr__ through it"
        )

    def test_qualified_fallback_when_owner_unbound(self):
        """Descriptor never bound via `__set_name__` falls back to bare names."""
        descriptor = DeprecatedAttributeAlias(
            "canonical_name", removed_in="2.0.0", since="1.0.0"
        )
        message = descriptor._build_message()
        assert "canonical_name" in message
        assert "." not in message.split("`")[1], (
            f"Unbound descriptor should not prefix old name with a class, got: {message}"
        )

    def test_qualified_fallback_when_both_owner_and_old_name_missing(self):
        """The qualified-name helper survives a fully-unset state (defensive path)."""
        descriptor = DeprecatedAttributeAlias("canonical_name")
        descriptor._old_name = None
        descriptor._owner_name = None
        assert descriptor._qualified(None) == "<unknown>"

    def test_constructor_stores_introspection_fields(self):
        """`new_name`/`old_name` properties expose what was passed and discovered."""
        descriptor = _SampleHolder.__dict__["deprecatedName"]
        assert descriptor.new_name == "canonical_name"
        assert descriptor.old_name == "deprecatedName"

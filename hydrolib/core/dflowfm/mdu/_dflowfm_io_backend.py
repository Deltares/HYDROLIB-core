"""Adapter to the external `dflowfm_io` backend.

This module is the **single** place in hydrolib-core that imports the `dflowfm_io` package
(the auto-generated wrapper around the shared D-Flow FM IO C++ library). Everything else in
hydrolib-core talks to the backend through the functions here, so the dependency stays isolated
behind one seam.

Current state (early integration): the whole-document `validate` path is wired, and `covers` is
active via an interim bootstrap that probes property existence through the get error path. It will be
replaced by a dedicated `mdu_schema_has_property` C-API call over the compiled `mdu.json` schema
(design task A.2).

Design: `planning/dflowfm_io-validation-integration-design.md` in the Delft3D dflowfm_io tree.
"""

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

# The backend loads its native library at import time, so a missing package *or* a missing
# native lib both surface here. Absence must never break importing hydrolib-core: it just means
# the backend is unavailable and validation falls back to the existing Pydantic logic.
try:
    from dflowfm_io import MduDocument as _MduDocument
    from dflowfm_io import Severity as _Severity

    _IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - exercised only when the backend is absent
    _MduDocument = None
    _Severity = None
    _IMPORT_ERROR = exc


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation finding from the dflowfm_io backend.

    Decoupled from the backend's own `Issue` type so the rest of hydrolib-core never imports
    `dflowfm_io` directly.

    Attributes:
        line_number: 1-based source line the issue refers to, or a negative value if not tied
            to a specific line.
        severity: One of `"INFO"`, `"WARNING"`, `"ERROR"`.
        message: Human-readable description from the backend.
    """

    line_number: int
    severity: str
    message: str


def is_available() -> bool:
    """Return whether the dflowfm_io backend (package + native library) is usable."""
    return _MduDocument is not None


def unavailable_reason() -> str | None:
    """Return the import/load error that made the backend unavailable, or `None` if available."""
    return (
        None if is_available() else f"dflowfm_io backend not available: {_IMPORT_ERROR}"
    )


def validate(mdu_text: str) -> List[ValidationIssue]:
    """Validate a full MDU document with the dflowfm_io backend.

    Args:
        mdu_text: The complete MDU file content as a single string.

    Returns:
        All issues the backend reports for the document (INFO/WARNING/ERROR), in backend order.

    Raises:
        RuntimeError: If the backend is not available. Callers should guard with
            :func:`is_available` first; this is a defensive check, not a normal control path.
    """
    if not is_available():
        raise RuntimeError(unavailable_reason())

    document = _MduDocument()
    document.load_from_lines(mdu_text.splitlines())
    return [
        ValidationIssue(
            line_number=issue.line_number,
            severity=_Severity(issue.severity).name,
            message=issue.message,
        )
        for issue in document.report.get_issues()
    ]


_probe_document = None


def _property_exists(key: str) -> bool:
    """Best-effort check whether ``key`` (``section.property``) exists in the backend schema.

    Interim bootstrap (design task A.2): the backend has no dedicated schema query yet, so existence
    is probed through the get error path. A fresh ``MduDocument`` answers from schema defaults without
    loading a file; an unknown key raises with an "Unknown MDU property" message, while a *type*
    mismatch (e.g. reading an int key as a string) raises a different message. So only the
    unknown-property message counts as "does not exist"; every other outcome means the key exists.
    Replace with ``mdu_schema_has_property`` once A.2 lands.
    """
    global _probe_document
    if _probe_document is None:
        _probe_document = _MduDocument()
    try:
        _probe_document.model.get_string(key)
        return True
    except RuntimeError as exc:
        return "unknown mdu property" not in str(exc).lower()


def knows_property(section: str, key: str) -> bool:
    """Return whether the backend schema has ``key`` in ``section`` (case-insensitive)."""
    if not is_available():
        return False
    return _property_exists(f"{section}.{key}")


_covers_cache: dict = {}


def covers(section: str, aliases: Iterable[str]) -> bool:
    """Return whether the backend schema knows **every** given alias for ``section``.

    True only when the backend's key-set for the section is a superset of the aliases hydrolib would
    otherwise validate (the Tier-1 safety gate). Any alias the backend does not know ⇒ not a superset
    ⇒ ``False``, so Pydantic stays authoritative and delegation can't regress.

    Result is cached per (section, alias-set): these are class-level and constant, and this is called
    on every INI-model construction, so the schema is probed at most once per distinct section shape.
    """
    if not is_available():
        return False
    alias_tuple = tuple(aliases)
    if not alias_tuple:
        return False
    cache_key = (section.lower(), tuple(sorted(a.lower() for a in alias_tuple)))
    if cache_key not in _covers_cache:
        _covers_cache[cache_key] = all(
            _property_exists(f"{section}.{alias}") for alias in alias_tuple
        )
    return _covers_cache[cache_key]


# The backend reports issues as free text; the owning section is embedded as ``[section]`` in the
# message (e.g. "Property [geometry].BathymetryFile is not a supported property."). Attributing an
# issue to a section by parsing the message is interim — a structured section/key on the C-API issue
# type would remove this fragility (candidate backend feature request).
_SECTION_RE = re.compile(r"\[(\w+)\]")


def section_of(issue: "ValidationIssue") -> Optional[str]:
    """Return the lower-cased section an issue belongs to, or ``None`` if not attributable."""
    match = _SECTION_RE.search(issue.message)
    return match.group(1).lower() if match else None


def is_blocking(issue: "ValidationIssue") -> bool:
    """Return whether an issue should fail loading right now.

    Only the **unknown-keyword** check is currently delegated — it is Tier-1 (provably safe on
    covered sections, whose key-set is a superset of hydrolib's), and dflowfm_io reports it as an
    unsupported-property ``WARNING``. Value/type ``ERROR``s (e.g. an invalid datetime) belong to
    checks that still need Tier-2 corpus verification before they can be trusted to block — hydrolib
    and dflowfm_io demonstrably diverge on some of them — so they stay **advisory** until a check is
    added to the trusted-set. See design Sections 2-3.
    """
    return issue.severity == "WARNING" and "not a supported property" in issue.message

"""Adapter to the external ``dflowfm_io`` backend.

This module is the **single** place in hydrolib-core that talks to the ``dflowfm_io`` package (the
auto-generated wrapper around the shared D-Flow FM IO C++ library). The rest of hydrolib-core uses the
module-level :data:`backend` singleton, so the dependency stays isolated behind one object.

Current state (early integration): the whole-document :meth:`~DflowfmIoBackend.validate` path is wired,
and :meth:`~DflowfmIoBackend.covers` / :meth:`~DflowfmIoBackend.knows_property` are active via an
interim bootstrap that probes property existence through the get error path. That bootstrap is
replaced by a dedicated ``mdu_schema_has_property`` C-API call over the compiled ``mdu.json`` schema
(design task A.2).

Design: ``planning/dflowfm_io-validation-integration-design.md`` in the Delft3D dflowfm_io tree.
"""

import re
from dataclasses import dataclass
from typing import ClassVar, Iterable, List, Optional, Pattern


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation finding from the dflowfm_io backend.

    A value object decoupled from the backend's own ``Issue`` type (so nothing else in hydrolib-core
    imports ``dflowfm_io``), carrying the small amount of behaviour that belongs with the data.

    Attributes:
        line_number: 1-based source line the issue refers to, or a negative value if not tied to a
            specific line.
        severity: One of ``"INFO"``, ``"WARNING"``, ``"ERROR"``.
        message: Human-readable description from the backend.
    """

    line_number: int
    severity: str
    message: str

    # The backend reports issues as free text with the owning section embedded as ``[section]``
    # (e.g. "Property [geometry].BathymetryFile is not a supported property."). Attributing by parsing
    # the message is interim — a structured section/key on the C-API issue type would remove this.
    _SECTION_RE: ClassVar[Pattern] = re.compile(r"\[(\w+)\]")

    @property
    def section(self) -> Optional[str]:
        """The lower-cased section this issue belongs to, or ``None`` if not attributable."""
        match = self._SECTION_RE.search(self.message)
        return match.group(1).lower() if match else None

    @property
    def is_blocking(self) -> bool:
        """Whether this issue should fail loading right now.

        Only the **unknown-keyword** check is currently delegated — it is Tier-1 (provably safe on
        covered sections), reported by dflowfm_io as an unsupported-property ``WARNING``. Value/type
        ``ERROR``s (e.g. an invalid datetime) belong to checks that still need Tier-2 corpus
        verification — hydrolib and dflowfm_io demonstrably diverge on some — so they stay **advisory**
        until added to the trusted-set. See design Sections 2-3.
        """
        return self.severity == "WARNING" and "not a supported property" in self.message


class DflowfmIoBackend:
    """Object wrapper around the dflowfm_io native library.

    Owns everything stateful about the backend — the imported library, a reusable probe document, and
    the per-section coverage cache — so callers just hold the :data:`backend` singleton. The native
    library loads at construction; a missing package or native lib is captured, never raised, so
    importing hydrolib-core never breaks and the integration is simply inactive.
    """

    def __init__(self) -> None:
        try:
            from dflowfm_io import MduDocument, Severity

            self._document_cls = MduDocument
            self._severity_cls = Severity
            self._import_error: Optional[Exception] = None
        except Exception as exc:  # pragma: no cover - only when the backend is absent
            self._document_cls = None
            self._severity_cls = None
            self._import_error = exc

        self._probe_document = None
        self._covers_cache: dict = {}

    def is_available(self) -> bool:
        """Whether the dflowfm_io backend (package + native library) is usable."""
        return self._document_cls is not None

    def unavailable_reason(self) -> Optional[str]:
        """The import/load error that made the backend unavailable, or ``None`` if available."""
        if self.is_available():
            return None
        return f"dflowfm_io backend not available: {self._import_error}"

    def validate(self, mdu_text: str) -> List[ValidationIssue]:
        """Validate a full MDU document with the backend.

        Args:
            mdu_text: The complete MDU file content as a single string.

        Returns:
            All issues the backend reports (INFO/WARNING/ERROR), in backend order.

        Raises:
            RuntimeError: If the backend is not available. Callers should guard with
                :meth:`is_available` first; this is a defensive check, not a normal control path.
        """
        if not self.is_available():
            raise RuntimeError(self.unavailable_reason())

        document = self._document_cls()
        document.load_from_lines(mdu_text.splitlines())
        return [
            ValidationIssue(
                line_number=issue.line_number,
                severity=self._severity_cls(issue.severity).name,
                message=issue.message,
            )
            for issue in document.report.get_issues()
        ]

    def knows_property(self, section: str, key: str) -> bool:
        """Whether the backend schema has ``key`` in ``section`` (case-insensitive)."""
        if not self.is_available():
            return False
        return self._property_exists(f"{section}.{key}")

    def covers(self, section: str, aliases: Iterable[str]) -> bool:
        """Whether the backend schema knows **every** given alias for ``section``.

        True only when the backend's key-set for the section is a superset of the aliases hydrolib
        would otherwise validate (the Tier-1 safety gate). Any alias the backend does not know ⇒ not a
        superset ⇒ ``False``, so Pydantic stays authoritative and delegation can't regress.

        Cached per (section, alias-set): these are class-level and constant, and this runs on every
        INI-model construction, so the schema is probed at most once per distinct section shape.
        """
        if not self.is_available():
            return False
        alias_tuple = tuple(aliases)
        if not alias_tuple:
            return False
        cache_key = (section.lower(), tuple(sorted(a.lower() for a in alias_tuple)))
        if cache_key not in self._covers_cache:
            self._covers_cache[cache_key] = all(
                self._property_exists(f"{section}.{alias}") for alias in alias_tuple
            )
        return self._covers_cache[cache_key]

    def _property_exists(self, key: str) -> bool:
        """Best-effort existence check for ``key`` (``section.property``) via the get error path.

        Interim bootstrap (design task A.2): the backend has no dedicated schema query yet. A reused
        probe document answers from schema defaults without loading a file; an unknown key raises with
        an "Unknown MDU property" message, whereas a *type* mismatch (e.g. reading an int key as a
        string) raises a different message. So only the unknown-property message counts as "does not
        exist"; every other outcome means the key exists. Replaced by ``mdu_schema_has_property``.
        """
        if self._probe_document is None:
            self._probe_document = self._document_cls()
        try:
            self._probe_document.model.get_string(key)
            return True
        except RuntimeError as exc:
            return "unknown mdu property" not in str(exc).lower()


#: The single dflowfm_io backend used throughout hydrolib-core.
backend = DflowfmIoBackend()

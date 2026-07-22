"""Tests for the dflowfm_io backend adapter (whole-document ``validate`` path).

These require the ``dflowfm_io`` package and its native library to be importable; they are
skipped cleanly when the backend is unavailable so the suite still runs without it.
"""

from pathlib import Path

import pytest

from hydrolib.core.dflowfm.mdu import _dflowfm_io_backend as backend

pytestmark = pytest.mark.skipif(
    not backend.is_available(),
    reason=f"dflowfm_io backend unavailable: {backend.unavailable_reason()}",
)

MDU_FIXTURE = Path(__file__).parents[1] / "data/input/file_load_test/fm.mdu"


class TestDflowfmIoBackend:
    def test_is_available(self):
        assert backend.is_available() is True
        assert backend.unavailable_reason() is None

    def test_validate_returns_issues(self):
        issues = backend.validate(MDU_FIXTURE.read_text())
        assert isinstance(issues, list)
        assert (
            issues
        ), "expected the backend to report at least some issues (defaults/warnings)"
        first = issues[0]
        assert isinstance(first, backend.ValidationIssue)
        assert first.severity in {"INFO", "WARNING", "ERROR"}
        assert isinstance(first.line_number, int)
        assert isinstance(first.message, str)

    def test_validate_severities_are_valid_names(self):
        issues = backend.validate(MDU_FIXTURE.read_text())
        assert all(i.severity in {"INFO", "WARNING", "ERROR"} for i in issues)

    def test_covers_true_when_all_keys_known(self):
        # kmx and netFile both exist in the dflowfm_io schema.
        assert backend.covers("geometry", ["kmx", "netFile"]) is True

    def test_covers_false_when_a_key_is_unknown(self):
        # bathymetryFile is a hydrolib key the dflowfm_io schema does not (yet) have.
        assert backend.covers("geometry", ["kmx", "bathymetryFile"]) is False

    def test_covers_false_for_empty_aliases(self):
        assert backend.covers("geometry", []) is False


def _issue(message: str, severity: str = "WARNING", line: int = -1):
    return backend.ValidationIssue(line_number=line, severity=severity, message=message)


class TestBackendPolicyHelpers:
    """Pure helpers — no native library required, so these always run."""

    def test_section_of_parses_bracketed_section(self):
        assert (
            backend.section_of(_issue("Property [geometry].netFile ...")) == "geometry"
        )

    def test_section_of_returns_none_when_absent(self):
        assert backend.section_of(_issue("no section here")) is None

    def test_value_error_is_advisory_until_tier2(self):
        # Value/type ERRORs are not delegated yet (Tier-2 pending), so they must not block.
        msg = 'Property [restart].restartDateTime contains invalid value: "yyyymmddhhmmss".'
        assert backend.is_blocking(_issue(msg, severity="ERROR")) is False

    def test_is_blocking_unsupported_warning(self):
        msg = "Property [geometry].Foo is not a supported property."
        assert backend.is_blocking(_issue(msg, severity="WARNING")) is True

    def test_is_not_blocking_other_warning(self):
        assert (
            backend.is_blocking(_issue("just a heads up", severity="WARNING")) is False
        )

    def test_is_not_blocking_info(self):
        assert backend.is_blocking(_issue("default used", severity="INFO")) is False


class TestFMModelDelegation:
    """The active FMModel-level pass, exercised via a monkeypatched backend (no manifest needed)."""

    @staticmethod
    def _wire(monkeypatch, *, covered_section, issues):
        from hydrolib.core.dflowfm.mdu import models as mdu_models

        b = mdu_models.dflowfm_io_backend
        monkeypatch.setattr(b, "is_available", lambda: True)
        monkeypatch.setattr(
            b, "covers", lambda section, aliases: section.lower() == covered_section
        )
        monkeypatch.setattr(b, "validate", lambda mdu_text: issues)
        return mdu_models.FMModel

    def test_blocking_issue_in_covered_section_raises(self, monkeypatch):
        from pydantic import ValidationError

        FMModel = self._wire(
            monkeypatch,
            covered_section="geometry",
            issues=[_issue("Property [geometry].Foo is not a supported property.")],
        )
        with pytest.raises(ValidationError, match="dflowfm_io validation failed"):
            FMModel()

    def test_non_blocking_issue_does_not_raise(self, monkeypatch):
        FMModel = self._wire(
            monkeypatch,
            covered_section="geometry",
            issues=[_issue("Property [geometry].kmx default used", severity="INFO")],
        )
        FMModel()  # should construct fine

    def test_blocking_issue_in_uncovered_section_is_ignored(self, monkeypatch):
        FMModel = self._wire(
            monkeypatch,
            covered_section="geometry",  # only geometry is covered
            issues=[_issue("Property [numerics].Bar is not a supported property.")],
        )
        FMModel()  # numerics not covered -> issue ignored -> no raise

    def test_dflowfm_io_known_key_accepted_in_section(self):
        # B.3 behaviour change: [wind].windHuOrZwsBased exists in the dflowfm_io schema but is not a
        # hydrolib Wind field. Previously hydrolib rejected it as unknown; now it is accepted.
        from hydrolib.core.dflowfm.mdu.models import Wind

        Wind(windHuOrZwsBased="0")  # must not raise an unknown-keyword ValueError

    def test_key_unknown_to_both_still_rejected(self):
        from hydrolib.core.dflowfm.mdu.models import Wind

        with pytest.raises(ValueError, match="Unknown keywords"):
            Wind(totallyBogusKeyXyz="x")

    def test_value_error_in_covered_section_is_advisory(self, monkeypatch):
        # The regression we hit activating covers(): a value/type ERROR in a covered section must
        # NOT block (Tier-2 not verified yet) — only unknown-keyword issues are delegated.
        FMModel = self._wire(
            monkeypatch,
            covered_section="restart",
            issues=[
                _issue(
                    'Property [restart].restartDateTime contains invalid value: "yyyymmddhhmmss".',
                    severity="ERROR",
                )
            ],
        )
        FMModel()  # advisory -> no raise

"""Tests for the dflowfm_io backend adapter (whole-document ``validate`` path).

These require the `dflowfm_io` package and its native library to be importable; they are
skipped cleanly when the backend is unavailable so the suite still runs without it.
"""

from pathlib import Path

import pytest

from hydrolib.core.dflowfm.mdu.dflowfm_io import ValidationIssue, backend

pytestmark = pytest.mark.skipif(
    not backend.is_available(),
    reason=f"dflowfm_io backend unavailable: {backend.unavailable_reason()}",
)

MDU_FIXTURE = Path("tests/data/input/file_load_test/fm.mdu")


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
        assert isinstance(first, ValidationIssue)
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
        # A key that is not part of the dflowfm_io [geometry] schema (use a clearly-bogus name so the
        # test does not depend on which real keys the schema happens to include).
        assert backend.covers("geometry", ["kmx", "definitelyNotAnMduKeyXYZ"]) is False

    def test_covers_false_for_empty_aliases(self):
        assert backend.covers("geometry", []) is False


def _issue(message: str, severity: str = "WARNING", line: int = -1) -> ValidationIssue:
    return ValidationIssue(line_number=line, severity=severity, message=message)


class TestValidationIssue:
    """The value object's own behaviour — no native library required, so these always run."""

    def test_section_parses_bracketed_section(self):
        assert _issue("Property [geometry].netFile ...").section == "geometry"

    def test_section_is_none_when_absent(self):
        assert _issue("no section here").section is None

    def test_value_error_is_advisory_until_tier2(self):
        # Value/type ERRORs are not delegated yet (Tier-2 pending), so they must not block.
        msg = 'Property [restart].restartDateTime contains invalid value: "yyyymmddhhmmss".'
        assert _issue(msg, severity="ERROR").is_blocking is False

    def test_unsupported_property_warning_is_blocking(self):
        msg = "Property [geometry].Foo is not a supported property."
        assert _issue(msg, severity="WARNING").is_blocking is True

    def test_other_warning_is_not_blocking(self):
        assert _issue("just a heads up", severity="WARNING").is_blocking is False

    def test_info_is_not_blocking(self):
        assert _issue("default used", severity="INFO").is_blocking is False


class TestFMModelDelegation:
    """The active FMModel-level pass, exercised via a monkeypatched backend singleton."""

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

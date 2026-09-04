"""End-to-end tests: FMModel reads a real MDU file and both validation paths run on it.

A real fixture is loaded through the real ``FMModel`` (its Pydantic validators plus the
integrated dflowfm_io backend), and the dflowfm_io backend is also run directly on the same file. The
fixture loads cleanly in hydrolib, but dflowfm_io validates it more strictly — an empty required
`[geometry].netFile` and the `mdu.json` enum gap on `[numerics].vertAdvTypSal = 5`. Because those
are value/type checks that are not yet Tier-2 verified, the integration keeps them advisory, so the
hydrolib load still succeeds. One real file therefore exercises both stacks and pins down where, and
how, they differ.
"""

from pathlib import Path
from typing import List

import pytest

from hydrolib.core.dflowfm.mdu.dflowfm_io import ValidationIssue, backend
from hydrolib.core.dflowfm.mdu.models import FMModel

MDU_FILE = Path("tests/data/input/obsfile_cases/single_ini/fm.mdu")


@pytest.fixture(scope="module")
def fm_model() -> FMModel:
    """The fixture MDU loaded through hydrolib's FMModel (Pydantic + dflowfm_io integration)."""
    return FMModel(filepath=MDU_FILE, recurse=False)


@pytest.fixture(scope="module")
def backend_issues() -> List[ValidationIssue]:
    """The dflowfm_io backend's own validation of the same MDU file."""
    return backend.validate(MDU_FILE.read_text())


@pytest.fixture(scope="module")
def backend_errors(backend_issues: List[ValidationIssue]) -> List[ValidationIssue]:
    """Only the ERROR-severity findings from the backend."""
    return [issue for issue in backend_issues if issue.severity == "ERROR"]


class TestFMModelReadsRealMdu:
    """The Pydantic path: FMModel parses the file into a typed model."""

    def test_model_loads(self, fm_model: FMModel):
        assert isinstance(fm_model, FMModel)

    @pytest.mark.parametrize(
        "dotted_attribute, expected",
        [
            ("general.program", "D-Flow FM"),
            ("geometry.bedlevtype", 1),
            ("numerics.cflmax", 0.7),
            # Accepted by hydrolib; dflowfm_io rejects this enum value (see TestBackendValidatesSameFile).
            ("numerics.vertadvtypsal", 5),
        ],
    )
    def test_parses_typed_value(
        self, fm_model: FMModel, dotted_attribute: str, expected
    ):
        value = fm_model
        for attribute in dotted_attribute.split("."):
            value = getattr(value, attribute)
        assert value == expected


class TestBackendValidatesSameFile:
    """The dflowfm_io path: stricter, but advisory, so it does not block the hydrolib load."""

    def test_reports_issues(self, backend_issues: List[ValidationIssue]):
        assert backend_issues

    @pytest.mark.parametrize("expected_property", ["netFile", "vertAdvTypSal"])
    def test_reports_error_hydrolib_tolerates(
        self, backend_errors: List[ValidationIssue], expected_property: str
    ):
        assert any(expected_property in error.message for error in backend_errors)

    def test_all_errors_are_advisory(self, backend_errors: List[ValidationIssue]):
        assert backend_errors, "fixture is expected to produce backend ERRORs"
        assert all(error.is_blocking is False for error in backend_errors)

    def test_hydrolib_loads_despite_backend_errors(
        self, fm_model: FMModel, backend_errors: List[ValidationIssue]
    ):
        assert backend_errors, "fixture is expected to produce backend ERRORs"
        assert isinstance(fm_model, FMModel)

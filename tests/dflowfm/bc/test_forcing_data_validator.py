"""Tests for the `_reject_disk_only_on_recursive_load` AfterValidator on `ForcingData`.

This module validates that the `AfterValidator` correctly guards the `ForcingData`
annotated Union so that `DiskOnlyFileModel` is only accepted when the file load
context has `recurse=False`. Under a recursive load (`recurse=True`), a
`DiskOnlyFileModel` value must be rejected with a clear `ValueError`.

Module under test:
    `hydrolib.core.dflowfm.bc.models._reject_disk_only_on_recursive_load`
"""

import pytest
from pydantic import ValidationError

from hydrolib.core.base import DiskOnlyFileModel
from hydrolib.core.base.file_manager import (
    FileLoadContext,
    context_file_loading,
)
from hydrolib.core.base.utils import PathStyle
from hydrolib.core.dflowfm.bc.models import (
    ForcingModel,
    RealTime,
    _reject_disk_only_on_recursive_load,
)
from hydrolib.core.dflowfm.ext.models import Lateral, SourceSink


class TestRejectDiskOnlyOnRecursiveLoad:
    """Tests for _reject_disk_only_on_recursive_load validator function."""

    def test_non_disk_only_float_passes_through(self):
        """Float values pass through the validator unchanged.

        Test scenario:
            A float (valid ForcingData member) should be returned as-is regardless
            of load context, since the guard only checks DiskOnlyFileModel instances.
        """
        result = _reject_disk_only_on_recursive_load(3.14)
        assert result == 3.14, f"Expected 3.14, got {result}"

    def test_non_disk_only_realtime_passes_through(self):
        """RealTime enum values pass through the validator unchanged.

        Test scenario:
            RealTime.realtime should be returned as-is regardless of load context.
        """
        result = _reject_disk_only_on_recursive_load(RealTime.realtime)
        assert result is RealTime.realtime, f"Expected RealTime.realtime, got {result!r}"

    def test_non_disk_only_forcing_model_passes_through(self):
        """ForcingModel instances pass through the validator unchanged.

        Test scenario:
            A ForcingModel is the expected type under recursive loads, so it must
            never be rejected.
        """
        model = ForcingModel()
        result = _reject_disk_only_on_recursive_load(model)
        assert result is model, "ForcingModel should be returned by identity"

    def test_none_passes_through(self):
        """None passes through unchanged (for Optional[ForcingData] fields).

        Test scenario:
            None is not a DiskOnlyFileModel, so the isinstance check short-circuits
            and None is returned unchanged.
        """
        result = _reject_disk_only_on_recursive_load(None)
        assert result is None, f"None should pass through, got {result!r}"

    def test_disk_only_rejected_when_recurse_true(self):
        """DiskOnlyFileModel is rejected when the load context has recurse=True.

        Test scenario:
            Simulate a recursive load by setting up a FileLoadContext with
            `recurse=True`. The validator must raise a ValueError explaining
            that DiskOnlyFileModel is not valid in this context.
        """
        ctx = FileLoadContext()
        ctx.initialize_load_settings(
            recurse=True, resolve_casing=False, path_style=PathStyle.UNIXLIKE
        )
        token = context_file_loading.set(ctx)
        try:
            disk_model = DiskOnlyFileModel(filepath=None)
            with pytest.raises(ValueError, match="not valid for ForcingData"):
                _reject_disk_only_on_recursive_load(disk_model)
        finally:
            context_file_loading.reset(token)

    def test_disk_only_accepted_when_recurse_false(self):
        """DiskOnlyFileModel is accepted when the load context has recurse=False.

        Test scenario:
            Simulate a non-recursive load by setting up a FileLoadContext with
            `recurse=False`. The validator must allow DiskOnlyFileModel through
            since this is the legitimate case.
        """
        ctx = FileLoadContext()
        ctx.initialize_load_settings(
            recurse=False, resolve_casing=False, path_style=PathStyle.UNIXLIKE
        )
        token = context_file_loading.set(ctx)
        try:
            disk_model = DiskOnlyFileModel(filepath=None)
            result = _reject_disk_only_on_recursive_load(disk_model)
            assert result is disk_model, (
                f"DiskOnlyFileModel should pass through when recurse=False, got {result!r}"
            )
        finally:
            context_file_loading.reset(token)

    def test_disk_only_accepted_when_no_load_context(self):
        """DiskOnlyFileModel is accepted when no file load context exists.

        Test scenario:
            When models are constructed programmatically (outside of file loading),
            there is no active FileLoadContext (or _load_settings is None).
            The validator must not reject DiskOnlyFileModel in this case, allowing
            manual model construction.
        """
        # Ensure no context is set
        token = context_file_loading.set(FileLoadContext())
        context_file_loading.reset(token)

        disk_model = DiskOnlyFileModel(filepath=None)
        result = _reject_disk_only_on_recursive_load(disk_model)
        assert result is disk_model, (
            "DiskOnlyFileModel should pass through when no load context is active"
        )

    def test_disk_only_accepted_when_load_settings_not_initialized(self):
        """DiskOnlyFileModel is accepted when load settings have not been initialized.

        Test scenario:
            A FileLoadContext exists but `initialize_load_settings` was never called,
            so `_load_settings` is None. The validator must not reject
            DiskOnlyFileModel in this case.
        """
        ctx = FileLoadContext()
        # Do NOT call ctx.initialize_load_settings(...)
        token = context_file_loading.set(ctx)
        try:
            disk_model = DiskOnlyFileModel(filepath=None)
            result = _reject_disk_only_on_recursive_load(disk_model)
            assert result is disk_model, (
                "DiskOnlyFileModel should pass through when _load_settings is None"
            )
        finally:
            context_file_loading.reset(token)

    def test_error_message_is_descriptive(self):
        """The ValueError message mentions the expected types and the cause.

        Test scenario:
            Verify the error message contains actionable information: it should
            mention DiskOnlyFileModel, recurse=True, and the valid alternatives.
        """
        ctx = FileLoadContext()
        ctx.initialize_load_settings(
            recurse=True, resolve_casing=False, path_style=PathStyle.UNIXLIKE
        )
        token = context_file_loading.set(ctx)
        try:
            disk_model = DiskOnlyFileModel(filepath=None)
            with pytest.raises(ValueError) as exc_info:
                _reject_disk_only_on_recursive_load(disk_model)

            msg = str(exc_info.value)
            assert "DiskOnlyFileModel" in msg, (
                f"Error should mention DiskOnlyFileModel, got: {msg}"
            )
            assert "recurse=True" in msg, (
                f"Error should mention recurse=True, got: {msg}"
            )
            assert "ForcingModel" in msg, (
                f"Error should mention ForcingModel as alternative, got: {msg}"
            )
        finally:
            context_file_loading.reset(token)

    def test_disk_only_with_filepath_rejected_when_recurse_true(self):
        """DiskOnlyFileModel with an actual filepath is also rejected under recurse=True.

        Test scenario:
            Even if the DiskOnlyFileModel carries a real path, it should be rejected
            under recursive loading — the expectation is that the file should have
            been fully parsed into a ForcingModel.
        """
        ctx = FileLoadContext()
        ctx.initialize_load_settings(
            recurse=True, resolve_casing=False, path_style=PathStyle.UNIXLIKE
        )
        token = context_file_loading.set(ctx)
        try:
            disk_model = DiskOnlyFileModel(filepath="some/file.bc")
            with pytest.raises(ValueError, match="not valid for ForcingData"):
                _reject_disk_only_on_recursive_load(disk_model)
        finally:
            context_file_loading.reset(token)

    @pytest.mark.parametrize(
        "value",
        [0.0, -1.5, 1e10, ""],
        ids=["zero", "negative", "large", "empty_string"],
    )
    def test_non_disk_only_values_always_pass_through(self, value):
        """Non-DiskOnlyFileModel values always pass through regardless of context.

        Args:
            value: Various non-DiskOnlyFileModel values to test passthrough.

        Test scenario:
            The isinstance(v, DiskOnlyFileModel) check should short-circuit for
            any value that is not a DiskOnlyFileModel instance.
        """
        ctx = FileLoadContext()
        ctx.initialize_load_settings(
            recurse=True, resolve_casing=False, path_style=PathStyle.UNIXLIKE
        )
        token = context_file_loading.set(ctx)
        try:
            result = _reject_disk_only_on_recursive_load(value)
            assert result == value, f"Expected {value!r} to pass through, got {result!r}"
        finally:
            context_file_loading.reset(token)


class TestForcingDataIntegration:
    """Integration tests verifying the AfterValidator works within Pydantic model validation."""

    def test_lateral_accepts_disk_only_under_non_recursive_load(self):
        """A Lateral model accepts DiskOnlyFileModel for discharge when recurse=False.

        Test scenario:
            Simulate the real workflow: a non-recursive load produces a
            DiskOnlyFileModel from resolve_file_model, then Pydantic validates
            it into the Lateral.discharge field. The AfterValidator must allow it.
        """
        ctx = FileLoadContext()
        ctx.initialize_load_settings(
            recurse=False, resolve_casing=False, path_style=PathStyle.UNIXLIKE
        )
        token = context_file_loading.set(ctx)
        try:
            disk_model = DiskOnlyFileModel(filepath=None)
            lateral = Lateral(
                id="test_lateral",
                name="test",
                discharge=disk_model,
                locationType="1d",
                branchId="branch1",
                chainage=100.0,
            )
            assert isinstance(lateral.discharge, DiskOnlyFileModel), (
                f"Expected DiskOnlyFileModel, got {type(lateral.discharge).__name__}"
            )
        finally:
            context_file_loading.reset(token)

    def test_lateral_rejects_disk_only_under_recursive_load(self):
        """A Lateral model rejects DiskOnlyFileModel for discharge when recurse=True.

        Test scenario:
            Simulate a recursive load context and attempt to assign a
            DiskOnlyFileModel to the discharge field. Pydantic's AfterValidator
            should reject it with a ValidationError.
        """
        ctx = FileLoadContext()
        ctx.initialize_load_settings(
            recurse=True, resolve_casing=False, path_style=PathStyle.UNIXLIKE
        )
        token = context_file_loading.set(ctx)
        try:
            disk_model = DiskOnlyFileModel(filepath=None)
            with pytest.raises(ValidationError) as exc_info:
                Lateral(
                    id="test_lateral",
                    name="test",
                    discharge=disk_model,
                    locationType="1d",
                    branchId="branch1",
                    chainage=100.0,
                )
            assert "DiskOnlyFileModel" in str(exc_info.value), (
                f"ValidationError should mention DiskOnlyFileModel, got: {exc_info.value}"
            )
        finally:
            context_file_loading.reset(token)

    def test_lateral_accepts_float_under_recursive_load(self):
        """A Lateral model accepts float discharge values under recursive load.

        Test scenario:
            Float is always valid for ForcingData regardless of load context.
            Confirms the AfterValidator doesn't interfere with non-DiskOnlyFileModel values.
        """

        ctx = FileLoadContext()
        ctx.initialize_load_settings(
            recurse=True, resolve_casing=False, path_style=PathStyle.UNIXLIKE
        )
        token = context_file_loading.set(ctx)
        try:
            lateral = Lateral(
                id="test_lateral",
                name="test",
                discharge=5.0,
                locationType="1d",
                branchId="branch1",
                chainage=100.0,
            )
            assert lateral.discharge == 5.0, (
                f"Expected discharge=5.0, got {lateral.discharge}"
            )
        finally:
            context_file_loading.reset(token)

    def test_source_sink_accepts_disk_only_under_non_recursive_load(self):
        """A SourceSink model accepts DiskOnlyFileModel under non-recursive load.

        Test scenario:
            SourceSink has multiple ForcingData fields (discharge, salinitydelta,
            temperaturedelta). Verify the AfterValidator allows DiskOnlyFileModel
            for the main discharge field when recurse=False.
        """

        ctx = FileLoadContext()
        ctx.initialize_load_settings(
            recurse=False, resolve_casing=False, path_style=PathStyle.UNIXLIKE
        )
        token = context_file_loading.set(ctx)
        try:
            disk_model = DiskOnlyFileModel(filepath=None)
            source_sink = SourceSink(
                id="test_ss",
                name="test",
                discharge=disk_model,
                numCoordinates=1,
                xCoordinates=[0.0],
                yCoordinates=[0.0],
            )
            assert isinstance(source_sink.discharge, DiskOnlyFileModel), (
                f"Expected DiskOnlyFileModel, got {type(source_sink.discharge).__name__}"
            )
        finally:
            context_file_loading.reset(token)




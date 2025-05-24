from pathlib import Path
from typing import List

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.extold.models import (
    ExtOldExtrapolationMethod,
    ExtOldFileType,
    ExtOldForcing,
    ExtOldMethod,
    ExtOldModel,
    ExtOldQuantity,
    ExtOldTracerQuantity,
)
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.tim.models import TimModel


class TestExtForcing:
    def test_initialize_with_old_external_forcing_file(
        self,
        old_forcing_file: Path,
        old_forcing_file_quantities: List[str],
        old_forcing_comment_len: int,
    ):
        model = ExtOldModel(old_forcing_file)
        assert isinstance(model, ExtOldModel)
        assert len(model.comment) == old_forcing_comment_len
        assert len(model.forcing) == len(old_forcing_file_quantities)
        forcing_1 = model.forcing[0]
        assert isinstance(forcing_1, ExtOldForcing)
        quantities = [forcing.quantity for forcing in model.forcing]
        assert all([quantity in old_forcing_file_quantities for quantity in quantities])

    def test_initialize_with_timfile_initializes_timmodel(self, input_files_dir: Path):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename=input_files_dir.joinpath("tim/triple_data_for_timeseries.tim"),
            filetype=ExtOldFileType.TimeSeries,
            method=ExtOldMethod.InterpolateTimeAndSpaceSaveWeights,
            operand=Operand.override,
        )

        assert isinstance(forcing.filename, TimModel)

    def test_initialize_with_polyfile_initializes_polyfile(self, input_files_dir: Path):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename=input_files_dir.joinpath("dflowfm_individual_files/test.pli"),
            filetype=ExtOldFileType.Polyline,
            method=ExtOldMethod.InterpolateTimeAndSpaceSaveWeights,
            operand=Operand.override,
        )

        assert isinstance(forcing.filename, PolyFile)

    def test_initialize_with_unrecognized_file_initializes_diskonlyfilemodel(
        self, input_files_dir: Path
    ):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename=input_files_dir.joinpath("file_load_test/FlowFM_net.nc"),
            filetype=ExtOldFileType.NetCDFGridData,
            method=ExtOldMethod.InterpolateTimeAndSpaceSaveWeights,
            operand=Operand.override,
        )

        assert isinstance(forcing.filename, DiskOnlyFileModel)


class TestValidateQuantity:
    @pytest.mark.parametrize("quantity", ExtOldQuantity)
    def test_with_valid_quantity_string_equal_casing(self, quantity):
        quantity_str = quantity.value
        forcing = ExtOldForcing(
            quantity=quantity_str, filename="", filetype=9, method=1, operand="O"
        )
        assert forcing.quantity == quantity

    @pytest.mark.parametrize("quantity", ExtOldQuantity)
    def test_with_valid_quantity_string_different_casing(self, quantity):
        quantity_str = quantity.value.upper()
        forcing = ExtOldForcing(
            quantity=quantity_str, filename="", filetype=9, method=1, operand="O"
        )
        assert forcing.quantity == quantity

    @pytest.mark.parametrize("quantity", ExtOldQuantity)
    def test_with_valid_quantity_enum(self, quantity):
        forcing = ExtOldForcing(
            quantity=quantity, filename="", filetype=9, method=1, operand="O"
        )
        assert forcing.quantity == quantity

    @pytest.mark.parametrize("quantity", ExtOldTracerQuantity)
    def test_with_tracerquantity_appended_with_tracer_name(self, quantity):
        quantity_str = quantity + "Some_Tracer_Name"
        forcing = ExtOldForcing(
            quantity=quantity_str, filename="", filetype=9, method=1, operand="O"
        )
        assert forcing.quantity == quantity_str

    @pytest.mark.parametrize("quantity", ExtOldTracerQuantity)
    def test_with_just_a_tracerquantity_raises_error(self, quantity):
        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=quantity, filename="", filetype=9, method=1, operand="O"
            )

        exp_error = (
            f"QUANTITY '{quantity.value}' should be appended with a tracer name."
        )
        assert exp_error in str(error.value)

    @pytest.mark.parametrize("quantity", ExtOldTracerQuantity)
    def test_with_tracerquantity_string_without_tracer_name_raises_error(
        self, quantity
    ):
        quantity_str = quantity.value
        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=quantity_str,
                filename="",
                filetype=9,
                method=1,
                operand="O",
            )

        assert (
            f"QUANTITY '{quantity_str}' should be appended with a tracer name."
            in str(error.value)
        )

    def test_with_invalid_quantity_string_raises_value_error(
        self,
    ):
        quantity_str = "invalid"

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=quantity_str,
                filename="",
                filetype=9,
                method=1,
                operand="O",
            )

        supported_values_str = ", ".join(([x.value for x in ExtOldQuantity]))
        assert (
            f"QUANTITY 'invalid' not supported. Supported values: {supported_values_str}"
            in str(error.value)
        )


class TestValidateOperand:
    @pytest.mark.parametrize("operand", Operand)
    def test_with_valid_operand_string_equal_casing(self, operand):
        operand_str = operand.value
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            filetype=9,
            method=1,
            operand=operand_str,
        )
        assert forcing.operand == operand

    @pytest.mark.parametrize("operand", Operand)
    def test_with_valid_operand_string_different_casing(self, operand):
        operand_str = operand.value.lower()
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            filetype=9,
            method=1,
            operand=operand_str,
        )
        assert forcing.operand == operand

    @pytest.mark.parametrize("operand", Operand)
    def test_with_valid_operand_enum(self, operand):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            filetype=9,
            method=1,
            operand=operand,
        )
        assert forcing.operand == operand

    def test_with_invalid_operand_string_raises_value_error(
        self,
    ):
        operand_str = "invalid"

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=ExtOldQuantity.WaterLevelBnd,
                filename="",
                filetype=9,
                method=1,
                operand=operand_str,
            )

        supported_values_str = ", ".join(([x.value for x in Operand]))
        assert (
            f"OPERAND 'invalid' not supported. Supported values: {supported_values_str}"
            in str(error.value)
        )


class TestValidateVarName:
    def test_validate_varname_with_valid_filetype_11(self):
        filetype = 11
        varname = "some_varname"

        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            varname=varname,
            filetype=filetype,
            method=1,
            operand="O",
        )

        assert forcing.varname == varname

    def test_validate_varname_with_invalid_filetype(self):
        filetype = 9
        varname = "some_varname"

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=ExtOldQuantity.WaterLevelBnd,
                filename="",
                varname=varname,
                filetype=filetype,
                method=1,
                operand="O",
            )

        exp_msg = "VARNAME only allowed when FILETYPE is 11"
        assert exp_msg in str(error.value)


class TestValidateSourceMask:
    @pytest.mark.parametrize("filetype", [4, 6])
    def test_validate_sourcemask_with_valid_filetype_4_or_6(self, filetype):
        sourcemask = "sourcemask.file"

        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            sourcemask=sourcemask,
            filetype=filetype,
            method=1,
            operand="O",
        )

        assert forcing.sourcemask.filepath.name == sourcemask

    def test_validate_sourcemask_with_invalid_filetype(self):
        filetype = 9
        sourcemask = "sourcemask.file"

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=ExtOldQuantity.WaterLevelBnd,
                filename="",
                sourcemask=sourcemask,
                filetype=filetype,
                method=1,
                operand="O",
            )

        exp_msg = "SOURCEMASK only allowed when FILETYPE is 4 or 6"
        assert exp_msg in str(error.value)


class TestValidateExtrapolationMethod:
    def test_validate_extrapolation_method_with_valid_method_3(self):
        method = 3
        extrapolation_method = (
            ExtOldExtrapolationMethod.SpatialExtrapolationOutsideOfSourceDataBoundingBox
        )

        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            filetype=9,
            method=method,
            extrapolation_method=extrapolation_method,
            operand="O",
        )

        assert forcing.extrapolation_method == extrapolation_method

    def test_validate_extrapolation_method_with_invalid_method(self):
        method = 1
        extrapolation_method = (
            ExtOldExtrapolationMethod.SpatialExtrapolationOutsideOfSourceDataBoundingBox
        )

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=ExtOldQuantity.WaterLevelBnd,
                filename="",
                filetype=9,
                method=method,
                extrapolation_method=extrapolation_method,
                operand="O",
            )

        exp_msg = "EXTRAPOLATION_METHOD only allowed to be 1 when METHOD is 3"
        assert exp_msg in str(error.value)


class TestValidateMaxSearchRadius:
    def test_validate_maxsearchradius_method_with_valid_extrapolation_method_1(
        self,
    ):
        extrapolation_method = 1
        maxsearchradius = 1.23

        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.AirPressureWindXWindY,
            filename="",
            filetype=3,
            method=3,
            extrapolation_method=extrapolation_method,
            maxsearchradius=maxsearchradius,
            operand="O",
        )

        assert forcing.extrapolation_method == extrapolation_method

    def test_validate_maxsearchradius_method_with_invalid_extrapolation_method(
        self,
    ):
        extrapolation_method = 0
        maxsearchradius = 1.23

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=ExtOldQuantity.AirPressureWindXWindY,
                filename="",
                filetype=3,
                method=3,
                extrapolation_method=extrapolation_method,
                maxsearchradius=maxsearchradius,
                operand="O",
            )

        exp_msg = "MAXSEARCHRADIUS only allowed when EXTRAPOLATION_METHOD is 1"
        assert exp_msg in str(error.value)


class TestValidateValue:
    def test_validate_value_with_valid_method_4(self):
        method = 4
        value = 1.23

        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            filetype=9,
            method=method,
            operand="O",
            value=value,
        )

        assert forcing.value == pytest.approx(value)

    def test_validate_sourcemask_with_invalid_method(self):
        method = 1
        value = 1.23

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=ExtOldQuantity.WaterLevelBnd,
                filename="",
                filetype=9,
                method=method,
                operand="O",
                value=value,
            )

        exp_msg = "VALUE only allowed when METHOD is 4"
        assert exp_msg in str(error.value)


class TestValidateFactor:
    def test_validate_factor_with_valid_quantity_initialtracer(self):
        quantity = ExtOldTracerQuantity.InitialTracer + "Some_Tracer_Name"
        factor = 1.23

        forcing = ExtOldForcing(
            quantity=quantity,
            filename="",
            filetype=9,
            method=1,
            operand="O",
            factor=factor,
        )

        assert forcing.factor == pytest.approx(factor)

    def test_validate_factor_with_invalid_quantity(self):
        quantity = ExtOldQuantity.WaterLevelBnd
        factor = 1.23

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=quantity,
                filename="",
                filetype=9,
                method=1,
                operand="O",
                factor=factor,
            )

        exp_msg = "FACTOR only allowed when QUANTITY starts with initialtracer"
        assert exp_msg in str(error.value)


class TestValidateIFrcTyp:
    def test_validate_ifrctyp_with_valid_quantity_frictioncoefficient(self):
        quantity = ExtOldQuantity.FrictionCoefficient
        ifrctyp = 1.23

        forcing = ExtOldForcing(
            quantity=quantity,
            filename="",
            filetype=9,
            method=1,
            operand="O",
            ifrctyp=ifrctyp,
        )

        assert forcing.ifrctyp == pytest.approx(ifrctyp)

    def test_validate_ifrctyp_with_invalid_quantity(self):
        quantity = ExtOldQuantity.WaterLevelBnd
        ifrctyp = 1.23

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=quantity,
                filename="",
                filetype=9,
                method=1,
                operand="O",
                ifrctyp=ifrctyp,
            )

        exp_msg = "IFRCTYP only allowed when QUANTITY is frictioncoefficient"
        assert exp_msg in str(error.value)


class TestValidateAveragingType:
    def test_validate_averagingtype_with_valid_method_6(self):
        method = 6
        averagingtype = 1.23

        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            filetype=9,
            method=method,
            operand="O",
            averagingtype=averagingtype,
        )

        assert forcing.averagingtype == pytest.approx(averagingtype)

    def test_validate_averagingtype_with_invalid_method(self):
        method = 1
        averagingtype = 1.23

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=ExtOldQuantity.WaterLevelBnd,
                filename="",
                filetype=9,
                method=method,
                operand="O",
                averagingtype=averagingtype,
            )

        exp_msg = "AVERAGINGTYPE only allowed when METHOD is 6"
        assert exp_msg in str(error.value)


class TestValidateRelativeSearchCellSize:
    def test_validate_relativesearchcellsize_with_valid_method_6(self):
        method = 6
        relativesearchcellsize = 1.23

        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            filetype=9,
            method=method,
            operand="O",
            relativesearchcellsize=relativesearchcellsize,
        )

        assert forcing.relativesearchcellsize == pytest.approx(relativesearchcellsize)

    def test_validate_relativesearchcellsize_with_invalid_method(self):
        method = 1
        relativesearchcellsize = 1.23

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=ExtOldQuantity.WaterLevelBnd,
                filename="",
                filetype=9,
                method=method,
                operand="O",
                relativesearchcellsize=relativesearchcellsize,
            )

        exp_msg = "RELATIVESEARCHCELLSIZE only allowed when METHOD is 6"
        assert exp_msg in str(error.value)


class TestValidateExtrapolTol:
    def test_validate_extrapoltol_with_valid_method_5(self):
        method = 5
        extrapoltol = 1.23

        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            filetype=9,
            method=method,
            operand="O",
            extrapoltol=extrapoltol,
        )

        assert forcing.extrapoltol == pytest.approx(extrapoltol)

    def test_validate_extrapoltol_with_invalid_method(self):
        method = 1
        extrapoltol = 1.23

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=ExtOldQuantity.WaterLevelBnd,
                filename="",
                filetype=9,
                method=method,
                operand="O",
                extrapoltol=extrapoltol,
            )

        exp_msg = "EXTRAPOLTOL only allowed when METHOD is 5"
        assert exp_msg in str(error.value)


class TestValidatePercentileMinMax:
    def test_validate_percentileminmax_with_valid_method_6(self):
        method = 6
        percentileminmax = 1.23

        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            filetype=9,
            method=method,
            operand="O",
            percentileminmax=percentileminmax,
        )

        assert forcing.percentileminmax == pytest.approx(percentileminmax)

    def test_validate_percentileminmax_with_invalid_method(self):
        method = 1
        percentileminmax = 1.23

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=ExtOldQuantity.WaterLevelBnd,
                filename="",
                filetype=9,
                method=method,
                operand="O",
                percentileminmax=percentileminmax,
            )

        exp_msg = "PERCENTILEMINMAX only allowed when METHOD is 6"
        assert exp_msg in str(error.value)


class TestValidateArea:
    def test_validate_area_with_valid_quantity_discharge_salinity_temperature_sorsin(
        self,
    ):
        quantity = ExtOldQuantity.DischargeSalinityTemperatureSorSin
        area = 1.23

        forcing = ExtOldForcing(
            quantity=quantity,
            filename="",
            filetype=9,
            method=1,
            operand="O",
            area=area,
        )

        assert forcing.area == pytest.approx(area)

    def test_validate_area_with_invalid_quantity(self):
        quantity = ExtOldQuantity.WaterLevelBnd
        area = 1.23

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=quantity,
                filename="",
                filetype=9,
                method=1,
                operand="O",
                area=area,
            )

        exp_msg = (
            "AREA only allowed when QUANTITY is discharge_salinity_temperature_sorsin"
        )
        assert exp_msg in str(error.value)


class TestValidateNumMin:
    def test_validate_nummin_with_valid_method_6(self):
        method = 6
        nummin = 123

        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename="",
            filetype=9,
            method=method,
            operand="O",
            nummin=nummin,
        )

        assert forcing.nummin == nummin

    def test_validate_nummin_with_invalid_method(self):
        method = 1
        nummin = 123

        with pytest.raises(ValueError) as error:
            _ = ExtOldForcing(
                quantity=ExtOldQuantity.WaterLevelBnd,
                filename="",
                filetype=9,
                method=method,
                operand="O",
                nummin=nummin,
            )

        exp_msg = "NUMMIN only allowed when METHOD is 6"
        assert exp_msg in str(error.value)

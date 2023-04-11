from pathlib import Path

import pytest

from hydrolib.core.basemodel import (
    DiskOnlyFileModel,
    ModelSaveSettings,
    SerializerConfig,
)
from hydrolib.core.dflowfm.extold.models import (
    ExtOldForcing,
    ExtOldModel,
    ExtOldFileType,
    ExtOldMethod,
    ExtOldOperand,
    ExtOldQuantity,
    ExtOldTracerQuantity,
)
from hydrolib.core.dflowfm.extold.parser import Parser
from hydrolib.core.dflowfm.extold.serializer import Serializer
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.tim.models import TimModel

from ..utils import (
    assert_files_equal,
    create_temp_file_from_lines,
    get_temp_file,
    test_input_dir,
)


class TestExtForcing:
    def test_initialize_with_timfile_initializes_timmodel(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename=test_input_dir / "tim" / "triple_data_for_timeseries.tim",
            filetype=ExtOldFileType.TimeSeries,
            method=ExtOldMethod.InterpolateTimeAndSpaceSaveWeights,
            operand=ExtOldOperand.OverwriteExistingValues,
        )

        assert isinstance(forcing.filename, TimModel)

    def test_initialize_with_polyfile_initializes_polyfile(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename=test_input_dir / "dflowfm_individual_files" / "test.pli",
            filetype=ExtOldFileType.Polyline,
            method=ExtOldMethod.InterpolateTimeAndSpaceSaveWeights,
            operand=ExtOldOperand.OverwriteExistingValues,
        )

        assert isinstance(forcing.filename, PolyFile)

    def test_initialize_with_unrecognized_file_initializes_diskonlyfilemodel(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename=Path(test_input_dir / "file_load_test" / "FlowFM_net.nc"),
            filetype=ExtOldFileType.NetCDFGridData,
            method=ExtOldMethod.InterpolateTimeAndSpaceSaveWeights,
            operand=ExtOldOperand.OverwriteExistingValues,
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
        @pytest.mark.parametrize("operand", ExtOldOperand)
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

        @pytest.mark.parametrize("operand", ExtOldOperand)
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

        @pytest.mark.parametrize("operand", ExtOldOperand)
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

            supported_values_str = ", ".join(([x.value for x in ExtOldOperand]))
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

            assert forcing.value == value

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

            assert forcing.factor == factor

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

            assert forcing.ifrctyp == ifrctyp

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

            assert forcing.averagingtype == averagingtype

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

            assert forcing.relativesearchcellsize == relativesearchcellsize

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

            assert forcing.extrapoltol == extrapoltol

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

            assert forcing.percentileminmax == percentileminmax

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

            assert forcing.area == area

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

            exp_msg = "AREA only allowed when QUANTITY is discharge_salinity_temperature_sorsin"
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


class TestExtOldModel:
    def test_initialization(self):
        model = ExtOldModel()

        assert len(model.comment) == 0
        assert len(model.forcing) == 0

    def test_load_model(self):
        file_content = [
            "* This is a comment",
            "* This is a comment",
            "",
            "QUANTITY=internaltidesfrictioncoefficient",
            "FILENAME=surroundingDomain.pol",
            "FILETYPE=11",
            "METHOD=4",
            "OPERAND=+",
            "VALUE=0.0125",
            "",
            "* This is a comment",
            "",
            "QUANTITY=waterlevelbnd",
            "FILENAME=OB_001_orgsize.pli",
            "FILETYPE=9",
            "METHOD=3",
            "* This is a comment",
            "OPERAND=O",
            "* This is a comment",
        ]

        with create_temp_file_from_lines(
            file_content, "test_load_model_two_blocks.ext"
        ) as temp_file:
            model = ExtOldModel(filepath=temp_file)

        # Assert correct comments
        assert len(model.comment) == 3
        exp_comments = [" This is a comment", " This is a comment", ""]
        assert model.comment == exp_comments

        # Assert correct forcings
        assert len(model.forcing) == 2

        forcing_1 = model.forcing[0]
        assert forcing_1.quantity == ExtOldQuantity.InternalTidesFrictionCoefficient
        assert forcing_1.filename.filepath == Path("surroundingDomain.pol")
        assert forcing_1.varname == None
        assert forcing_1.sourcemask.filepath == None
        assert forcing_1.filetype == ExtOldFileType.NetCDFGridData
        assert forcing_1.method == ExtOldMethod.InterpolateSpace
        assert forcing_1.operand == ExtOldOperand.SuperimposeNewValues
        assert forcing_1.value == 0.0125
        assert forcing_1.factor == None
        assert forcing_1.ifrctyp == None
        assert forcing_1.averagingtype == None
        assert forcing_1.relativesearchcellsize == None
        assert forcing_1.extrapoltol == None
        assert forcing_1.percentileminmax == None
        assert forcing_1.area == None
        assert forcing_1.nummin == None

        forcing_2 = model.forcing[1]
        assert forcing_2.quantity == ExtOldQuantity.WaterLevelBnd
        assert forcing_2.filename.filepath == Path("OB_001_orgsize.pli")
        assert forcing_2.varname == None
        assert forcing_2.sourcemask.filepath == None
        assert forcing_2.filetype == ExtOldFileType.Polyline
        assert forcing_2.method == ExtOldMethod.InterpolateTimeAndSpaceSaveWeights
        assert forcing_2.operand == ExtOldOperand.OverwriteExistingValues
        assert forcing_2.value == None
        assert forcing_2.factor == None
        assert forcing_2.ifrctyp == None
        assert forcing_2.averagingtype == None
        assert forcing_2.relativesearchcellsize == None
        assert forcing_2.extrapoltol == None
        assert forcing_2.percentileminmax == None
        assert forcing_2.area == None
        assert forcing_2.nummin == None

    def test_save_model(self):

        exp_file_content = [
            "*This is a comment",
            "*This is a comment",
            "*",
            "QUANTITY=internaltidesfrictioncoefficient",
            "FILENAME=surroundingDomain.pol",
            "FILETYPE=11",
            "METHOD=4",
            "OPERAND=+",
            "VALUE=0.012500",
            "",
            "QUANTITY=waterlevelbnd",
            "FILENAME=OB_001_orgsize.pli",
            "FILETYPE=9",
            "METHOD=3",
            "OPERAND=O",
        ]

        comments = ["This is a comment", "This is a comment", ""]

        forcing_1 = ExtOldForcing(
            quantity=ExtOldQuantity.InternalTidesFrictionCoefficient,
            filename=Path("surroundingDomain.pol"),
            filetype=ExtOldFileType.NetCDFGridData,
            method=ExtOldMethod.InterpolateSpace,
            operand=ExtOldOperand.SuperimposeNewValues,
            value=0.0125,
        )

        forcing_2 = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename=Path("OB_001_orgsize.pli"),
            filetype=ExtOldFileType.Polyline,
            method=ExtOldMethod.InterpolateTimeAndSpaceSaveWeights,
            operand=ExtOldOperand.OverwriteExistingValues,
        )

        model = ExtOldModel(comment=comments, forcing=[forcing_1, forcing_2])

        model.serializer_config.float_format = "f"

        with get_temp_file("test_save_model.ext") as file:
            model.save(filepath=file)

            with create_temp_file_from_lines(
                exp_file_content, "test_save_model_expected.ext"
            ) as exp_file:
                assert_files_equal(file, exp_file)


class TestParser:
    def test_parse_two_blocks_parses_to_the_correct_dictionaries(self):
        file_content = [
            "* This is a comment",
            "* This is a comment",
            "",
            "QUANTITY=internaltidesfrictioncoefficient",
            "FILENAME=surroundingDomain.pol",
            "FILETYPE=11",
            "METHOD=4",
            "OPERAND=+",
            "VALUE=0.0125",
            "",
            "* This is a comment",
            "",
            "QUANTITY=waterlevelbnd",
            "FILENAME=OB_001_orgsize.pli",
            "FILETYPE=9",
            "METHOD=3",
            "* This is a comment",
            "OPERAND=O",
            "* This is a comment",
        ]

        parser = Parser()

        with create_temp_file_from_lines(file_content, "two_blocks.ext") as temp_file:
            data = parser.parse(filepath=temp_file)

        exp_data = {
            "comment": [" This is a comment", " This is a comment", ""],
            "forcing": [
                {
                    "QUANTITY": "internaltidesfrictioncoefficient",
                    "FILENAME": "surroundingDomain.pol",
                    "FILETYPE": "11",
                    "METHOD": "4",
                    "OPERAND": "+",
                    "VALUE": "0.0125",
                },
                {
                    "QUANTITY": "waterlevelbnd",
                    "FILENAME": "OB_001_orgsize.pli",
                    "FILETYPE": "9",
                    "METHOD": "3",
                    "OPERAND": "O",
                },
            ],
        }

        assert data == exp_data

    def test_parse_block_with_incorrect_order_raises_error(self):
        file_lines = [
            "FILENAME=surroundingDomain.pol",
            "QUANTITY=internaltidesfrictioncoefficient",
            "FILETYPE=11",
            "OPERAND=+",
            "VALUE=0.0125",
            "QUANTITY=internaltidesfrictioncoefficient",
        ]

        parser = Parser()

        with create_temp_file_from_lines(
            file_lines, "incorrect_order.ext"
        ) as temp_file:
            with pytest.raises(ValueError) as error:
                parser.parse(filepath=temp_file)

        exp_error = "Line 1: Properties should be in the following order: QUANTITY, FILENAME, FILETYPE, OPERAND, VALUE"
        assert str(error.value) == exp_error


class TestSerializer:
    def test_serialize(self):
        exp_file_content = [
            "*This is a comment",
            "*This is a comment",
            "*",
            "QUANTITY=internaltidesfrictioncoefficient",
            "FILENAME=surroundingDomain.pol",
            "FILETYPE=11",
            "METHOD=4",
            "OPERAND=+",
            "VALUE=0.012500",
            "",
            "QUANTITY=waterlevelbnd",
            "FILENAME=OB_001_orgsize.pli",
            "FILETYPE=9",
            "METHOD=3",
            "OPERAND=O",
        ]

        comments = ["This is a comment", "This is a comment", ""]

        forcing_1 = {
            "quantity": "internaltidesfrictioncoefficient",
            "filename": DiskOnlyFileModel(Path("surroundingDomain.pol")),
            "filetype": 11,
            "method": 4,
            "operand": "+",
            "value": 0.0125,
        }

        forcing_2 = {
            "quantity": "waterlevelbnd",
            "filename": DiskOnlyFileModel(Path("OB_001_orgsize.pli")),
            "filetype": 9,
            "method": 3,
            "operand": "O",
        }

        forcing_data = {"comment": comments, "forcing": [forcing_1, forcing_2]}

        serializer_config = SerializerConfig(float_format="f")
        save_settings = ModelSaveSettings()

        with get_temp_file("test_serialize.ext") as file:
            Serializer.serialize(file, forcing_data, serializer_config, save_settings)

            with create_temp_file_from_lines(
                exp_file_content, "test_serialize_expected.ext"
            ) as exp_file:
                assert_files_equal(file, exp_file)

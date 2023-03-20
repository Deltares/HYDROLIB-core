import pytest

from hydrolib.core.dflowfm.extold.models import ExtForcing, Operand, Quantity


class TestExtForcing:
    class TestValidateQuantity:
        @pytest.mark.parametrize("quantity", Quantity)
        def test_with_valid_quantity_string_equal_casing(self, quantity):
            quantity_str = quantity.value
            forcing = ExtForcing(
                quantity=quantity_str, filename="", filetype=9, method=1, operand="O"
            )
            assert forcing.quantity == quantity

        @pytest.mark.parametrize("quantity", Quantity)
        def test_with_valid_quantity_string_different_casing(self, quantity):
            quantity_str = quantity.value.upper()
            forcing = ExtForcing(
                quantity=quantity_str, filename="", filetype=9, method=1, operand="O"
            )
            assert forcing.quantity == quantity

        @pytest.mark.parametrize("quantity", Quantity)
        def test_with_valid_quantity_enum(self, quantity):
            forcing = ExtForcing(
                quantity=quantity, filename="", filetype=9, method=1, operand="O"
            )
            assert forcing.quantity == quantity

        def test_with_valid_tracerbnd_quantity_string(self):
            quantity_str = Quantity.TracerBnd.value + "Some_Tracer_Name"
            forcing = ExtForcing(
                quantity=quantity_str, filename="", filetype=9, method=1, operand="O"
            )
            assert forcing.quantity == quantity_str

        def test_with_valid_initialtracer_quantity_string(self):
            quantity_str = Quantity.InitialTracer.value + "Some_Tracer_Name"
            forcing = ExtForcing(
                quantity=quantity_str, filename="", filetype=9, method=1, operand="O"
            )
            assert forcing.quantity == quantity_str

        def test_with_invalid_quantity_string_raises_value_error(
            self,
        ):
            quantity_str = "invalid"

            with pytest.raises(ValueError) as error:
                _ = ExtForcing(
                    quantity=quantity_str,
                    filename="",
                    filetype=9,
                    method=1,
                    operand="O",
                )

            supported_values_str = ", ".join(([x.value for x in Quantity]))
            assert (
                f"QUANTITY 'invalid' not supported. Supported values: {supported_values_str}"
                in str(error.value)
            )

    class TestValidateOperand:
        @pytest.mark.parametrize("operand", Operand)
        def test_with_valid_operand_string_equal_casing(self, operand):
            operand_str = operand.value
            forcing = ExtForcing(
                quantity=Quantity.WaterLevelBnd,
                filename="",
                filetype=9,
                method=1,
                operand=operand_str,
            )
            assert forcing.operand == operand

        @pytest.mark.parametrize("operand", Operand)
        def test_with_valid_operand_string_different_casing(self, operand):
            operand_str = operand.value.lower()
            forcing = ExtForcing(
                quantity=Quantity.WaterLevelBnd,
                filename="",
                filetype=9,
                method=1,
                operand=operand_str,
            )
            assert forcing.operand == operand

        @pytest.mark.parametrize("operand", Operand)
        def test_with_valid_operand_enum(self, operand):
            forcing = ExtForcing(
                quantity=Quantity.WaterLevelBnd,
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
                _ = ExtForcing(
                    quantity=Quantity.WaterLevelBnd,
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

            forcing = ExtForcing(
                quantity=Quantity.WaterLevelBnd,
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
                _ = ExtForcing(
                    quantity=Quantity.WaterLevelBnd,
                    filename="",
                    varname=varname,
                    filetype=filetype,
                    method=1,
                    operand="O",
                )

            exp_msg = "VARNAME only allowed when FILETYPE is 11 (NetCDF grid data)"
            assert exp_msg in str(error.value)

    class TestValidateSourceMask:
        @pytest.mark.parametrize("filetype", [4, 6])
        def test_validate_sourcemask_with_valid_filetype_4_or_6(self, filetype):
            sourcemask = "sourcemask.file"

            forcing = ExtForcing(
                quantity=Quantity.WaterLevelBnd,
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
                _ = ExtForcing(
                    quantity=Quantity.WaterLevelBnd,
                    filename="",
                    sourcemask=sourcemask,
                    filetype=filetype,
                    method=1,
                    operand="O",
                )

            exp_msg = "SOURCEMASK only allowed when FILETYPE is 4 (ArcInfo) or 6 (Curvilinear data)"
            assert exp_msg in str(error.value)

    class TestValidateValue:
        def test_validate_value_with_valid_method_4(self):
            method = 4
            value = 1.23

            forcing = ExtForcing(
                quantity=Quantity.WaterLevelBnd,
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
                _ = ExtForcing(
                    quantity=Quantity.WaterLevelBnd,
                    filename="",
                    filetype=9,
                    method=method,
                    operand="O",
                    value=value,
                )

            exp_msg = "VALUE only allowed when METHOD is 4 (Interpolate space)"
            assert exp_msg in str(error.value)

    class TestValidateFactor:
        def test_validate_factor_with_valid_quantity_initialtracer(self):
            quantity = Quantity.InitialTracer + "Some_Tracer_Name"
            factor = 1.23

            forcing = ExtForcing(
                quantity=quantity,
                filename="",
                filetype=9,
                method=1,
                operand="O",
                factor=factor,
            )

            assert forcing.factor == factor

        def test_validate_factor_with_invalid_quantity(self):
            quantity = Quantity.WaterLevelBnd
            factor = 1.23

            with pytest.raises(ValueError) as error:
                _ = ExtForcing(
                    quantity=quantity,
                    filename="",
                    filetype=9,
                    method=1,
                    operand="O",
                    factor=factor,
                )

            exp_msg = f"FACTOR only allowed when QUANTITY starts with {Quantity.InitialTracer}"
            assert exp_msg in str(error.value)

    class TestValidateIFrcTyp:
        def test_validate_ifrctyp_with_valid_quantity_frictioncoefficient(self):
            quantity = Quantity.FrictionCoefficient
            ifrctyp = 1.23

            forcing = ExtForcing(
                quantity=quantity,
                filename="",
                filetype=9,
                method=1,
                operand="O",
                ifrctyp=ifrctyp,
            )

            assert forcing.ifrctyp == ifrctyp

        def test_validate_ifrctyp_with_invalid_quantity(self):
            quantity = Quantity.WaterLevelBnd
            ifrctyp = 1.23

            with pytest.raises(ValueError) as error:
                _ = ExtForcing(
                    quantity=quantity,
                    filename="",
                    filetype=9,
                    method=1,
                    operand="O",
                    ifrctyp=ifrctyp,
                )

            exp_msg = (
                f"IFRCTYP only allowed when QUANTITY is {Quantity.FrictionCoefficient}"
            )
            assert exp_msg in str(error.value)

    class TestValidateAveragingType:
        def test_validate_averagingtype_with_valid_method_6(self):
            method = 6
            averagingtype = 1.23

            forcing = ExtForcing(
                quantity=Quantity.WaterLevelBnd,
                filename="",
                filetype=9,
                method=method,
                operand="O",
                averagingtype=averagingtype,
            )

            assert forcing.averagingtype == averagingtype

        def test_validate_sourcemask_with_invalid_method(self):
            method = 1
            averagingtype = 1.23

            with pytest.raises(ValueError) as error:
                _ = ExtForcing(
                    quantity=Quantity.WaterLevelBnd,
                    filename="",
                    filetype=9,
                    method=method,
                    operand="O",
                    averagingtype=averagingtype,
                )

            exp_msg = "AVERAGINGTYPE only allowed when METHOD is 6 (Averaging)"
            assert exp_msg in str(error.value)

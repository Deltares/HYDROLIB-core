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

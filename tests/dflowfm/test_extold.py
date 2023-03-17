import pytest
from hydrolib.core.dflowfm.extold.models import ExtForcing, Operand, Quantity


class TestExtForcing:

    class TestValidateQuantity:
        @pytest.mark.parametrize("quantity", Quantity)
        def test_quantity_validation_with_valid_quantity_string(self, quantity):
            quantity_str = quantity.value
            forcing = ExtForcing(quantity=quantity_str, filename="", filetype=9, method=1, operand="O")
            assert forcing.quantity == quantity

        @pytest.mark.parametrize("quantity", Quantity)
        def test_quantity_validation_with_valid_quantity(self, quantity):
            forcing = ExtForcing(quantity=quantity, filename="", filetype=9, method=1, operand="O")
            assert forcing.quantity == quantity

        def test_quantity_validation_with_valid_tracerbnd_quantity_string(self):
            quantity_str = Quantity.TracerBnd.value + "some_tracer_name"
            forcing = ExtForcing(quantity=quantity_str, filename="", filetype=9, method=1, operand="O")
            assert forcing.quantity == quantity_str

        def test_quantity_validation_with_valid_initialtracer_quantity_string(self):
            quantity_str = Quantity.InitialTracer.value + "some_tracer_name"
            forcing = ExtForcing(quantity=quantity_str, filename="", filetype=9, method=1, operand="O")
            assert forcing.quantity == quantity_str

        def test_quantity_validation_with_invalid_quantity_string_raises_value_error(self):
            quantity_str = "invalid"

            with pytest.raises(ValueError) as error:
                _ = ExtForcing(quantity=quantity_str, filename="", filetype=9, method=1, operand="O")
            
            supported_values_str = ", ".join(([x.value for x in Quantity]))
            assert f"Quantity 'invalid' not supported. Supported values: {supported_values_str}" in str(error.value)

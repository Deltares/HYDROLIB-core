from hydrolib.core.io.structure.models import FlowDirection, Weir
from hydrolib.core.io.ini.parser import Parser, ParserConfig
from pydantic.generics import GenericModel
from typing import Generic, TypeVar

import inspect


TWrapper = TypeVar("TWrapper")


class TestWrapper(GenericModel, Generic[TWrapper]):
    val: TWrapper


def test_weir_construction_with_parser():
    parser = Parser(ParserConfig())

    input_str = inspect.cleandoc(
        """
        [Structure]
        id                = weir_id     # Unique structure id (max. 256 characters).
        name              = weir        # Given name in the user interface.
        branchId          = branch      # (optional) Branch on which the structure is located.
        chainage          = 3.0         # (optional)   Chanage on the branch (m)
        type              = weir        # Structure type
        allowedFlowdir    = positive    # Possible values: both, positive, negative, none.
        crestLevel        = 10.5        # Crest level of weir (m AD)
        crestWidth        = 5           # Width of weir (m)
        useVelocityHeight = false       # Flag indicates whether the velocity height is to be calculated or not.
        """
    )

    for line in input_str.splitlines():
        parser.feed_line(line)

    document = parser.finalize()

    wrapper = TestWrapper[Weir].parse_obj({"val": document.sections[0]})
    weir = wrapper.val

    assert weir.id.value == "weir_id"
    assert weir.name.value == "weir"
    assert weir.branch_id.value == "branch"
    assert weir.chainage.value == 3.0
    assert weir.structure_type.value == "weir"
    assert weir.allowed_flow_direction.value == FlowDirection.POSITIVE
    assert weir.crest_level.value == 10.5
    assert weir.crest_width.value == 5
    assert weir.use_velocity_height.value == False

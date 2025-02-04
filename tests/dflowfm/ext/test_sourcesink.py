"""
Class to test all methods contained in the
hydrolib.core.dflowfm.ext.models.SourceSink class
"""

from typing import Dict, List, Optional

import numpy as np
import pytest
from pydantic.v1 import ValidationError

from hydrolib.core.dflowfm.bc.models import Constant, ForcingModel, RealTime
from hydrolib.core.dflowfm.ext.models import ExtModel, SourceSink
from hydrolib.core.dflowfm.ini.models import INIBasedModel
from tests.utils import test_data_dir


class TestSourceSink:
    """
    Class to test the different types of source/sink forcings.
    """

    def test_sourcesink_fromfile(self):

        filepath = test_data_dir / "input/source-sink/source-sink-new.ext"
        m = ExtModel(filepath)
        assert len(m.sourcesink) == 2
        assert m.sourcesink[0].id == "L1"
        assert np.isclose(m.sourcesink[0].discharge, 10)
        assert np.isclose(m.sourcesink[1].discharge, 20)

    def test_sourcesink_fromdict(self):

        data = {
            "sourcesink": [
                {
                    "id": "L1",
                    "name": "L1",
                    "locationFile": "foobar.pli",
                    "zSink": 0.0,
                    "zSource": 0.0,
                    "area": 1.0,
                    "discharge": 1.23,
                    "salinityDelta": 4.0,
                    "temperatureDelta": 5.0,
                }
            ]
        }
        m = ExtModel(**data)
        assert len(m.sourcesink) == 1
        assert np.isclose(m.sourcesink[0].discharge, 1.23)


#     def test_sourcesink_todict(self):

#         filepath = test_data_dir / "input/dflowfm_individual_files/FlowFM_bnd.ext"
#         m = ExtModel(filepath)
#         d = m.dict()
#         assert len(d["lateral"]) == 72
#         assert d["lateral"][0]["discharge"] == "realtime"
#         assert d["lateral"][1]["discharge"] == 1.23
#         assert d["lateral"][3]["discharge"]["forcing"][0]["constant"]["value"] == 1.23

#     def test_sourcesink_todict_fromdict(self):

#         data = {
#             "lateral": [
#                 {"discharge": 1.23},
#                 {"discharge": {"forcing": [{"constant": {"value": 1.23}}]}},
#             ]
#         }
#         m = ExtModel(**data)
#         d = m.dict()
#         assert len(d["lateral"])


# class TestValidateForcingData:
#     """
#     Class to test the different types of discharge forcings.
#     """

#     def test_dischargeforcings_fromfile(self):

#         filepath = test_data_dir / "input/dflowfm_individual_files/FlowFM_bnd.ext"
#         m = ExtModel(filepath)
#         assert len(m.lateral) == 72
#         assert m.lateral[0].discharge == RealTime.realtime
#         assert np.isclose(m.lateral[1].discharge, 1.23)
#         assert isinstance(m.lateral[3].discharge, ForcingModel)
#         assert isinstance(m.lateral[3].discharge.forcing[0], Constant)
#         assert m.lateral[3].discharge.forcing[0].name == "10637"

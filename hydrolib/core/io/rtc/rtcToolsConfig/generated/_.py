# generated by datamodel-codegen:
#   filename:  rtcToolsConfig.json
#   timestamp: 2022-09-27T13:34:13+00:00

from __future__ import annotations

from hydrolib.core.io.rtc.basemodel import RtcBaseModel

from . import RtcToolsConfigComplexType


class RtcToolsConfig(RtcBaseModel):
    __root__: RtcToolsConfigComplexType


RtcToolsConfig.update_forward_refs()

from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional

from pydantic.v1 import Field

from hydrolib.core.base.models import BaseModel, ModelSaveSettings, ParsableFileModel
from hydrolib.core.dflowfm.cmp.parser import CMPParser
from hydrolib.core.dflowfm.cmp.serializer import CMPSerializer


class HarmonicRecord(BaseModel):
    """Single cmp record, representing a harmonic component with amplitude and phase.

    Args:
        period (float): the period.
        amplitude (float): the amplitude.
        phase (float): the phase in degrees.

    Returns:
        HarmonicRecord: A new instance of the `HarmonicRecord` class.

    Raises:
        ValueError: If the period, amplitude or phase are not valid numbers.

    Examples:
        Create a `HarmonicRecord` object from a dictionary:
            ```python
            >>> data = {
            ...     "period": 0.0,
            ...     "amplitude": 1.0,
            ...     "phase": 2.0
            ... }
            >>> harmonic_record = HarmonicRecord(**data)
            >>> print(harmonic_record.period)
            0.0

            ```
    """

    period: float
    amplitude: float
    phase: float


class AstronomicName(Enum):
    A0 = "A0"
    SA = "SA"
    SSA = "SSA"
    MSM = "MSM"
    MM = "MM"
    MSF = "MSF"
    MS0 = "MS0"
    MF = "MF"
    KO0 = "KO0"
    MK0 = "MK0"
    SNU = "SNU"
    SN = "SN"
    MSTM = "MSTM"
    MFM = "MFM"
    TwoSM = "2SM"
    MSQM = "MSQM"
    MQM = "MQM"
    TwoSMSMN = "2SMN"
    TwoSMOK1 = "2OK1"
    TwoSMQ1 = "2Q1"
    NJ1 = "NJ1"
    SIGMA1 = "SIGMA1"
    MUK1 = "MUK1"
    NUJ1 = "NUJ1"
    Q1 = "Q1"
    NK1 = "NK1"
    RO1 = "RO1"
    NUK1 = "NUK1"
    O1 = "O1"
    TAU1 = "TAU1"
    MP1 = "MP1"
    M1B = "M1B"
    M1C = "M1C"
    M1A = "M1A"
    M1 = "M1"
    NO1 = "NO1"
    CHI1 = "CHI1"
    LP1 = "LP1"
    PI1 = "PI1"
    TK1 = "TK1"
    P1 = "P1"
    SK1 = "SK1"
    S1 = "S1"
    K1 = "K1"
    MO1 = "MO1"
    SP1 = "SP1"
    PSI1 = "PSI1"
    RP1 = "RP1"
    FI1 = "FI1"
    KP1 = "KP1"
    THETA1 = "THETA1"
    LABDAO1 = "LABDAO1"
    J1 = "J1"
    MQ1 = "MQ1"
    TwoSMPO1 = "2PO1"
    SO1 = "SO1"
    OO1 = "OO1"
    TwoSMKO1 = "2KO1"
    UPSILON1 = "UPSILON1"
    KQ1 = "KQ1"
    TwoSMMN2S2 = "2MN2S2"
    ThreeMKS2 = "3MKS2"
    TwoSMNS2 = "2NS2"
    ThreeMS2 = "3MS2"
    OQ2 = "OQ2"
    MNK2 = "MNK2"
    EPSILON2 = "EPSILON2"
    MNS2 = "MNS2"
    TwoSMML2S2 = "2ML2S2"
    MNUS2 = "MNUS2"
    MNK2S2 = "MNK2S2"
    TwoSMMS2K2 = "2MS2K2"
    O2 = "O2"
    NLK2 = "NLK2"
    TwoSMMK2 = "2MK2"
    TwoSMN2 = "2N2"
    MU2 = "MU2"
    TwoSMMS2 = "2MS2"
    SNK2 = "SNK2"
    NA2 = "NA2"
    N2 = "N2"
    KQ2 = "KQ2"
    NB2 = "NB2"
    NU2 = "NU2"
    ThreeMSN2 = "3MSN2"
    TwoSMKN2S2 = "2KN2S2"
    OP2 = "OP2"
    MSK2 = "MSK2"
    GAMMA2 = "GAMMA2"
    ALFA2 = "ALFA2"
    MPS2 = "MPS2"
    MA2 = "MA2"
    M2 = "M2"
    KO2 = "KO2"
    MSP2 = "MSP2"
    MB2 = "MB2"
    DELTA2 = "DELTA2"
    MKS2 = "MKS2"
    M2KS2 = "M2(KS)2"
    TwoSMSNMK2 = "2SN(MK)2"
    LABDA2 = "LABDA2"
    SNM2 = "SNM2"
    TwoSMMN2 = "2MN2"
    L2 = "L2"
    L2A = "L2A"
    L2B = "L2B"
    TwoSMSK2 = "2SK2"
    T2 = "T2"
    S2 = "S2"
    KP2 = "KP2"
    R2 = "R2"
    K2 = "K2"
    MSNU2 = "MSNU2"
    MSN2 = "MSN2"
    ZETA2 = "ZETA2"
    ETA2 = "ETA2"
    KJ2 = "KJ2"
    MKN2 = "MKN2"
    TwoSMKMSN2 = "2KM(SN)2"
    TwoSMSM2 = "2SM2"
    SKM2 = "SKM2"
    TwoSMMS2N2 = "2MS2N2"
    TwoSMSNU2 = "2SNU2"
    TwoSMSN2 = "2SN2"
    SKN2 = "SKN2"
    MQ3 = "MQ3"
    NO3 = "NO3"
    MO3 = "MO3"
    TwoSMMK3 = "2MK3"
    TwoSMMP3 = "2MP3"
    M3 = "M3"
    NK3 = "NK3"
    SO3 = "SO3"
    MP3 = "MP3"
    MK3 = "MK3"
    SP3 = "SP3"
    TwoSMMQ3 = "2MQ3"
    SK3 = "SK3"
    TwoSMSO3 = "2SO3"
    K3 = "K3"
    FourMS4 = "4MS4"
    TwoSMMNS4 = "2MNS4"
    ThreeMK4 = "3MK4"
    MNLK4 = "MNLK4"
    ThreeMS4 = "3MS4"
    MSNK4 = "MSNK4"
    MN4 = "MN4"
    MNU4 = "MNU4"
    TwoSMMLS4 = "2MLS4"
    TwoSMMSK4 = "2MSK4"
    M4 = "M4"
    TwoSMMKS4 = "2MKS4"
    SN4 = "SN4"
    TwoSMMN4 = "3MN4"
    TwoSMSMK4 = "2SMK4"
    MS4 = "MS4"
    MK4 = "MK4"
    TwoSMSNM4 = "2SNM4"
    TwoSMMSN4 = "2MSN4"
    SL4 = "SL4"
    S4 = "S4"
    SK4 = "SK4"
    TwoSMSMN4 = "2SMN4"
    ThreeSM4 = "3SM4"
    TwoSMSKM4 = "2SKM4"
    MNO5 = "MNO5"
    ThreeMK5 = "3MK5"
    ThreeMP5 = "3MP5"
    M5 = "M5"
    MNK5 = "MNK5"
    TwoSMMP5 = "2MP5"
    MSO5 = "MSO5"
    ThreeMO5 = "3MO5"
    MSK5 = "MSK5"
    ThreeKM5 = "3KM5"
    TwoSMMNS6 = "2(MN)S6"
    ThreeMNS6 = "3MNS6"
    FourMK6 = "4MK6"
    TwoSMNM6 = "2NM6"
    FourMS6 = "4MS6"
    TwoSMMSNK6 = "2MSNK6"
    TwoSMMN6 = "2MN6"
    TwoSMMNU6 = "2MNU6"
    ThreeMSK6 = "3MSK6"
    M6 = "M6"
    MSN6 = "MSN6"
    MNK6 = "MNK6"
    FourMN6 = "4MN6"
    MKNU6 = "MKNU6"
    TwoSMMSK6 = "2(MS)K6"
    TwoSMMS6 = "2MS6"
    TwoSMMK6 = "2MK6"
    TwoSMSN6 = "2SN6"
    ThreeMSN6 = "3MSN6"
    MKL6 = "MKL6"
    TwoSMSM6 = "2SM6"
    MSK6 = "MSK6"
    S6 = "S6"
    TwoSMMNO7 = "2MNO7"
    TwoSMNMK7 = "2NMK7"
    M7 = "M7"
    TwoSMMSO7 = "2MSO7"
    MSKO7 = "MSKO7"
    TwoSMMN8 = "2(MN)8"
    ThreeMN8 = "3MN8"
    ThreeMNKS8 = "3MNKS8"
    M8 = "M8"
    TwoSMMSN8 = "2MSN8"
    TwoSMMNK8 = "2MNK8"
    ThreeMS8 = "3MS8"
    ThreeMK8 = "3MK8"
    TwoSMSNM8 = "2SNM8"
    MSNK8 = "MSNK8"
    TwoSMMS8 = "2(MS)8"
    TwoSMMSK8 = "2MSK8"
    ThreeSM8 = "3SM8"
    TwoSMSMK8 = "2SMK8"
    S8 = "S8"
    TwoSMMNK9 = "2(MN)K9"
    ThreeMNK9 = "3MNK9"
    FourMK9 = "4MK9"
    ThreeMSK9 = "3MSK9"
    FourMN10 = "4MN10"
    M10 = "M10"
    ThreeMSN10 = "3MSN10"
    FourMS10 = "4MS10"
    TwoSMMSN10 = "2(MS)N10"
    TwoSMMNSK10 = "2MNSK10"
    ThreeM2S10 = "3M2S10"
    FourMSK11 = "4MSK11"
    M12 = "M12"
    FourMSN12 = "4MSN12"
    FourMS12 = "5MS12"
    ThreeMNKS12 = "3MNKS12"
    FourM2S12 = "4M2S12"


class AstronomicRecord(BaseModel):
    """Single cmp record, representing an astronomic component with amplitude and phase.

    Args:
        name (AstronomicName): the astronomic name.
        amplitude (float): the amplitude.
        phase (float): the phase in degrees.

    Returns:
        AstronomicRecord: A new instance of the `AstronomicRecord` class.

    Raises:
        ValueError: If the name, amplitude or phase are not valid numbers.

    Examples:
        Create an `AstronomicRecord` object from a dictionary:
            ```python
            >>> data = {
            ...     "name": "4MS10",
            ...     "amplitude": 1.0,
            ...     "phase": 2.0
            ... }
            >>> astronomic_record = AstronomicRecord(**data)
            >>> print(astronomic_record.name)
            4MS10

            ```
    """

    name: AstronomicName
    amplitude: float
    phase: float


class CMPSet(BaseModel):
    """A CMP set containing harmonics and astronomics.

    Args:
        harmonics (List[HarmonicRecord]): A list containing the harmonic components.
        astronomics (List[AstronomicRecord]): A list containing the astronomic components.

    Returns:
        CmpSet: A new instance of the `CmpSet` class.

    Raises:
        ValueError: If the harmonics or astronomics are not valid lists.

    Examples:
        Create a `CmpSet` object from a dictionary:
            ```python
            >>> data = {
            ...     "astronomics": [{"name": "4MS10", "amplitude": 1.0, "phase": 2.0}]
            ... }
            >>> cmp_set = CMPSet(**data)
            >>> print(cmp_set.astronomics)
            [AstronomicRecord(name='4MS10', amplitude=1.0, phase=2.0)]

            ```
    """

    harmonics: Optional[List[HarmonicRecord]] = Field(default_factory=list)
    astronomics: Optional[List[AstronomicRecord]] = Field(default_factory=list)


class CMPModel(ParsableFileModel):
    """Class representing a cmp (*.cmp) file.
    This class is used to parse and serialize cmp files, which contain
    information about various components such as harmonics and astronomics.

    Args:
        comments (List[str]): A list with the header comment of the cmp file.
        components (CMPSet): A CMPSet of astronomic and/or harmonic records.

    Returns:
        CmpModel: A new instance of the `CmpModel` class.

    Raises:
        ValueError: If the comments or components are not valid lists.

    Examples:
        Create a `CmpModel` object from a dictionary:
            ```python
            >>> data = {
            ...     "comments": ["# Example comment"],
            ...     "component": {
            ...         "harmonics": [{"period": 0.0, "amplitude": 1.0, "phase": 2.0}],
            ...         "astronomics": [{"name": "4MS10", "amplitude": 1.0, "phase": 2.0}]
            ...     }
            ... }
            >>> cmp_model = CMPModel(**data)
            >>> print(cmp_model.component.astronomics)
            [AstronomicRecord(name='4MS10', amplitude=1.0, phase=2.0)]

            ```

    See Also:
        CmpSet: Class representing the components of the cmp file.
        CmpSerializer: Class responsible for serializing cmp files.
        CmpParser: Class responsible for parsing cmp files.
    """

    comments: List[str] = Field(default_factory=list)
    component: CMPSet = Field(default_factory=list)
    quantities_name: Optional[List[str]] = None

    @classmethod
    def _ext(cls) -> str:
        return ".cmp"

    @classmethod
    def _filename(cls) -> str:
        return "components"

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, ModelSaveSettings], None]:
        return CMPSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return CMPParser.parse

    def get_units(self):
        """Return the units for each quantity in the timeseries.

        Returns:
            List[str]: A list of units for each quantity in the timeseries.

        Examples:
            Create a `CMPModel` object from a .cmp file:
                ```python
                >>> data = {
                ...     "comments": ["# Example comment"],
                ...     "component": {
                ...         "harmonics": [{"period": 0.0, "amplitude": 1.0, "phase": 2.0}],
                ...     },
                ...     "quantities_name": ["discharge"],
                ... }
                >>> model = CMPModel(**data)
                >>> print(model.get_units())
                ['m3/s']

                ```
        """
        if self.quantities_name is None:
            return None
        return CMPModel._get_quantity_unit(self.quantities_name)

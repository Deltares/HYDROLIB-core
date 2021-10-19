"""serializer.py defines the write method for the RainfallRunoffModel."""

import inspect
from pathlib import Path
from typing import Dict, Iterable, Optional


def _calculate_max_value_length(data: Iterable[Optional[Path]]) -> int:
    sizes = (len(str(v)) for v in data if v is not None)
    return max(sizes)


def _calculate_offset(value: str, max_len: int) -> str:
    return (max_len - len(value)) * " "


def _get_formatted_value(path_value: Optional[Path], max_len: int) -> str:
    value = str(path_value) if path_value is not None else ""
    return f"'{value}'{_calculate_offset(value, max_len)}"


def serialize(data: Dict) -> str:
    """Serialize the specified model.

    Args:
        model (RainfallRunoffModel): The model to serialize.

    Returns:
        str: The serialized RainfallRunoffModel in .fnm format.
    """
    if "filepath" in data:
        del data["filepath"]

    max_len = _calculate_max_value_length(data.values())
    values = (_get_formatted_value(v, max_len) for v in data.values())

    # fmt: off
    return inspect.cleandoc("""
        *
        * DELFT_3B Version 1.00
        * -----------------------------------------------------------------
        *
        * Last update : March 1995
        *
        * All input- and output file names (free format)
        *
        *   Namen Mappix files (*.DIR, *.TST, *.his) mogen NIET gewijzigd worden.
        *   Overige filenamen mogen wel gewijzigd worden.
        *
        *
        {}    *   1. Control file                                                         I
        {}    *   2. Knoop data                                                           I
        {}    *   3. Tak data                                                             I
        {}    *   4. Open water data                                                      I
        {}    *   5. Verhard gebied algemeen                                              I
        {}    *   6. Verhard gebied storage                                               I
        {}    *   7. Verhard gebied DWA                                                   I
        {}    *   8. Verhard gebied sewer pump capacity                                   I
        {}    *   9. Boundaries                                                           I
        {}    *  10. Pluvius                                                              I
        {}    *  11. Pluvius algemeen                                                     I
        {}    *  12. Kasklasse                                                            I
        {}    *  13. buifile                                                              I
        {}    *  14. verdampingsfile                                                      I
        {}    *  15. unpaved algemeen                                                     I
        {}    *  16. unpaved storage                                                      I
        {}    *  17. kasgebied initialisatie (SC)                                         I
        {}    *  18. kasgebied verbruiksdata (SC)                                         I
        {}    *  19. crop factors gewassen                                                I
        {}    *  20. tabel bergingscoef=f(ontw.diepte,grondsoort)                         I
        {}    *  21. Unpaved - alfa factor definities                                     I
        {}    *  22. Run messages                                                         O
        {}    *  23. Overzicht van schematisatie, algemene gegevens                       O
        {}    *  24. Output results verhard                                               O
        {}    *  25. Output results onverhard                                             O
        {}    *  26. Output results kas                                                   O
        {}    *  27. Output results open water                                            O
        {}    *  28. Output results kunstwerk                                             O
        {}    *  29. Output results boundaries                                            O
        {}    *  30. Output results Pluvius                                               O
        {}    *  31. Unpaved infiltratie definities                                       I
        {}    *  32. Debugfile                                                            O
        {}    *  33. Unpaved seepage                                                      I
        {}    *  34. Unpaved tabels initial gwl and Scurve                                I
        {}    *  35. Kassen general data                                                  I
        {}    *  36. Kassen roof storage                                                  I
        {}    *  37. Pluvius rioolinloop ASCII file                                       O
        {}    *  38. Invoerfile met variabele peilen op randknopen                        I
        {}    *  39. Invoerfile met zoutgegevens                                          I
        {}    *  40. Invoerfile met cropfactors open water                                I
        {}    *  41. Restart file input                                                   I
        {}    *  42. Restart file output                                                  O
        {}    *  43. Binary file input                                                    I
        {}    *  44. Sacramento input I        
        {}    *  45. Uitvoer ASCII file met debieten van/naar randknopen                  O
        {}    *  46. Uitvoer ASCII file met zoutconcentratie op rand                      O
        {}    *  47. Zout uitvoer in ASCII file                                           O
        {}    *  48. Greenhouse silo definitions                                          I
        {}    *  49. Open water general data                                              I
        {}    *  50. Open water seepage definitions                                       I
        {}    *  51. Open water tables target levels                                      I
        {}    *  52. General structure data                                               I
        {}    *  53. Structure definitions                                                I
        {}    *  54. Controller definitions                                               I
        {}    *  55. Tabellen structures                                                  I
        {}    *  56. Boundary data                                                        I
        {}    *  57. Boundary tables                                                      I
        {}    *  58.                                                                      I
        {}    *  59. Wwtp data                                                            I
        {}    *  60. Wwtp tabellen                                                        I
        {}    *  61. Industry general data                                                I
        {}    *  62. Mappix output file detail berging riool verhard gebied per tijdstap  O
        {}    *  63. Mappix output file detail debiet verhard gebied        per tijdstap  O
        {}    *  64. Mappix output file detail debiet onverhard gebied      per tijdstap  O
        {}    *  65. Mappix output file detail grondwaterstand              per tijdstap  O
        {}    *  66. Mappix output file detail bergingsgraad kasbassins     per tijdstap  O
        {}    *  67. Mappix output file detail uitslag kasbassins           per tijdstap  O
        {}    *  68. Mappix output file detail open water peil              per tijdstap  O
        {}    *  69  Mappix output file detail overschrijdingsduur ref.peil per tijdstap  O
        {}    *  70. Mappix output file detail debiet over kunstwerk        per tijdstap  O
        {}    *  71. Mappix output file detail debiet naar rand             per tijdstap  O
        {}    *  72. Mappix output file max.berging riool Pluvius           per tijdstap  O
        {}    *  73. Mappix output file max.debiet Pluvius                  per tijdstap  O
        {}    *  74. Mappix output file detail balans                       per tijdstap  O
        {}    *  75. Mappix output file detail balans cumulatief            per tijdstap  O
        {}    *  76. Mappix output file detail zoutconcentraties            per tijdstap  O
        {}    *  77. Industry tabellen                                                    I
        {}    *  78. Maalstop                                                             I
        {}    *  79. Temperature time series                                              I
        {}    *  80. Runoff time series              
        {}    *  81. Totalen/lozingen op randknopen                                       O
        {}    *  82. Language file                                                        I
        {}    *  83. OW-volume                                                            O
        {}    *  84. OW_peilen                                                            O
        {}    *  85. Balans file                                                          O
        {}    *  86. 3B-arealen in HIS file                                               O
        {}    *  87. 3B-structure data in HIS file                                        O
        {}    *  88. RR Runoff his file              
        {}    *  89. Sacramento HIS file              
        {}    *  90. rwzi HIS file                                                        O
        {}    *  91. Industry HIS file                                                    O
        {}    *  92. CTRL.INI                                                             I
        {}    *  93. CAPSIM input file                                                    I
        {}    *  94. CAPSIM input file                                                    I
        {}    *  95. CAPSIM message file                                                  O
        {}    *  96. CAPSIM debug file                                                    O
        {}    *  97. Restart file na 1 uur                                                O
        {}    *  98. Restart file na 12 uur                                               O
        {}    *  99. Ready                                                                O
        {}    * 100. NWRW detailed areas                                                  O
        {}    * 101. Link flows                                                           O
        {}    * 102. Modflow-RR                                                           O
        {}    * 103. RR-Modflow                                                           O
        {}    * 104. RR-balance for WLM              
        {}    * 105. Sacramento ASCII output              
        {}    * 106. Additional NWRW input file with DWA table                            I
        {}    * 107. RR balans
        {}    * 108. Kasklasse, new format                                                I
        {}    * 109. KasInit, new format                                                  I
        {}    * 110. KasGebr, new format                                                  I
        {}    * 111. CropFact, new format                                                 I
        {}    * 112. CropOW, new format                                                   I
        {}    * 113. Soildata, new format                                                 I
        {}    * 114. DioConfig Ini file
        {}    * 115. Buifile voor continue berekening Reeksen
        {}    * 116. NWRW output
        {}    * 117. RR Routing link definitions                                          I
        {}    * 118. Cel input file
        {}    * 119. Cel output file
        {}    * 120. RR Log file for Simulate
        {}    * 121. coupling WQ salt RTC
        {}    * 122. RR Boundary conditions file for SOBEK3
        {}    * 123. Optional RR ASCII restart (test) for OpenDA
        {}    * 124. Optional LGSI cachefile
        {}    * 125. Optional meteo NetCdf timeseries inputfile rainfall
        {}    * 126. Optional meteo NetCdf timeseries inputfile evaporation
        {}    * 127. Optional meteo NetCdf timeseries inputfile temperature (only for RR-HBV)
        """.format(*values))
    # fmt: on


def write(path: Path, data: Dict) -> None:
    """Write the specified model to the specified path.

    If the parent of the path does not exist, it will be created.

    Args:
        model (RainfallRunoffModel): The model to write to file
        path (Path): The file path to write to.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(serialize(data))

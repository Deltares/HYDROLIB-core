import inspect
import shutil
from pathlib import Path
from typing import Callable, Optional

import pytest

from hydrolib.core.base.file_manager import ResolveRelativeMode, file_load_context
from hydrolib.core.base.models import DiskOnlyFileModel, ModelSaveSettings
from hydrolib.core.dimr.models import DIMR
from hydrolib.core.rr.models import (
    RainfallRunoffModel,
    _mappix_balance_name,
    _mappix_cumulative_balance_name,
    _mappix_exceedance_time_reference_levels_name,
    _mappix_flow_rates_over_structures_name,
    _mappix_flow_rates_to_edge_name,
    _mappix_green_house_bassins_results_name,
    _mappix_green_house_bassins_storage_name,
    _mappix_ground_water_levels_name,
    _mappix_open_water_details_name,
    _mappix_paved_area_flow_rates_name,
    _mappix_paved_area_sewage_storage_name,
    _mappix_pluvius_max_flow_rates_name,
    _mappix_pluvius_max_sewage_storage_name,
    _mappix_salt_concentrations_name,
    _mappix_unpaved_area_flow_rates_name,
)
from hydrolib.core.rr.parser import parse
from hydrolib.core.rr.serializer import serialize
from tests.utils import assert_file_is_same_binary, test_input_dir, test_output_dir

rr_directory = test_input_dir / "e02" / "c11_korte-woerden-1d" / "dimr_model" / "rr"
rr_file_name = Path("Sobek_3b.fnm")


class TestRainFallRunoffModel:
    def test_load_from_file(self):
        path = rr_directory / rr_file_name

        model = RainfallRunoffModel(filepath=path)

        assert model.node_data is not None
        assert model.link_data is not None

    def test_property_keys_returns_correct_list(self):
        result = list(RainfallRunoffModel.property_keys())

        assert len(result) == 127
        assert result[0] == "control_file"
        assert result[1] == "node_data"
        assert result[2] == "link_data"
        assert result[-1] == "meteo_input_file_temperature"
        assert result[-2] == "meteo_input_file_evaporation"
        assert result[-3] == "meteo_input_file_rainfall"

    @pytest.mark.parametrize(
        "name,get_prop",
        [
            (
                (_mappix_paved_area_sewage_storage_name),
                (lambda m: m.mappix_paved_area_sewage_storage.filepath),
            ),
            (
                (_mappix_paved_area_flow_rates_name),
                (lambda m: m.mappix_paved_area_flow_rates.filepath),
            ),
            (
                (_mappix_unpaved_area_flow_rates_name),
                (lambda m: m.mappix_unpaved_area_flow_rates.filepath),
            ),
            (
                (_mappix_ground_water_levels_name),
                (lambda m: m.mappix_ground_water_levels.filepath),
            ),
            (
                (_mappix_green_house_bassins_storage_name),
                (lambda m: m.mappix_green_house_bassins_storage.filepath),
            ),
            (
                (_mappix_green_house_bassins_results_name),
                (lambda m: m.mappix_green_house_bassins_results.filepath),
            ),
            (
                (_mappix_open_water_details_name),
                (lambda m: m.mappix_open_water_details.filepath),
            ),
            (
                (_mappix_exceedance_time_reference_levels_name),
                (lambda m: m.mappix_exceedance_time_reference_levels.filepath),
            ),
            (
                (_mappix_flow_rates_over_structures_name),
                (lambda m: m.mappix_flow_rates_over_structures.filepath),
            ),
            (
                (_mappix_flow_rates_to_edge_name),
                (lambda m: m.mappix_flow_rates_to_edge.filepath),
            ),
            (
                (_mappix_pluvius_max_sewage_storage_name),
                (lambda m: m.mappix_pluvius_max_sewage_storage.filepath),
            ),
            (
                (_mappix_pluvius_max_flow_rates_name),
                (lambda m: m.mappix_pluvius_max_flow_rates.filepath),
            ),
            (
                (_mappix_balance_name),
                (lambda m: m.mappix_balance.filepath),
            ),
            (
                (_mappix_cumulative_balance_name),
                (lambda m: m.mappix_cumulative_balance.filepath),
            ),
            (
                (_mappix_salt_concentrations_name),
                (lambda m: m.mappix_salt_concentrations.filepath),
            ),
        ],
    )
    def test_mappix_property_returns_path_equal_to_name(
        self,
        name: str,
        get_prop: Callable[[RainfallRunoffModel], Path],
    ):
        model = RainfallRunoffModel()
        assert str(get_prop(model)) == name


def assert_same_fnm_model(
    input_model: RainfallRunoffModel, reference_model: RainfallRunoffModel
) -> None:
    input_values = input_model.dict()
    reference_values = reference_model.dict()

    assert len(input_values) == len(reference_values)

    for key, value in input_values.items():
        assert key in reference_values
        reference_value = reference_values[key]

        if isinstance(reference_value, DiskOnlyFileModel):
            assert isinstance(value, DiskOnlyFileModel)
            assert value.filepath == reference_value.filepath
        else:
            assert value == reference_value


def test_serialize_parse_should_return_same_result():
    model = RainfallRunoffModel()

    # Scramble some values to ensure we're not just getting the default.
    model.open_water_data.filepath = Path("somewhere_else")
    model.green_house_general.filepath = Path("greenhouse.general")
    model.restart_file_input.filepath = Path("aa_res.res")
    model.meteo_input_file_rainfall.filepath = Path("some_path.ini")

    serialized_model = serialize(model.dict(), ModelSaveSettings())
    deserialized_model = parse(
        RainfallRunoffModel.property_keys(), serialized_model.splitlines()
    )
    result = RainfallRunoffModel.parse_obj(deserialized_model)

    assert_same_fnm_model(result, model)


def test_parse_serialize_should_return_same_result():
    # fmt: off
    serialized_model = inspect.cleandoc("""
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
    'delft_3b.ini'             *   1. Control file                                                         I
    '___somewhere/else'        *   2. Knoop data                                                           I
    '3b_link.tp'               *   3. Tak data                                                             I
    '3brunoff.tp'              *   4. Open water data                                                      I
    'paved.3b'                 *   5. Verhard gebied algemeen                                              I
    'paved.sto'                *   6. Verhard gebied storage                                               I
    'paved.dwa'                *   7. Verhard gebied DWA                                                   I
    'paved.tbl'                *   8. Verhard gebied sewer pump capacity                                   I
    'pluvius.dwa'              *   9. Boundaries                                                           I
    'pluvius.3b'               *  10. Pluvius                                                              I
    'pluvius.alg'              *  11. Pluvius algemeen                                                     I
    'kasklass'                 *  12. Kasklasse                                                            I
    'bui_file.bui'             *  13. buifile                                                              I
    'default.evp'              *  14. verdampingsfile                                                      I
    'unpaved.3b'               *  15. unpaved algemeen                                                     I
    'unpaved.sto'              *  16. unpaved storage                                                      I
    'kasinit'                  *  17. kasgebied initialisatie (SC)                                         I
    'kasgebr'                  *  18. kasgebied verbruiksdata (SC)                                         I
    'cropfact'                 *  19. crop factors gewassen                                                I
    'bergcoef'                 *  20. tabel bergingscoef=f(ontw.diepte,grondsoort)                         I
    'unpaved.alf'              *  21. Unpaved - alfa factor definities                                     I
    'sobek_3b.log'             *  22. Run messages                                                         O
    '3b_gener.out'             *  23. Overzicht van schematisatie, algemene gegevens                       O
    'paved.out'                *  24. Output results verhard                                               O
    'unpaved.out'              *  25. Output results onverhard                                             O
    'grnhous.out'              *  26. Output results kas                                                   O
    'openwate.out'             *  27. Output results open water                                            O
    'struct3b.out'             *  28. Output results kunstwerk                                             O
    'bound3b.out'              *  29. Output results boundaries                                            O
    'pluvius.out'              *  30. Output results Pluvius                                               O
    'unpaved.inf'              *  31. Unpaved infiltratie definities                                       I
    'sobek_3b.dbg'             *  32. Debugfile                                                            O
    'unpaved.sep'              *  33. Unpaved seepage                                                      I
    'unpaved.tbl'              *  34. Unpaved tabels initial gwl and Scurve                                I
    'greenhouse.general'       *  35. Kassen general data                                                  I
    'greenhse.rf'              *  36. Kassen roof storage                                                  I
    'runoff.out'               *  37. Pluvius rioolinloop ASCII file                                       O
    'sbk_rtc.his'              *  38. Invoerfile met variabele peilen op randknopen                        I
    'salt.3b'                  *  39. Invoerfile met zoutgegevens                                          I
    'crop_ow.prn'              *  40. Invoerfile met cropfactors open water                                I
    '___res.res'               *  41. Restart file input                                                   I
    'RSRR_OUT'                 *  42. Restart file output                                                  O
    '3b_input.bin'             *  43. Binary file input                                                    I
    'sacrmnto.3b'              *  44. Sacramento input I        
    'aanvoer.abr'              *  45. Uitvoer ASCII file met debieten van/naar randknopen                  O
    'saltbnd.out'              *  46. Uitvoer ASCII file met zoutconcentratie op rand                      O
    'salt.out'                 *  47. Zout uitvoer in ASCII file                                           O
    'greenhse.sil'             *  48. Greenhouse silo definitions                                          I
    'openwate.3b'              *  49. Open water general data                                              I
    'openwate.sep'             *  50. Open water seepage definitions                                       I
    'openwate.tbl'             *  51. Open water tables target levels                                      I
    'struct3b.dat'             *  52. General structure data                                               I
    'struct3b.def'             *  53. Structure definitions                                                I
    'contr3b.def'              *  54. Controller definitions                                               I
    'struct3b.tbl'             *  55. Tabellen structures                                                  I
    'bound3b.3b'               *  56. Boundary data                                                        I
    'bound3b.tbl'              *  57. Boundary tables                                                      I
    'sbk_loc.rtc'              *  58.                                                                      I
    'wwtp.3b'                  *  59. Wwtp data                                                            I
    'wwtp.tbl'                 *  60. Wwtp tabellen                                                        I
    'industry.3b'              *  61. Industry general data                                                I
    'pvstordt.his'             *  62. Mappix output file detail berging riool verhard gebied per tijdstap  O
    'pvflowdt.his'             *  63. Mappix output file detail debiet verhard gebied        per tijdstap  O
    'upflowdt.his'             *  64. Mappix output file detail debiet onverhard gebied      per tijdstap  O
    'upgwlvdt.his'             *  65. Mappix output file detail grondwaterstand              per tijdstap  O
    'grnstrdt.his'             *  66. Mappix output file detail bergingsgraad kasbassins     per tijdstap  O
    'grnflodt.his'             *  67. Mappix output file detail uitslag kasbassins           per tijdstap  O
    'ow_lvldt.his'             *  68. Mappix output file detail open water peil              per tijdstap  O
    'ow_excdt.his'             *  69  Mappix output file detail overschrijdingsduur ref.peil per tijdstap  O
    'strflodt.his'             *  70. Mappix output file detail debiet over kunstwerk        per tijdstap  O
    'bndflodt.his'             *  71. Mappix output file detail debiet naar rand             per tijdstap  O
    'plvstrdt.his'             *  72. Mappix output file max.berging riool Pluvius           per tijdstap  O
    'plvflodt.his'             *  73. Mappix output file max.debiet Pluvius                  per tijdstap  O
    'balansdt.his'             *  74. Mappix output file detail balans                       per tijdstap  O
    'cumbaldt.his'             *  75. Mappix output file detail balans cumulatief            per tijdstap  O
    'saltdt.his'               *  76. Mappix output file detail zoutconcentraties            per tijdstap  O
    'industry.tbl'             *  77. Industry tabellen                                                    I
    'rtc_3b.his'               *  78. Maalstop                                                             I
    'default.tmp'              *  79. Temperature time series                                              I
    'rnff.#'                   *  80. Runoff time series              
    'bndfltot.his'             *  81. Totalen/lozingen op randknopen                                       O
    'sobek_3b.lng'             *  82. Language file                                                        I
    'ow_vol.his'               *  83. OW-volume                                                            O
    'ow_level.his'             *  84. OW_peilen                                                            O
    '3b_bal.out'               *  85. Balans file                                                          O
    '3bareas.his'              *  86. 3B-arealen in HIS file                                               O
    '3bstrdim.his'             *  87. 3B-structure data in HIS file                                        O
    'rrrunoff.his'             *  88. RR Runoff his file              
    'sacrmnto.his'             *  89. Sacramento HIS file              
    'wwtpdt.his'               *  90. rwzi HIS file                                                        O
    'industdt.his'             *  91. Industry HIS file                                                    O
    'ctrl.ini'                 *  92. CTRL.INI                                                             I
    'root_sim.inp'             *  93. CAPSIM input file                                                    I
    'unsa_sim.inp'             *  94. CAPSIM input file                                                    I
    'capsim.msg'               *  95. CAPSIM message file                                                  O
    'capsim.dbg'               *  96. CAPSIM debug file                                                    O
    'restart1.out'             *  97. Restart file na 1 uur                                                O
    'restart12.out'            *  98. Restart file na 12 uur                                               O
    'RR-ready'                 *  99. Ready                                                                O
    'NwrwArea.His'             * 100. NWRW detailed areas                                                  O
    '3blinks.his'              * 101. Link flows                                                           O
    'modflow_rr.His'           * 102. Modflow-RR                                                           O
    'rr_modflow.His'           * 103. RR-Modflow                                                           O
    'rr_wlmbal.His'            * 104. RR-balance for WLM              
    'sacrmnto.out'             * 105. Sacramento ASCII output              
    'pluvius.tbl'              * 106. Additional NWRW input file with DWA table                            I
    'rrbalans.his'             * 107. RR balans
    'KasKlasData.dat'          * 108. Kasklasse, new format                                                I
    'KasInitData.dat'          * 109. KasInit, new format                                                  I
    'KasGebrData.dat'          * 110. KasGebr, new format                                                  I
    'CropData.dat'             * 111. CropFact, new format                                                 I
    'CropOWData.dat'           * 112. CropOW, new format                                                   I
    'SoilData.dat'             * 113. Soildata, new format                                                 I
    'dioconfig.ini'            * 114. DioConfig Ini file
    'NWRWCONT.#'               * 115. Buifile voor continue berekening Reeksen
    'NwrwSys.His'              * 116. NWRW output
    '3b_rout.3b'               * 117. RR Routing link definitions                                          I
    '3b_cel.3b'                * 118. Cel input file
    '3b_cel.his'               * 119. Cel output file
    'sobek3b_progress.txt'     * 120. RR Log file for Simulate
    'wqrtc.his'                * 121. coupling WQ salt RTC
    'BoundaryConditions.bc'    * 122. RR Boundary conditions file for SOBEK3
    ''                         * 123. Optional RR ASCII restart (test) for OpenDA
    ''                         * 124. Optional LGSI cachefile
    'path.ini'                 * 125. Optional meteo NetCdf timeseries inputfile rainfall
    ''                         * 126. Optional meteo NetCdf timeseries inputfile evaporation
    ''                         * 127. Optional meteo NetCdf timeseries inputfile temperature (only for RR-HBV)
    """)
    # fmt: on

    deserialized_model = parse(
        RainfallRunoffModel.property_keys(), serialized_model.splitlines()
    )
    reserialized_model = serialize(deserialized_model, ModelSaveSettings())

    assert reserialized_model == serialized_model


def test_fnm_save_as_with_recurse_correctly_copies_subfiles():
    source_path_parent = rr_directory
    filepath = rr_file_name

    name = test_fnm_save_as_with_recurse_correctly_copies_subfiles.__name__
    target_path = test_output_dir / name

    if target_path.exists() and target_path.is_dir():
        try:
            shutil.rmtree(target_path)
        except PermissionError:
            pass
    target_path.mkdir(exist_ok=True)

    with file_load_context() as context:
        context.push_new_parent(source_path_parent, ResolveRelativeMode.ToParent)
        model = RainfallRunoffModel(filepath=filepath)

        model.save(filepath=target_path / filepath, recurse=True)

    def assert_correct_subfile(path: Optional[Path]) -> None:
        assert_file_is_same_binary(target_path, path, source_path_parent)

    assert (target_path / filepath).exists()

    disk_only_file_models = (
        v for v in dict(model).values() if isinstance(v, DiskOnlyFileModel)
    )
    for v in disk_only_file_models:
        assert_correct_subfile(v.filepath)


def test_fnm_save_without_recurse_only_copies_fnm_file():
    source_path_parent = rr_directory
    filepath = rr_file_name

    name = test_fnm_save_as_with_recurse_correctly_copies_subfiles.__name__
    target_path = test_output_dir / name

    if target_path.exists() and target_path.is_dir():
        try:
            shutil.rmtree(target_path)
        except PermissionError:
            pass

    target_path.mkdir(exist_ok=True)

    with file_load_context() as context:
        context.push_new_parent(source_path_parent, ResolveRelativeMode.ToParent)
        model = RainfallRunoffModel(filepath=filepath)

        model.save(filepath=target_path / filepath, recurse=False)

    assert (target_path / filepath).exists()

    disk_only_files = (
        v.filepath
        for v in dict(model).values()
        if isinstance(v, DiskOnlyFileModel) and v.filepath is not None
    )
    for v in disk_only_files:
        assert not (target_path / v).exists()


def test_dimr_model_save_with_recurse_correctly_copies_rr_sub_files():
    source_path_parent = test_input_dir / "e02" / "c11_korte-woerden-1d" / "dimr_model"
    filepath = Path("dimr_config.xml")

    name = test_dimr_model_save_with_recurse_correctly_copies_rr_sub_files.__name__
    target_path = test_output_dir / name

    if target_path.exists() and target_path.is_dir():
        try:
            shutil.rmtree(target_path)
        except PermissionError:
            pass
    target_path.mkdir(exist_ok=True)

    with file_load_context() as context:
        context.push_new_parent(source_path_parent, ResolveRelativeMode.ToParent)
        model = DIMR(filepath=filepath)

        model.save(filepath=target_path / filepath, recurse=True)

    rr_model = next(
        (m.model for m in model.component if isinstance(m.model, RainfallRunoffModel)),
        None,
    )
    assert rr_model is not None

    def assert_correct_subfile(path: Optional[Path]) -> None:
        assert_file_is_same_binary(target_path, path, source_path_parent)

    assert rr_model.filepath is not None
    assert (target_path / rr_model.filepath).exists()

    disk_only_file_models = (
        v for v in dict(rr_model).values() if isinstance(v, DiskOnlyFileModel)
    )
    for v in disk_only_file_models:
        assert_correct_subfile(v.filepath)

"""models.py defines the RainfallRunoffModel and supporting structures."""

from pathlib import Path
from typing import Callable, Dict, Iterable, Literal, Optional

from pydantic import Field
from pydantic.types import FilePath

from hydrolib.core.basemodel import SerializableFileModel

from .meteo.models import BuiModel
from .parser import read
from .serializer import write
from .topology.models import LinkFile, NodeFile


class RainfallRunoffModel(SerializableFileModel):
    """The RainfallRunoffModel contains all paths and sub-models related to the
    Rainfall Runoff model.
    """

    # Note that order is defined by the .fnm file type and is used for parsing the data.
    control_file: Optional[Path] = Path("delft_3b.ini")
    node_data: Optional[NodeFile] = Field(None)
    link_data: Optional[LinkFile] = Field(None)
    open_water_data: Optional[Path] = Path("3brunoff.tp")
    paved_area_general: Optional[Path] = Path("paved.3b")
    paved_area_storage: Optional[Path] = Path("paved.sto")
    paved_area_dwa: Optional[Path] = Path("paved.dwa")
    paved_area_sewer_pump_capacity: Optional[Path] = Path("paved.tbl")
    boundaries: Optional[Path] = Path("pluvius.dwa")
    pluvius: Optional[Path] = Path("pluvius.3b")
    pluvius_general: Optional[Path] = Path("pluvius.alg")
    kasklasse: Optional[Path] = Path("kasklass")
    bui_file: Optional[BuiModel] = Field(None)
    verdampings_file: Optional[Path] = Path("default.evp")
    unpaved_area_general: Optional[Path] = Path("unpaved.3b")
    unpaved_area_storage: Optional[Path] = Path("unpaved.sto")
    green_house_area_initialisation: Optional[Path] = Path("kasinit")
    green_house_area_usage_data: Optional[Path] = Path("kasgebr")
    crop_factors: Optional[Path] = Path("cropfact")
    table_bergingscoef: Optional[Path] = Path("bergcoef")
    unpaved_alpha_factor_definitions: Optional[Path] = Path("unpaved.alf")
    run_log_file: Optional[Path] = Path("sobek_3b.log")
    schema_overview: Optional[Path] = Path("3b_gener.out")
    output_results_paved_area: Optional[Path] = Path("paved.out")
    output_results_unpaved_area: Optional[Path] = Path("unpaved.out")
    output_results_green_houses: Optional[Path] = Path("grnhous.out")
    output_results_open_water: Optional[Path] = Path("openwate.out")
    output_results_structures: Optional[Path] = Path("struct3b.out")
    output_results_boundaries: Optional[Path] = Path("bound3b.out")
    output_results_pluvius: Optional[Path] = Path("pluvius.out")
    infiltration_definitions_unpaved: Optional[Path] = Path("unpaved.inf")
    run_debug_file: Optional[Path] = Path("sobek_3b.dbg")
    unpaved_seepage: Optional[Path] = Path("unpaved.sep")
    unpaved_initial_values_tables: Optional[Path] = Path("unpaved.tbl")
    green_house_general: Optional[Path] = Path("greenhse.3b")
    green_house_roof_storage: Optional[Path] = Path("greenhse.rf")
    pluvius_sewage_entry: Optional[Path] = Path("runoff.out")
    input_variable_gauges_on_edge_nodes: Optional[Path] = Path("sbk_rtc.his")
    input_salt_data: Optional[Path] = Path("salt.3b")
    input_crop_factors_open_water: Optional[Path] = Path("crop_ow.prn")
    restart_file_input: Optional[Path] = Path("RSRR_IN")
    restart_file_output: Optional[Path] = Path("RSRR_OUT")
    binary_file_input: Optional[Path] = Path("3b_input.bin")
    sacramento_input: Optional[Path] = Path("sacrmnto.3b")
    output_flow_rates_edge_nodes: Optional[Path] = Path("aanvoer.abr")
    output_salt_concentration_edge: Optional[Path] = Path("saltbnd.out")
    output_salt_exportation: Optional[Path] = Path("salt.out")
    greenhouse_silo_definitions: Optional[Path] = Path("greenhse.sil")
    open_water_general: Optional[Path] = Path("openwate.3b")
    open_water_seepage_definitions: Optional[Path] = Path("openwate.sep")
    open_water_tables_target_levels: Optional[Path] = Path("openwate.tbl")
    structure_general: Optional[Path] = Path("struct3b.dat")
    structure_definitions: Optional[Path] = Path("struct3b.def")
    controller_definitions: Optional[Path] = Path("contr3b.def")
    structure_tables: Optional[Path] = Path("struct3b.tbl")
    boundary_data: Optional[Path] = Path("bound3b.3b")
    boundary_tables: Optional[Path] = Path("bound3b.tbl")
    sobek_location_rtc: Optional[Path] = Path("sbk_loc.rtc")  # TODO 58.
    wwtp_data: Optional[Path] = Path("wwtp.3b")
    wwtp_tables: Optional[Path] = Path("wwtp.tbl")
    industry_general: Optional[Path] = Path("industry.3b")

    # Mappix paths should not change and always hold the defined values.
    # As such these values have been implemented as Literal values with
    # corresponding path properties, to expose them as paths.
    mappix_paved_area_sewage_storage_name: Literal["pvstordt.his"] = "pvstordt.his"
    mappix_paved_area_flow_rates_name: Literal["pvflowdt.his"] = "pvflowdt.his"
    mappix_unpaved_area_flow_rates_name: Literal["upflowdt.his"] = "upflowdt.his"
    mappix_ground_water_levels_name: Literal["upgwlvdt.his"] = "upgwlvdt.his"
    mappix_green_house_bassins_storage_name: Literal["grnstrdt.his"] = "grnstrdt.his"
    mappix_green_house_bassins_results_name: Literal["grnflodt.his"] = "grnflodt.his"
    mappix_open_water_details_name: Literal["ow_lvldt.his"] = "ow_lvldt.his"
    mappix_exceedance_time_reference_levels_name: Literal[
        "ow_excdt.his"
    ] = "ow_excdt.his"
    mappix_flow_rates_over_structures_name: Literal["strflodt.his"] = "strflodt.his"
    mappix_flow_rates_to_edge_name: Literal["bndflodt.his"] = "bndflodt.his"
    mappix_pluvius_max_sewage_storage_name: Literal["plvstrdt.his"] = "plvstrdt.his"
    mappix_pluvius_max_flow_rates_name: Literal["plvflodt.his"] = "plvflodt.his"
    mappix_balance_name: Literal["balansdt.his"] = "balansdt.his"
    mappix_cumulative_balance_name: Literal["cumbaldt.his"] = "cumbaldt.his"
    mappix_salt_concentrations_name: Literal["saltdt.his"] = "saltdt.his"

    @property
    def mappix_paved_area_sewage_storage(self) -> Path:
        return Path(self.mappix_paved_area_sewage_storage_name)

    @property
    def mappix_paved_area_flow_rates(self) -> Path:
        return Path(self.mappix_paved_area_flow_rates_name)

    @property
    def mappix_unpaved_area_flow_rates(self) -> Path:
        return Path(self.mappix_unpaved_area_flow_rates_name)

    @property
    def mappix_ground_water_levels(self) -> Path:
        return Path(self.mappix_ground_water_levels_name)

    @property
    def mappix_green_house_bassins_storage(self) -> Path:
        return Path(self.mappix_green_house_bassins_storage_name)

    @property
    def mappix_green_house_bassins_results(self) -> Path:
        return Path(self.mappix_green_house_bassins_results_name)

    @property
    def mappix_open_water_details(self) -> Path:
        return Path(self.mappix_open_water_details_name)

    @property
    def mappix_exceedance_time_reference_levels(self) -> Path:
        return Path(self.mappix_exceedance_time_reference_levels_name)

    @property
    def mappix_flow_rates_over_structures(self) -> Path:
        return Path(self.mappix_flow_rates_over_structures_name)

    @property
    def mappix_flow_rates_to_edge(self) -> Path:
        return Path(self.mappix_flow_rates_to_edge_name)

    @property
    def mappix_pluvius_max_sewage_storage(self) -> Path:
        return Path(self.mappix_pluvius_max_sewage_storage_name)

    @property
    def mappix_pluvius_max_flow_rates(self) -> Path:
        return Path(self.mappix_pluvius_max_flow_rates_name)

    @property
    def mappix_balance(self) -> Path:
        return Path(self.mappix_balance_name)

    @property
    def mappix_cumulative_balance(self) -> Path:
        return Path(self.mappix_cumulative_balance_name)

    @property
    def mappix_salt_concentrations(self) -> Path:
        return Path(self.mappix_salt_concentrations_name)

    industry_tables: Optional[Path] = Path("industry.tbl")
    maalstop: Optional[Path] = Path("rtc_3b.his")
    time_series_temperature: Optional[Path] = Path("default.tmp")
    time_series_runoff: Optional[Path] = Path("rnff.#")
    discharges_totals_at_edge_nodes: Optional[Path] = Path("bndfltot.his")
    language_file: Optional[Path] = Path("sobek_3b.lng")
    ow_volume: Optional[Path] = Path("ow_vol.his")
    ow_levels: Optional[Path] = Path("ow_level.his")
    balance_file: Optional[Path] = Path("3b_bal.out")
    his_3B_area_length: Optional[Path] = Path("3bareas.his")
    his_3B_structure_data: Optional[Path] = Path("3bstrdim.his")
    his_rr_runoff: Optional[Path] = Path("rrrunoff.his")
    his_sacramento: Optional[Path] = Path("sacrmnto.his")
    his_rwzi: Optional[Path] = Path("wwtpdt.his")
    his_industry: Optional[Path] = Path("industdt.his")
    ctrl_ini: Optional[Path] = Path("ctrl.ini")
    root_capsim_input_file: Optional[Path] = Path("root_sim.inp")
    unsa_capsim_input_file: Optional[Path] = Path("unsa_sim.inp")
    capsim_message_file: Optional[Path] = Path("capsim.msg")
    capsim_debug_file: Optional[Path] = Path("capsim.dbg")
    restart_1_hour: Optional[Path] = Path("restart1.out")
    restart_12_hours: Optional[Path] = Path("restart12.out")
    rr_ready: Optional[Path] = Path("RR-ready")
    nwrw_areas: Optional[Path] = Path("NwrwArea.His")
    link_flows: Optional[Path] = Path("3blinks.his")
    modflow_rr: Optional[Path] = Path("modflow_rr.His")
    rr_modflow: Optional[Path] = Path("rr_modflow.His")
    rr_wlm_balance: Optional[Path] = Path("rr_wlmbal.His")
    sacramento_ascii_output: Optional[Path] = Path("sacrmnto.out")
    nwrw_input_dwa_table: Optional[Path] = Path("pluvius.tbl")
    rr_balance: Optional[Path] = Path("rrbalans.his")
    green_house_classes: Optional[Path] = Path("KasKlasData.dat")
    green_house_init: Optional[Path] = Path("KasInitData.dat")
    green_house_usage: Optional[Path] = Path("KasGebrData.dat")
    crop_factor: Optional[Path] = Path("CropData.dat")
    crop_ow: Optional[Path] = Path("CropOWData.dat")
    soil_data: Optional[Path] = Path("SoilData.dat")
    dio_config_ini_file: Optional[Path] = Path("dioconfig.ini")
    bui_file_for_continuous_calculation_series: Optional[Path] = Path("NWRWCONT.#")
    nwrw_output: Optional[Path] = Path("NwrwSys.His")
    rr_routing_link_definitions: Optional[Path] = Path("3b_rout.3b")
    cell_input_file: Optional[Path] = Path("3b_cel.3b")
    cell_output_file: Optional[Path] = Path("3b_cel.his")
    rr_simulate_log_file: Optional[Path] = Path("sobek3b_progress.txt")
    rtc_coupling_wq_salt: Optional[Path] = Path("wqrtc.his")
    rr_boundary_conditions_sobek3: Optional[Path] = Path("BoundaryConditions.bc")

    rr_ascii_restart_openda: Optional[Path] = None
    lgsi_cachefile: Optional[Path] = None
    meteo_input_file_rainfall: Optional[Path] = None
    meteo_input_file_evaporation: Optional[Path] = None
    meteo_input_file_temperature: Optional[Path] = None

    @classmethod
    def property_keys(cls) -> Iterable[str]:
        # Skip first element corresponding with file_path introduced by the FileModel.
        return list(cls.schema()["properties"].keys())[1:]

    @classmethod
    def _ext(cls) -> str:
        return ".fnm"

    @classmethod
    def _filename(cls) -> str:
        return "rr"

    @classmethod
    def _get_parser(cls) -> Callable[[FilePath], Dict]:
        return lambda path: read(cls.property_keys(), path)

    @classmethod
    def _get_serializer(cls) -> Callable[[Path, Dict], None]:
        return write

"""models.py defines the RainfallRunoffModel and supporting structures."""

from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional

from pydantic.v1 import Field, validator
from pydantic.v1.types import FilePath

from hydrolib.core.base.models import (
    DiskOnlyFileModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
    validator_set_default_disk_only_file_model_when_none,
)

from .meteo.models import BuiModel
from .parser import read
from .serializer import write
from .topology.models import LinkFile, NodeFile


class ImmutableDiskOnlyFileModel(DiskOnlyFileModel, allow_mutation=False):
    """
    ImmutableDiskOnlyFileModel modifies the DiskOnlyFileModel to provide faux
    immutablitity.

    This behaviour is required for the mappix properties, which should always
    have the same name and path and should not be modified by users.
    """

    pass


_mappix_paved_area_sewage_storage_name = "pvstordt.his"
_mappix_paved_area_flow_rates_name = "pvflowdt.his"
_mappix_unpaved_area_flow_rates_name = "upflowdt.his"
_mappix_ground_water_levels_name = "upgwlvdt.his"
_mappix_green_house_bassins_storage_name = "grnstrdt.his"
_mappix_green_house_bassins_results_name = "grnflodt.his"
_mappix_open_water_details_name = "ow_lvldt.his"
_mappix_exceedance_time_reference_levels_name = "ow_excdt.his"
_mappix_flow_rates_over_structures_name = "strflodt.his"
_mappix_flow_rates_to_edge_name = "bndflodt.his"
_mappix_pluvius_max_sewage_storage_name = "plvstrdt.his"
_mappix_pluvius_max_flow_rates_name = "plvflodt.his"
_mappix_balance_name = "balansdt.his"
_mappix_cumulative_balance_name = "cumbaldt.his"
_mappix_salt_concentrations_name = "saltdt.his"


def _validator_mappix_value(field_name: str, expected: str) -> classmethod:
    def validate(v: Any) -> Any:
        if v != expected:
            actual_value = v or "None"
            raise ValueError(
                f"Expected a value of '{expected}' for '{field_name}' but got '{actual_value}'. Mappix values should not be changed."
            )
        return v

    return validator(field_name, allow_reuse=True, pre=True)(validate)


class RainfallRunoffModel(ParsableFileModel):
    """The RainfallRunoffModel contains all paths and sub-models related to the
    Rainfall Runoff model.
    """

    _disk_only_file_model_cannot_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    # Note that order is defined by the .fnm file type and is used for parsing the data.
    control_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("delft_3b.ini"))
    )
    node_data: Optional[NodeFile] = Field(None)
    link_data: Optional[LinkFile] = Field(None)
    open_water_data: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("3brunoff.tp"))
    )
    paved_area_general: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("paved.3b"))
    )
    paved_area_storage: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("paved.sto"))
    )
    paved_area_dwa: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("paved.dwa"))
    )
    paved_area_sewer_pump_capacity: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("paved.tbl"))
    )
    boundaries: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("pluvius.dwa"))
    )
    pluvius: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("pluvius.3b"))
    )
    pluvius_general: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("pluvius.alg"))
    )
    kasklasse: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("kasklass"))
    )
    bui_file: Optional[BuiModel] = Field(None)
    verdampings_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("default.evp"))
    )
    unpaved_area_general: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("unpaved.3b"))
    )
    unpaved_area_storage: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("unpaved.sto"))
    )
    green_house_area_initialisation: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("kasinit"))
    )
    green_house_area_usage_data: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("kasgebr"))
    )
    crop_factors: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("cropfact"))
    )
    table_bergingscoef: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("bergcoef"))
    )
    unpaved_alpha_factor_definitions: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("unpaved.alf"))
    )
    run_log_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("sobek_3b.log"))
    )
    schema_overview: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("3b_gener.out"))
    )
    output_results_paved_area: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("paved.out"))
    )
    output_results_unpaved_area: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("unpaved.out"))
    )
    output_results_green_houses: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("grnhous.out"))
    )
    output_results_open_water: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("openwate.out"))
    )
    output_results_structures: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("struct3b.out"))
    )
    output_results_boundaries: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("bound3b.out"))
    )
    output_results_pluvius: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("pluvius.out"))
    )
    infiltration_definitions_unpaved: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("unpaved.inf"))
    )
    run_debug_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("sobek_3b.dbg"))
    )
    unpaved_seepage: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("unpaved.sep"))
    )
    unpaved_initial_values_tables: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("unpaved.tbl"))
    )
    green_house_general: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("greenhse.3b"))
    )
    green_house_roof_storage: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("greenhse.rf"))
    )
    pluvius_sewage_entry: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("runoff.out"))
    )
    input_variable_gauges_on_edge_nodes: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("sbk_rtc.his"))
    )
    input_salt_data: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("salt.3b"))
    )
    input_crop_factors_open_water: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("crop_ow.prn"))
    )
    restart_file_input: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("RSRR_IN"))
    )
    restart_file_output: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("RSRR_OUT"))
    )
    binary_file_input: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("3b_input.bin"))
    )
    sacramento_input: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("sacrmnto.3b"))
    )
    output_flow_rates_edge_nodes: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("aanvoer.abr"))
    )
    output_salt_concentration_edge: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("saltbnd.out"))
    )
    output_salt_exportation: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("salt.out"))
    )
    greenhouse_silo_definitions: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("greenhse.sil"))
    )
    open_water_general: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("openwate.3b"))
    )
    open_water_seepage_definitions: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("openwate.sep"))
    )
    open_water_tables_target_levels: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("openwate.tbl"))
    )
    structure_general: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("struct3b.dat"))
    )
    structure_definitions: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("struct3b.def"))
    )
    controller_definitions: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("contr3b.def"))
    )
    structure_tables: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("struct3b.tbl"))
    )
    boundary_data: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("bound3b.3b"))
    )
    boundary_tables: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("bound3b.tbl"))
    )
    sobek_location_rtc: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("sbk_loc.rtc"))
    )
    wwtp_data: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("wwtp.3b"))
    )
    wwtp_tables: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("wwtp.tbl"))
    )
    industry_general: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("industry.3b"))
    )

    # Mappix paths should not change and always hold the defined values.
    _validate_mappix_paved_area_sewage_storage = _validator_mappix_value(
        "mappix_paved_area_sewage_storage", _mappix_paved_area_sewage_storage_name
    )
    mappix_paved_area_sewage_storage: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_paved_area_sewage_storage_name)),
        allow_mutation=False,
    )

    _validate_mappix_paved_area_flow_rates = _validator_mappix_value(
        "mappix_paved_area_flow_rates", _mappix_paved_area_flow_rates_name
    )
    mappix_paved_area_flow_rates: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_paved_area_flow_rates_name)),
        allow_mutation=False,
    )
    _validate_mappix_unpaved_area_flow_rates = _validator_mappix_value(
        "mappix_unpaved_area_flow_rates", _mappix_unpaved_area_flow_rates_name
    )
    mappix_unpaved_area_flow_rates: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_unpaved_area_flow_rates_name)),
        allow_mutation=False,
    )
    _validate_mappix_ground_water_levels = _validator_mappix_value(
        "mappix_ground_water_levels", _mappix_ground_water_levels_name
    )
    mappix_ground_water_levels: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_ground_water_levels_name)),
        allow_mutation=False,
    )
    _validate_mappix_green_house_bassins_storage = _validator_mappix_value(
        "mappix_green_house_bassins_storage", _mappix_green_house_bassins_storage_name
    )
    mappix_green_house_bassins_storage: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_green_house_bassins_storage_name)),
        allow_mutation=False,
    )
    _validate_mappix_green_house_bassins_results = _validator_mappix_value(
        "mappix_green_house_bassins_results", _mappix_green_house_bassins_results_name
    )
    mappix_green_house_bassins_results: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_green_house_bassins_results_name)),
        allow_mutation=False,
    )
    _validate_mappix_open_water_details = _validator_mappix_value(
        "mappix_open_water_details", _mappix_open_water_details_name
    )
    mappix_open_water_details: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_open_water_details_name)),
        allow_mutation=False,
    )
    _validate_mappix_exceedance_time_reference_levels = _validator_mappix_value(
        "mappix_exceedance_time_reference_levels",
        _mappix_exceedance_time_reference_levels_name,
    )
    mappix_exceedance_time_reference_levels: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_exceedance_time_reference_levels_name)),
        allow_mutation=False,
    )
    _validate_mappix_flow_rates_over_structures = _validator_mappix_value(
        "mappix_flow_rates_over_structures", _mappix_flow_rates_over_structures_name
    )
    mappix_flow_rates_over_structures: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_flow_rates_over_structures_name)),
        allow_mutation=False,
    )
    _validate_mappix_flow_rates_to_edge = _validator_mappix_value(
        "mappix_flow_rates_to_edge", _mappix_flow_rates_to_edge_name
    )
    mappix_flow_rates_to_edge: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_flow_rates_to_edge_name)),
        allow_mutation=False,
    )
    _validate_mappix_pluvius_max_sewage_storage = _validator_mappix_value(
        "mappix_pluvius_max_sewage_storage", _mappix_pluvius_max_sewage_storage_name
    )
    mappix_pluvius_max_sewage_storage: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_pluvius_max_sewage_storage_name)),
        allow_mutation=False,
    )
    _validate_mappix_pluvius_max_flow_rates = _validator_mappix_value(
        "mappix_pluvius_max_flow_rates", _mappix_pluvius_max_flow_rates_name
    )
    mappix_pluvius_max_flow_rates: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_pluvius_max_flow_rates_name)),
        allow_mutation=False,
    )
    _validate_mappix_balance = _validator_mappix_value(
        "mappix_balance", _mappix_balance_name
    )
    mappix_balance: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_balance_name)),
        allow_mutation=False,
    )
    _validate_mappix_cumulative_balance = _validator_mappix_value(
        "mappix_cumulative_balance", _mappix_cumulative_balance_name
    )
    mappix_cumulative_balance: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_cumulative_balance_name)),
        allow_mutation=False,
    )
    _validate_mappix_salt_concentrations = _validator_mappix_value(
        "mappix_salt_concentrations", _mappix_salt_concentrations_name
    )
    mappix_salt_concentrations: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_salt_concentrations_name)),
        allow_mutation=False,
    )

    industry_tables: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("industry.tbl"))
    )
    maalstop: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("rtc_3b.his"))
    )
    time_series_temperature: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("default.tmp"))
    )
    time_series_runoff: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("rnff.#"))
    )
    discharges_totals_at_edge_nodes: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("bndfltot.his"))
    )
    language_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("sobek_3b.lng"))
    )
    ow_volume: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("ow_vol.his"))
    )
    ow_levels: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("ow_level.his"))
    )
    balance_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("3b_bal.out"))
    )
    his_3B_area_length: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("3bareas.his"))
    )
    his_3B_structure_data: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("3bstrdim.his"))
    )
    his_rr_runoff: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("rrrunoff.his"))
    )
    his_sacramento: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("sacrmnto.his"))
    )
    his_rwzi: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("wwtpdt.his"))
    )
    his_industry: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("industdt.his"))
    )
    ctrl_ini: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("ctrl.ini"))
    )
    root_capsim_input_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("root_sim.inp"))
    )
    unsa_capsim_input_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("unsa_sim.inp"))
    )
    capsim_message_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("capsim.msg"))
    )
    capsim_debug_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("capsim.dbg"))
    )
    restart_1_hour: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("restart1.out"))
    )
    restart_12_hours: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("restart12.out"))
    )
    rr_ready: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("RR-ready"))
    )
    nwrw_areas: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("NwrwArea.His"))
    )
    link_flows: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("3blinks.his"))
    )
    modflow_rr: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("modflow_rr.His"))
    )
    rr_modflow: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("rr_modflow.His"))
    )
    rr_wlm_balance: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("rr_wlmbal.His"))
    )
    sacramento_ascii_output: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("sacrmnto.out"))
    )
    nwrw_input_dwa_table: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("pluvius.tbl"))
    )
    rr_balance: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("rrbalans.his"))
    )
    green_house_classes: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("KasKlasData.dat"))
    )
    green_house_init: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("KasInitData.dat"))
    )
    green_house_usage: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("KasGebrData.dat"))
    )
    crop_factor: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("CropData.dat"))
    )
    crop_ow: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("CropOWData.dat"))
    )
    soil_data: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("SoilData.dat"))
    )
    dio_config_ini_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("dioconfig.ini"))
    )
    bui_file_for_continuous_calculation_series: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("NWRWCONT.#"))
    )
    nwrw_output: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("NwrwSys.His"))
    )
    rr_routing_link_definitions: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("3b_rout.3b"))
    )
    cell_input_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("3b_cel.3b"))
    )
    cell_output_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("3b_cel.his"))
    )
    rr_simulate_log_file: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("sobek3b_progress.txt"))
    )
    rtc_coupling_wq_salt: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("wqrtc.his"))
    )
    rr_boundary_conditions_sobek3: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(Path("BoundaryConditions.bc"))
    )

    rr_ascii_restart_openda: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(filepath=None)
    )
    lgsi_cachefile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(filepath=None)
    )
    meteo_input_file_rainfall: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(filepath=None)
    )
    meteo_input_file_evaporation: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(filepath=None)
    )
    meteo_input_file_temperature: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(filepath=None)
    )

    @classmethod
    def property_keys(cls) -> Iterable[str]:
        # Skip first two elements corresponding with file_path and serializer_config introduced by the FileModel.
        return list(cls.schema()["properties"].keys())[2:]

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
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, SerializerConfig, ModelSaveSettings], None]:
        return write

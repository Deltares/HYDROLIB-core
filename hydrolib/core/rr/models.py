"""models.py defines the RainfallRunoffModel and supporting structures."""

from pathlib import Path
from typing import Annotated, Any, Callable, Dict, Iterable, Optional

from pydantic import (
    BeforeValidator,
    ConfigDict,
    Field,
    FilePath,
    ValidationInfo,
    field_validator,
    model_validator,
)

from hydrolib.core.base.models import (
    DiskOnlyFileModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
    set_default_disk_only_file_model,
)

from .meteo.models import BuiModel
from .parser import read
from .serializer import write
from .topology.models import LinkFile, NodeFile


class ImmutableDiskOnlyFileModel(DiskOnlyFileModel):
    """
    ImmutableDiskOnlyFileModel modifies the DiskOnlyFileModel to provide faux
    immutablitity.

    This behaviour is required for the mappix properties, which should always
    have the same name and path and should not be modified by users.
    """

    model_config = ConfigDict(frozen=True)


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


def validate_mappix_value(field_name: str, expected: str, v) -> classmethod:
    if str(v.filepath) != expected:
        actual_value = v or "None"
        raise ValueError(
            f"Expected a value of '{expected}' for '{field_name}' but got '{actual_value}'. Mappix values should not be changed."
        )
    return v


class RainfallRunoffModel(ParsableFileModel):
    """The RainfallRunoffModel contains all paths and sub-models related to the
    Rainfall Runoff model.
    """

    # Note that order is defined by the .fnm file type and is used for parsing the data.
    control_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("delft_3b.ini")))
    node_data: Optional[NodeFile] = Field(None)
    link_data: Optional[LinkFile] = Field(None)
    open_water_data: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("3brunoff.tp")))
    paved_area_general: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("paved.3b")))
    paved_area_storage: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("paved.sto")))
    paved_area_dwa: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("paved.dwa")))
    paved_area_sewer_pump_capacity: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("paved.tbl")))
    boundaries: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("pluvius.dwa")))
    pluvius: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("pluvius.3b")))
    pluvius_general: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("pluvius.alg")))
    kasklasse: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("kasklass")))
    bui_file: Optional[BuiModel] = Field(None)
    verdampings_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("default.evp")))
    unpaved_area_general: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("unpaved.3b")))
    unpaved_area_storage: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("unpaved.sto")))
    green_house_area_initialisation: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("kasinit")))
    green_house_area_usage_data: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("kasgebr")))
    crop_factors: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("cropfact")))
    table_bergingscoef: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("bergcoef")))
    unpaved_alpha_factor_definitions: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("unpaved.alf")))
    run_log_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("sobek_3b.log")))
    schema_overview: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("3b_gener.out")))
    output_results_paved_area: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("paved.out")))
    output_results_unpaved_area: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("unpaved.out")))
    output_results_green_houses: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("grnhous.out")))
    output_results_open_water: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("openwate.out")))
    output_results_structures: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("struct3b.out")))
    output_results_boundaries: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("bound3b.out")))
    output_results_pluvius: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("pluvius.out")))
    infiltration_definitions_unpaved: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("unpaved.inf")))
    run_debug_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("sobek_3b.dbg")))
    unpaved_seepage: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("unpaved.sep")))
    unpaved_initial_values_tables: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("unpaved.tbl")))
    green_house_general: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("greenhse.3b")))
    green_house_roof_storage: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("greenhse.rf")))
    pluvius_sewage_entry: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("runoff.out")))
    input_variable_gauges_on_edge_nodes: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("sbk_rtc.his")))
    input_salt_data: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("salt.3b")))
    input_crop_factors_open_water: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("crop_ow.prn")))
    restart_file_input: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("RSRR_IN")))
    restart_file_output: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("RSRR_OUT")))
    binary_file_input: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("3b_input.bin")))
    sacramento_input: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("sacrmnto.3b")))
    output_flow_rates_edge_nodes: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("aanvoer.abr")))
    output_salt_concentration_edge: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("saltbnd.out")))
    output_salt_exportation: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("salt.out")))
    greenhouse_silo_definitions: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("greenhse.sil")))
    open_water_general: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("openwate.3b")))
    open_water_seepage_definitions: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("openwate.sep")))
    open_water_tables_target_levels: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("openwate.tbl")))
    structure_general: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("struct3b.dat")))
    structure_definitions: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("struct3b.def")))
    controller_definitions: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("contr3b.def")))
    structure_tables: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("struct3b.tbl")))
    boundary_data: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("bound3b.3b")))
    boundary_tables: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("bound3b.tbl")))
    sobek_location_rtc: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("sbk_loc.rtc")))
    wwtp_data: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("wwtp.3b")))
    wwtp_tables: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("wwtp.tbl")))
    industry_general: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("industry.3b")))

    # Mappix paths should not change and always hold the defined values.
    @field_validator("mappix_paved_area_sewage_storage", mode="before")
    @classmethod
    def _validate_mappix_paved_area_sewage_storage(
        cls, v: Any, info: ValidationInfo
    ) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_paved_area_sewage_storage_name, v
        )

    mappix_paved_area_sewage_storage: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_paved_area_sewage_storage_name)),
        frozen=True,
    )

    @field_validator("mappix_paved_area_flow_rates", mode="before")
    @classmethod
    def _validate_mappix_paved_area_flow_rates(
        cls, v: Any, info: ValidationInfo
    ) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_paved_area_flow_rates_name, v
        )

    mappix_paved_area_flow_rates: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_paved_area_flow_rates_name)),
        frozen=True,
    )

    @field_validator("mappix_unpaved_area_flow_rates", mode="before")
    @classmethod
    def _validate_mappix_unpaved_area_flow_rates(
        cls, v: Any, info: ValidationInfo
    ) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_unpaved_area_flow_rates_name, v
        )

    mappix_unpaved_area_flow_rates: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_unpaved_area_flow_rates_name)),
        frozen=True,
    )

    @field_validator("mappix_ground_water_levels", mode="before")
    @classmethod
    def _validate_mappix_ground_water_levels(cls, v: Any, info: ValidationInfo) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_ground_water_levels_name, v
        )

    mappix_ground_water_levels: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_ground_water_levels_name)),
        frozen=True,
    )

    @field_validator("mappix_green_house_bassins_storage", mode="before")
    @classmethod
    def _validate_mappix_green_house_bassins_storage(
        cls, v: Any, info: ValidationInfo
    ) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_green_house_bassins_storage_name, v
        )

    mappix_green_house_bassins_storage: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_green_house_bassins_storage_name)),
        frozen=True,
    )

    @field_validator("mappix_green_house_bassins_results", mode="before")
    @classmethod
    def _validate_mappix_green_house_bassins_results(
        cls, v: Any, info: ValidationInfo
    ) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_green_house_bassins_results_name, v
        )

    mappix_green_house_bassins_results: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_green_house_bassins_results_name)),
        frozen=True,
    )

    @field_validator("mappix_open_water_details", mode="before")
    @classmethod
    def _validate_mappix_open_water_details(cls, v: Any, info: ValidationInfo) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_open_water_details_name, v
        )

    mappix_open_water_details: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_open_water_details_name)),
        frozen=True,
    )

    @field_validator("mappix_exceedance_time_reference_levels", mode="before")
    @classmethod
    def _validate_mappix_exceedance_time_reference_levels(
        cls, v: Any, info: ValidationInfo
    ) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_exceedance_time_reference_levels_name, v
        )

    mappix_exceedance_time_reference_levels: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_exceedance_time_reference_levels_name)),
        frozen=True,
    )

    @field_validator("mappix_flow_rates_over_structures", mode="before")
    @classmethod
    def _validate_mappix_flow_rates_over_structures(
        cls, v: Any, info: ValidationInfo
    ) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_flow_rates_over_structures_name, v
        )

    mappix_flow_rates_over_structures: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_flow_rates_over_structures_name)),
        frozen=True,
    )

    @field_validator("mappix_flow_rates_to_edge", mode="before")
    @classmethod
    def _validate_mappix_flow_rates_to_edge(cls, v: Any, info: ValidationInfo) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_flow_rates_to_edge_name, v
        )

    mappix_flow_rates_to_edge: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_flow_rates_to_edge_name)),
        frozen=True,
    )

    @field_validator("mappix_pluvius_max_sewage_storage", mode="before")
    @classmethod
    def _validate_mappix_pluvius_max_sewage_storage(
        cls, v: Any, info: ValidationInfo
    ) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_pluvius_max_sewage_storage_name, v
        )

    mappix_pluvius_max_sewage_storage: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_pluvius_max_sewage_storage_name)),
        frozen=True,
    )

    @field_validator("mappix_pluvius_max_flow_rates", mode="before")
    @classmethod
    def _validate_mappix_pluvius_max_flow_rates(
        cls, v: Any, info: ValidationInfo
    ) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_pluvius_max_flow_rates_name, v
        )

    mappix_pluvius_max_flow_rates: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_pluvius_max_flow_rates_name)),
        frozen=True,
    )

    @field_validator("mappix_balance", mode="before")
    @classmethod
    def _validate_mappix_balance(cls, v: Any, info: ValidationInfo) -> Any:
        return validate_mappix_value(info.field_name, _mappix_balance_name, v)

    mappix_balance: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_balance_name)),
        frozen=True,
    )

    @field_validator("mappix_cumulative_balance", mode="before")
    @classmethod
    def _validate_mappix_cumulative_balance(cls, v: Any, info: ValidationInfo) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_cumulative_balance_name, v
        )

    mappix_cumulative_balance: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_cumulative_balance_name)),
        frozen=True,
    )

    @field_validator("mappix_salt_concentrations", mode="before")
    @classmethod
    def _validate_mappix_salt_concentrations(cls, v: Any, info: ValidationInfo) -> Any:
        return validate_mappix_value(
            info.field_name, _mappix_salt_concentrations_name, v
        )

    mappix_salt_concentrations: ImmutableDiskOnlyFileModel = Field(
        ImmutableDiskOnlyFileModel(Path(_mappix_salt_concentrations_name)),
        frozen=True,
    )

    industry_tables: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("industry.tbl")))
    maalstop: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("rtc_3b.his")))
    time_series_temperature: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("default.tmp")))
    time_series_runoff: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("rnff.#")))
    discharges_totals_at_edge_nodes: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("bndfltot.his")))
    language_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("sobek_3b.lng")))
    ow_volume: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("ow_vol.his")))
    ow_levels: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("ow_level.his")))
    balance_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("3b_bal.out")))
    his_3b_area_length: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("3bareas.his")))
    his_3b_structure_data: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("3bstrdim.his")))
    his_rr_runoff: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("rrrunoff.his")))
    his_sacramento: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("sacrmnto.his")))
    his_rwzi: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("wwtpdt.his")))
    his_industry: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("industdt.his")))
    ctrl_ini: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("ctrl.ini")))
    root_capsim_input_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("root_sim.inp")))
    unsa_capsim_input_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("unsa_sim.inp")))
    capsim_message_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("capsim.msg")))
    capsim_debug_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("capsim.dbg")))
    restart_1_hour: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("restart1.out")))
    restart_12_hours: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("restart12.out")))
    rr_ready: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("RR-ready")))
    nwrw_areas: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("NwrwArea.His")))
    link_flows: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("3blinks.his")))
    modflow_rr: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("modflow_rr.His")))
    rr_modflow: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("rr_modflow.His")))
    rr_wlm_balance: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("rr_wlmbal.His")))
    sacramento_ascii_output: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("sacrmnto.out")))
    nwrw_input_dwa_table: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("pluvius.tbl")))
    rr_balance: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("rrbalans.his")))
    green_house_classes: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("KasKlasData.dat")))
    green_house_init: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("KasInitData.dat")))
    green_house_usage: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("KasGebrData.dat")))
    crop_factor: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("CropData.dat")))
    crop_ow: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("CropOWData.dat")))
    soil_data: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("SoilData.dat")))
    dio_config_ini_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("dioconfig.ini")))
    bui_file_for_continuous_calculation_series: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("NWRWCONT.#")))
    nwrw_output: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("NwrwSys.His")))
    rr_routing_link_definitions: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("3b_rout.3b")))
    cell_input_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("3b_cel.3b")))
    cell_output_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("3b_cel.his")))
    rr_simulate_log_file: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("sobek3b_progress.txt")))
    rtc_coupling_wq_salt: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("wqrtc.his")))
    rr_boundary_conditions_sobek3: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(Path("BoundaryConditions.bc")))

    rr_ascii_restart_openda: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(filepath=None))
    lgsi_cachefile: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(filepath=None))
    meteo_input_file_rainfall: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(filepath=None))
    meteo_input_file_evaporation: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(filepath=None))
    meteo_input_file_temperature: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(filepath=None))

    @model_validator(mode="before")
    @classmethod
    def _validate_diskonlyfilemodel(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure that all DiskOnlyFileModel fields are set to a default value if None."""
        for key, value in values.items():
            field = cls.model_fields.get(key)
            if (
                field is not None
                and field.annotation is DiskOnlyFileModel
                and isinstance(value, (str, Path))
            ):
                values[key] = DiskOnlyFileModel(Path(value))
        return values

    @model_validator(mode="before")
    @classmethod
    def _validate_immutable_diskonlyfilemodel(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ensure that all DiskOnlyFileModel fields are set to a default value if None."""
        for key, value in values.items():
            field = cls.model_fields.get(key)
            if (
                field is not None
                and field.annotation is ImmutableDiskOnlyFileModel
                and isinstance(value, (str, Path))
            ):
                values[key] = ImmutableDiskOnlyFileModel(Path(value))
        return values

    @field_validator("node_data", mode="before")
    @classmethod
    def _validate_node_data(cls, value: Optional[str]) -> Optional[NodeFile]:
        """Ensure that node_data is set to parsed to a model if not none."""
        if value and isinstance(value, (str, Path)):
            return NodeFile(Path(value))
        return value

    @field_validator("link_data", mode="before")
    @classmethod
    def _validate_link_data(cls, value: Optional[str]) -> Optional[LinkFile]:
        """Ensure that link_data is set to parsed to a model if not none."""
        if value and isinstance(value, (str, Path)):
            return LinkFile(Path(value))
        return value

    @field_validator("bui_file", mode="before")
    @classmethod
    def _validate_bui_file(cls, value: Optional[str]) -> Optional[BuiModel]:
        """Ensure that bui_file is set to parsed to a model if not none."""
        if value and isinstance(value, (str, Path)):
            return BuiModel(Path(value))
        return value

    @classmethod
    def property_keys(cls) -> Iterable[str]:
        # Skip first two elements corresponding with file_path and serializer_config introduced by the FileModel.
        return list(cls.model_json_schema()["properties"].keys())[2:]

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

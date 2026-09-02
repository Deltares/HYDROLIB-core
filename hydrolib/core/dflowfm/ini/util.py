"""util.py provides additional utility methods related to handling ini files."""

import warnings

from datetime import datetime
from enum import Enum
from operator import eq
from typing import Any, Callable, Dict, List, Optional, Set, Type

from pydantic import BaseModel, ValidationInfo
from pydantic.fields import FieldInfo

from hydrolib.core.base.utils import operator_str, str_is_empty_or_none, to_list
from hydrolib.core.dflowfm.common.models import LocationType


def split_string_on_delimiter(cls, v: Any, field: ValidationInfo):
    """Split a string on the list field delimiter, and return a list of strings.

    If the input is a string, it is split on the delimiter defined in the class.
    If the input is anything else, it is returned as is.

    Args:
        cls (Type[BaseModel]): The class that contains the field.
        v (Any): The value to split.
        field (ValidationInfo): The field information.

    Returns:
        List[str] or Any: A list of strings if the input was a string, otherwise
            the input value as is.
    """
    if isinstance(v, str):
        v = v.split(cls.get_list_field_delimiter(field.field_name))
        v = [item.strip() for item in v if item != ""]
    return v


def enum_value_parser(
    v,
    enum: Type[Enum],
    alternative_enum_values: Optional[Dict[str, List[str]]] = None,
):
    """Return a function that converts strings (and string lists) to Enum values.

    Args:
        enum (Type[Enum]): The Enum type to parse values into.
        alternative_enum_values (Optional[Dict[str, List[str]]]): A dictionary mapping enum values
            to alternative string representations. If provided, the parser will also accept these
            alternative strings as valid inputs for the corresponding enum values.

    Returns:
        Callable: A function that takes a value (or list of values) and returns the corresponding
            Enum value or raises a ValueError if the value is invalid.

    Raises:
        ValueError: If the input value is not a valid Enum value or does not match any
            alternative string representations.
    """
    if isinstance(v, list):
        result = [parse_enum(item, enum, alternative_enum_values) for item in v]
    else:
        result = parse_enum(v, enum, alternative_enum_values)
    return result


def parse_enum(
    v, enum: Type[Enum], alternative_enum_values: Optional[Dict[str, List[str]]] = None
):
    """Parse a value into an Enum member, with optional alternative string representations.

    Args:
        v: The value to parse.
        enum (Type[Enum]): The Enum type to parse into.
        alternative_enum_values (Optional[Dict[str, List[str]]]): Optional mapping from
            enum values to alternative string representations.

    Returns:
        Enum: The matching enum member.

    Raises:
        ValueError: If the value does not match any valid enum entry.
    """
    result = None

    if isinstance(v, enum):
        result = v
    elif isinstance(v, str):
        v_lower = v.lower()
        for entry in enum:
            if entry.value.lower() == v_lower:
                result = entry
                break
            if (
                alternative_enum_values
                and (alts := alternative_enum_values.get(entry.value))
                and any(v_lower == alt.lower() for alt in alts)
            ):
                result = entry
                warnings.warn(
                    f"{enum.__name__} value {v!r} is deprecated; "
                    f"use {entry.value!r} instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                break
    if result is None:
        valid_values = [e.value for e in enum]
        raise ValueError(f"Invalid enum value: {v!r}. Expected one of: {valid_values}")
    return result


def ensure_list(v: Any):
    """Ensure that the input is a list.

    Args:
        v (Any): The value to ensure is a list.

    Returns:
        List[Any]: A list containing the input value if it was a dictionary,
            or the input value itself if it was already a list.

    Raises:
        TypeError: If the input is not a list or a dictionary.
    """
    if isinstance(v, dict):
        v = [v]
    if not isinstance(v, list):
        raise TypeError("Expected a list or a single dictionary")
    return v


def make_list(v: Any):
    """Wrap a non-list value in a list, or return the value unchanged if it is already a list."""
    if not isinstance(v, list):
        v = [v]
    return v


def validate_correct_length(
    values: Dict,
    *field_names,
    length_name: str,
    length_incr: int = 0,
    list_required_with_length: bool = False,
    min_length: int = 0,
):
    """Validate the correct length (and presence) of several list fields in an object.

    Args:
        values (Dict):
            dictionary of values to validate.
        *field_names (str):
            names of the instance variables that are a list and need checking.
        length_name (str):
            name of the instance variable that stores the expected length.
        length_incr (int):
            Optional extra increment of length value (e.g., to have +1 extra value in lists).
        list_required_with_length (obj:`bool`, optional):
            Whether each list *must* be present if the length attribute is present (and > 0) in the input values.
            Default: False. If False, list length is only checked for the lists that are not None.
        min_length (int):
            minimum for list length value, overrides length_name value if that is smaller. For example, to require
            list length 1 when length value is given as 0.

    Raises:
        ValueError:
            When the number of values for any of the given field_names is not as expected.

    Returns:
        Dict:
            Dictionary of validated values.
    """

    def _get_incorrect_length_validation_message() -> str:
        """Make a validation message string, ready to be format()ed with field name and length name."""
        incrstring = f" + {length_incr}" if length_incr != 0 else ""
        minstring = f" (and at least {min_length})" if min_length > 0 else ""

        return (
            "Number of values for {} should be equal to the {} value"
            + incrstring
            + minstring
            + "."
        )

    def _validate_listfield_length(
        field_name: str, field: Optional[List[Any]], requiredlength: int
    ):
        """Validate the length of a single field, which should be a list."""
        if field is not None and len(field) != requiredlength:
            raise ValueError(
                _get_incorrect_length_validation_message().format(
                    field_name, length_name
                )
            )
        if field is None and list_required_with_length and requiredlength > 0:
            raise ValueError(
                f"List {field_name} cannot be missing if {length_name} is given."
            )

    length = values.get(length_name)
    if length is None:
        # length attribute not present, possibly defer validation to a subclass.
        return values

    requiredlength = max(int(length) + length_incr, min_length)

    for field_name in field_names:
        field = values.get(field_name)
        _validate_listfield_length(field_name, field, requiredlength)


def validate_forbidden_fields(
    values: Dict,
    *field_names,
    conditional_field_name: str,
    conditional_value: Any,
    comparison_func: Callable[[Any, Any], bool] = eq,
) -> Dict:
    """Validates whether certain fields are *not* provided, if `conditional_field_name` equals `conditional_value`.

    The equality check can be overridden with another comparison operator function.

    Args:
        values (Dict): Dictionary of input class fields.
        *field_names (str): Names of the instance variables that need to be validated.
        conditional_field_name (str): Name of the instance variable on which the fields are dependent.
        conditional_value (Any): Value that the conditional field should contain to perform this validation.
        comparison_func (Callable): binary operator function, used to override the default "eq" check for the conditional field value.

    Raises:
        ValueError: When a forbidden field is provided.

    Returns:
        Dict: Validated dictionary of input class fields.
    """
    if (val := values.get(conditional_field_name)) is None or not comparison_func(
        val, conditional_value
    ):
        return values

    for field in field_names:
        if values.get(field) is not None:
            raise ValueError(
                f"{field} is forbidden when {conditional_field_name} {operator_str(comparison_func)} {conditional_value}"
            )

    return values


def validate_required_fields(
    values: Dict,
    *field_names,
    conditional_field_name: str,
    conditional_value: Any,
    comparison_func: Callable[[Any, Any], bool] = eq,
):
    """Validates whether the specified fields are provided, if `conditional_field_name` equals `conditional_value`.

    The equality check can be overridden with another comparison operator function.

    Args:
        values (Dict): Dictionary of input class fields.
        *field_names (str): Names of the instance variables that need to be validated.
        conditional_field_name (str): Name of the instance variable on which the fields are dependent.
        conditional_value (Any): Value that the conditional field should contain to perform this validation.
        comparison_func (Callable): binary operator function, used to override the default "eq" check for the conditional field value.

    Raises:
        ValueError: When a required field is not provided under the given conditions.

    Returns:
        Dict: Validated dictionary of input class fields.
    """
    if (val := values.get(conditional_field_name)) is None or not comparison_func(
        val, conditional_value
    ):
        return values

    for field in field_names:
        if values.get(field) is None:
            raise ValueError(
                f"{field} should be provided when {conditional_field_name} {operator_str(comparison_func)} {conditional_value}"
            )


def validate_conditionally(
    values: Dict,
    root_vldt: classmethod,
    conditional_field_name: str,
    conditional_value: Any,
    comparison_func: Callable[[Any, Any], bool] = eq,
) -> Dict:
    """Validate whether certain fields are *not* provided, if `conditional_field_name` equals `conditional_value`.

    The equality check can be overridden with another comparison operator function.

    Args:
        values (Dict):
            Dictionary of input class fields.
        root_vldt (classmethod):
            A root validator that is to be called *if* the condition is satisfied.
        conditional_field_name (str):
            Name of the instance variable that determines whether the root validator must be called or not.
        conditional_value (Any):
            Value that the conditional field should be compared with to perform this validation.
        comparison_func (Callable):
            Binary operator function, used to override the default "eq" check for the conditional field value.

    Returns:
        Dict:
            Validated dictionary of input class fields.
    """
    if (val := values.get(conditional_field_name)) is not None and comparison_func(
        val, conditional_value
    ):
        # Condition is met: call the actual root validator, passing on the attribute values.
        root_vldt(values)


def validate_datetime_string(
    field_value: Optional[str], field: ValidationInfo
) -> Optional[str]:
    """Validate that a field value matches the expected datetime format.

    The validation checks that the date formats conform to either 'YYYYmmddHHMMSS' or 'YYYYmmdd'.

    Args:
        field_value (Optional[str]): value of a Pydantic field, may be optional.
        field (ModelField): the underlying Pydantic ModelField, used in error
            message.

    Returns:
        Optional[str]: the original input value, if valid.

    Raises:
        ValueError: if a non-empty input string does not have valid format.
    """
    if (
        field_value is not None
        and len(field_value.strip()) > 0
        and field_value != "yyyymmddhhmmss"
    ):
        formats = {14: "%Y%m%d%H%M%S", 8: "%Y%m%d"}
        result = False
        format_length = len(field_value)
        if format_length in formats:
            try:
                datetime.strptime(field_value, formats[format_length])
                result = True
            except ValueError:
                pass

        if not result:
            raise ValueError(
                f"Invalid datetime string for {field.field_name}: '{field_value}', expecting 'YYYYmmddHHMMSS' or 'YYYYmmdd'."
            )

    return field_value  # this is the value written to the class field


def get_from_subclass_defaults(cls: Type[BaseModel], fieldname: str, value: str) -> str:
    """Gets a value that corresponds with the default field value of one of the subclasses.

    If the subclass doesn't have the specified field, it will look into its own subclasses
    recursively for the specified fieldname.

    Args:
        cls (Type[BaseModel]): The parent model type.
        fieldname (str): The field name for which retrieve the default for.
        value (str): The value to compare with.

    Returns:
        str: The field default that corresponds to the value. If nothing is found return the input value.
    """
    # Immediately check in direct subclasses, not in base cls itself:
    for c in cls.__subclasses__():
        default = _try_get_default_value(c, fieldname, value)
        if default is not None:
            return default

    # No matching default was found, return input value:
    return value


def _try_get_default_value(
    c: Type[BaseModel], fieldname: str, value: str
) -> Optional[str]:
    """Helper subroutine to get the default value for a particular field in the given class.

    Also searches any descendant classes if the value matches the input value (case insensitive).
    This method recurses depth-first topdown into the class'es subclasses.

    Args:
        c (Type[BaseModel]): The base model type where the search starts.
        fieldname (str): The field name for which retrieve the default for.
        value (str): The value to compare with.

    Returns:
        Optional[str]: The field default that corresponds to the value. If nothing is found return None.
    """
    stack = [c]
    result = None
    while stack:
        current_class = stack.pop()
        if not hasattr(current_class, "model_fields"):
            continue
        field = current_class.model_fields.get(fieldname)
        if field is not None:
            # In pydantic v2, default is accessed through default_factory or directly
            if hasattr(field, "default_factory") and field.default_factory is not None:
                default = field.default_factory()
            else:
                default = field.default

            if (
                default is not None
                and hasattr(default, "lower")
                and default.lower() == value.lower()
            ):
                result = default
                break
        # Add subclasses to stack for further checking
        stack.extend(current_class.__subclasses__())
    return result


class LocationValidationConfiguration(BaseModel):
    """Class that holds the various configuration settings needed for location validation."""

    validate_node: bool = True
    """bool, optional: Whether or not node location specification should be validated. Defaults to True."""

    validate_coordinates: bool = True
    """bool, optional: Whether or not coordinate location specification should be validated. Defaults to True."""

    validate_branch: bool = True
    """bool, optional: Whether or not branch location specification should be validated. Defaults to True."""

    validate_num_coordinates: bool = True
    """bool, optional: Whether or not the number of coordinates should be validated or not. This option is only relevant when `validate_coordinates` is True. Defaults to True."""

    validate_location_type: bool = True
    """bool, optional: Whether or not the location type should be validated. Defaults to True."""

    minimum_num_coordinates: int = 0
    """int, optional: The minimum required number of coordinates. This option is only relevant when `validate_coordinates` is True. Defaults to 0."""


class LocationValidationFieldNames(BaseModel):
    """Class that holds the various field names needed for location validation."""

    node_id: str = "nodeId"
    """str, optional: The node id field name. Defaults to `nodeId`."""

    branch_id: str = "branchId"
    """str, optional: The branch id field name. Defaults to `branchId`."""

    chainage: str = "chainage"
    """str, optional: The chainage field name. Defaults to `chainage`."""

    x_coordinates: str = "xCoordinates"
    """str, optional: The x-coordinates field name. Defaults to `xCoordinates`."""

    y_coordinates: str = "yCoordinates"
    """str, optional: The y-coordinates field name. Defaults to `yCoordinates`."""

    num_coordinates: str = "numCoordinates"
    """str, optional: The number of coordinates field name. Defaults to `numCoordinates`."""

    location_type: str = "locationType"
    """str, optional: The location type field name. Defaults to `locationType`."""


class LocationValidator:
    """Encapsulates all logic for validating a location dict.

    This class groups the boolean presence-checks, individual sub-validators,
    and the top-level orchestration that was previously spread across a single
    function with many nested helpers.  It is used by the module-level
    :func:`validate_location_specification` convenience wrapper.

    Args:
        values (Dict):
            Dictionary of object's validated fields (mutated in-place when
            defaulting ``locationType``).
        config (LocationValidationConfiguration, optional):
            Switches that control which location types are accepted.
            Defaults to :class:`LocationValidationConfiguration` with all
            options enabled.
        fields (LocationValidationFieldNames, optional):
            Field-name overrides.  Defaults to
            :class:`LocationValidationFieldNames` with standard D-FLOW FM names.
    """

    def __init__(
        self,
        values: Dict,
        config: Optional[LocationValidationConfiguration] = None,
        fields: Optional[LocationValidationFieldNames] = None,
    ) -> None:
        self._config = config if config is not None else LocationValidationConfiguration()
        self._fields = fields if fields is not None else LocationValidationFieldNames()
        self._values = self._normalize_aliases(values)

        # Pre-compute presence flags once so every property/method can reuse them.
        f = self._fields
        v = self._values
        self._has_node_id = not str_is_empty_or_none(v.get(f.node_id.lower()))
        self._has_branch_id = not str_is_empty_or_none(v.get(f.branch_id.lower()))
        self._has_chainage = v.get(f.chainage.lower()) is not None
        self._has_x_coordinates = v.get(f.x_coordinates.lower()) is not None
        self._has_y_coordinates = v.get(f.y_coordinates.lower()) is not None
        self._has_num_coordinates = v.get(f.num_coordinates.lower()) is not None

    def _normalize_aliases(self, values: Dict) -> Dict:
        """Lower-case any camelCase alias keys that Pydantic has not yet resolved.

        ``mode="before"`` validators receive the raw input dict, so a caller
        passing e.g. ``branchId`` instead of ``branchid`` needs to be handled
        explicitly.
        """
        if not isinstance(values, dict):
            return values
        for alias in (
            self._fields.node_id,
            self._fields.branch_id,
            self._fields.chainage,
            self._fields.x_coordinates,
            self._fields.y_coordinates,
            self._fields.num_coordinates,
            self._fields.location_type,
        ):
            lowered = alias.lower()
            if alias != lowered and alias in values and lowered not in values:
                values[lowered] = values.pop(alias)
        return values

    def _get_length(self, field: str) -> int:
        """Return the number of coordinate values stored in *field*."""
        value = self._values[field.lower()]
        if isinstance(value, str):
            return len(value.split())
        return len(to_list(value))

    def _validate_location_type_for_node_or_branch(
        self, expected: LocationType
    ) -> None:
        """Validate / default ``locationType`` for node- or branch-based specs.

        Only ``1d`` is accepted; ``2d`` and ``all`` are rejected because they
        require coordinate fields to be meaningful.
        """
        f = self._fields
        location_type = self._values.get(f.location_type.lower(), None)
        if str_is_empty_or_none(location_type):
            self._values[f.location_type.lower()] = expected
        elif location_type in (LocationType.twod, LocationType.all):
            raise ValueError(
                f"{f.location_type}='{location_type}' is only valid when "
                f"{f.x_coordinates} and {f.y_coordinates} are also specified. "
                f"When {f.node_id} or {f.branch_id} with {f.chainage} are given, "
                f"the only accepted value is '1d'."
            )
        elif location_type != expected:
            raise ValueError(
                f"{f.location_type} should be {expected} but was {location_type}"
            )

    def _validate_location_type_for_coordinates(self) -> None:
        """Validate / default ``locationType`` for coordinate-based specs.

        When ``xCoordinates`` and ``yCoordinates`` are given, ``locationType``
        may be ``1d``, ``2d`` or ``all``.  Absent defaults to ``all``.
        """
        f = self._fields
        location_type = self._values.get(f.location_type.lower(), None)
        if str_is_empty_or_none(location_type):
            self._values[f.location_type.lower()] = LocationType.all
        elif location_type not in (LocationType.oned, LocationType.twod, LocationType.all):
            raise ValueError(
                f"{f.location_type} has invalid value '{location_type}'. "
                f"Possible values are: 1d, 2d, all"
            )

    def _validate_minimum_num_coordinates(self, actual_num: int) -> None:
        f = self._fields
        if actual_num < self._config.minimum_num_coordinates:
            raise ValueError(
                f"{f.x_coordinates} and {f.y_coordinates} should have at least "
                f"{self._config.minimum_num_coordinates} coordinate(s)"
            )

    def _validate_coordinates(self) -> None:
        """Validate that x/y coordinate lists are the same length and meet the minimum."""
        f = self._fields
        len_x = self._get_length(f.x_coordinates)
        len_y = self._get_length(f.y_coordinates)
        if len_x != len_y:
            raise ValueError(
                f"{f.x_coordinates} and {f.y_coordinates} should have an equal amount of coordinates"
            )
        self._validate_minimum_num_coordinates(len_x)

    def _validate_coordinates_with_num_coordinates(self) -> None:
        """Validate that x/y coordinate lists and numCoordinates are all consistent."""
        f = self._fields
        length_x = self._get_length(f.x_coordinates)
        length_y = self._get_length(f.y_coordinates)
        num_coordinates = int(self._values[f.num_coordinates.lower()])
        if not num_coordinates == length_x == length_y:
            raise ValueError(
                f"{f.num_coordinates} should be equal to the amount of "
                f"{f.x_coordinates} and {f.y_coordinates}"
            )
        self._validate_minimum_num_coordinates(num_coordinates)

    @property
    def _is_valid_node_specification(self) -> bool:
        has_other = (
            self._has_branch_id
            or self._has_chainage
            or self._has_x_coordinates
            or self._has_y_coordinates
            or self._has_num_coordinates
        )
        return self._has_node_id and not has_other

    @property
    def _is_valid_branch_specification(self) -> bool:
        has_other = (
            self._has_node_id
            or self._has_x_coordinates
            or self._has_y_coordinates
            or self._has_num_coordinates
        )
        return self._has_branch_id and self._has_chainage and not has_other

    @property
    def _is_valid_coordinates_specification(self) -> bool:
        has_other = (
            self._has_node_id
            or self._has_branch_id
            or self._has_chainage
            or self._has_num_coordinates
        )
        return self._has_x_coordinates and self._has_y_coordinates and not has_other

    @property
    def _is_valid_coordinates_with_num_coordinates_specification(self) -> bool:
        has_other = self._has_node_id or self._has_branch_id or self._has_chainage
        return (
            self._has_x_coordinates
            and self._has_y_coordinates
            and self._has_num_coordinates
            and not has_other
        )

    def _try_validate_node(self, error_parts: List[str]) -> Optional[Dict]:
        """Attempt to validate a node-based location specification.

        Args:
            error_parts (List[str]): Accumulator for error message fragments.

        Returns:
            Optional[Dict]: The validated values dict if the node specification
                is valid, otherwise ``None``.
        """
        result = None
        if self._config.validate_node:
            if self._is_valid_node_specification:
                if self._config.validate_location_type:
                    self._validate_location_type_for_node_or_branch(LocationType.oned)
                result = self._values
            else:
                error_parts.append(self._fields.node_id)
        return result

    def _try_validate_branch(self, error_parts: List[str]) -> Optional[Dict]:
        """Attempt to validate a branch-based location specification.

        Args:
            error_parts (List[str]): Accumulator for error message fragments.

        Returns:
            Optional[Dict]: The validated values dict if the branch specification
                is valid, otherwise ``None``.
        """
        result = None
        if self._config.validate_branch:
            f = self._fields
            if self._is_valid_branch_specification:
                if self._config.validate_location_type:
                    self._validate_location_type_for_node_or_branch(LocationType.oned)
                result = self._values
            else:
                error_parts.append(f"{f.branch_id} and {f.chainage}")
        return result

    def _try_validate_coordinates(self, error_parts: List[str]) -> Optional[Dict]:
        """Attempt to validate a coordinate-based location specification.

        Handles both the ``numCoordinates``-present and ``numCoordinates``-absent
        sub-cases.

        Args:
            error_parts (List[str]): Accumulator for error message fragments.

        Returns:
            Optional[Dict]: The validated values dict if the coordinate
                specification is valid, otherwise ``None``.
        """
        result = None
        if self._config.validate_coordinates:
            f = self._fields
            if self._config.validate_num_coordinates:
                result = self._try_validate_coordinates_with_num_coordinates(error_parts)
            elif self._is_valid_coordinates_specification:
                self._validate_coordinates()
                if self._config.validate_location_type:
                    self._validate_location_type_for_coordinates()
                result = self._values
            else:
                error_parts.append(f"{f.x_coordinates} and {f.y_coordinates}")
        return result

    def _try_validate_coordinates_with_num_coordinates(
        self, error_parts: List[str]
    ) -> Optional[Dict]:
        """Attempt to validate a coordinate specification that includes ``numCoordinates``.

        Args:
            error_parts (List[str]): Accumulator for error message fragments.

        Returns:
            Optional[Dict]: The validated values dict if the specification is
                valid, otherwise ``None``.
        """
        result = None
        f = self._fields
        if self._is_valid_coordinates_with_num_coordinates_specification:
            self._validate_coordinates_with_num_coordinates()
            if self._config.validate_location_type:
                self._validate_location_type_for_coordinates()
            result = self._values
        else:
            error_parts.append(
                f"{f.x_coordinates}, {f.y_coordinates} and {f.num_coordinates}"
            )
        return result

    def validate(self) -> Dict:
        """Run the full location-specification validation.

        Returns:
            Dict: The (possibly mutated) values dict, with ``locationType``
            defaulted where applicable.

        Raises:
            ValueError: When no valid location specification can be found in
                the values dict, or when a sub-validator detects an inconsistency.
        """
        error_parts: List[str] = []

        validators: List[Callable[[List[str]], Optional[Dict]]] = [
            self._try_validate_node,
            self._try_validate_branch,
            self._try_validate_coordinates,
        ]
        result = next(
            (r for try_validate in validators if (r := try_validate(error_parts)) is not None),
            None,
        )
        if result is not None:
            return result
        else:
            raise ValueError(" or ".join(error_parts) + " should be provided")


def rename_keys_for_backwards_compatibility(
    values: Dict, keys_to_rename: Dict[str, List[str]]
) -> Dict:
    """Renames the provided keys to support backwards compatibility.

    Args:
        values (Dict): Dictionary of input class fields.
        keys_to_rename (Dict[str, List[str]]): Dictionary of keys and a list of old keys that
            should be converted to the current key.

    Returns:
        Dict: Dictionary where the provided keys are renamed.
    """
    if not isinstance(values, dict):
        return values
    for current_keyword, old_keywords in keys_to_rename.items():
        if current_keyword in values:
            continue

        for old_keyword in old_keywords:
            if (value := values.get(old_keyword)) is not None:
                values[current_keyword] = value
                del values[old_keyword]
                break

    return values


class UnknownKeywordErrorManager:
    """Error manager for unknown keys.

    Detects unknown keys and manages the Error to the user.
    """

    def raise_error_for_unknown_keywords(
        self,
        data: Dict[str, Any],
        section_header: str,
        fields: Dict[str, FieldInfo],
        excluded_fields: Set[str],
    ) -> None:
        """
        Notify the user of unknown keywords.

        Args:
            data (Dict[str, Any]):
                Input data containing all properties which are checked on unknown keywords.
            section_header (str):
                Header of the section in which unknown keys might be detected.
            fields (Dict[str, FieldInfo]):
                Known fields of the section.
            excluded_fields (Set[str]):
                Fields which should be excluded from the check for unknown keywords.
        """
        unknown_keywords = self._get_all_unknown_keywords(data, fields, excluded_fields)

        if len(unknown_keywords) > 0:
            raise ValueError(
                f"Unknown keywords are detected in section: '{section_header}', '{unknown_keywords}'"
            )

    def _get_all_unknown_keywords(
        self,
        data: Dict[str, Any],
        fields: Dict[str, FieldInfo],
        excluded_fields: Set,
    ) -> List[str]:
        """Get all unknown keywords in the data.

        Args:
            data: Dict[str, Any]:
                Input data containing all properties which are checked on unknown keywords.
            fields: Dict[str, FieldInfo]:
                Known fields of the Model.
            excluded_fields: Set[str]:
                Fields which should be excluded from the check for unknown keywords.

        Returns:
            List[str]: List of unknown keywords.
        """
        list_of_unknown_keywords = []
        for keyword in data:
            if self._is_unknown_keyword(keyword, fields, excluded_fields):
                list_of_unknown_keywords.append(keyword)

        return list_of_unknown_keywords

    @staticmethod
    def _is_unknown_keyword(
        keyword: str, fields: Dict[str, FieldInfo], excluded_fields: Set
    ) -> bool:
        """Check if the given field name equals to any of the model field names or aliases.

        If not, the function checks if the field is not in the excluded_fields parameter.

        Args:
            keyword: str: Name of the field.
            fields: Dict[str, FieldInfo]: Known fields of the Model.
            excluded_fields: Set[str]: Fields which should be excluded from the check for unknown keywords.

        Returns:
            bool: True if the field is unknown (not a field name or alias and not in the exclude list),
            False otherwise.
        """
        exists = keyword in fields or any(
            hasattr(field_info, "alias") and keyword == field_info.alias
            for field_info in fields.values()
        )
        # the field is not in the known fields, check if it should be excluded
        unknown = not exists and keyword not in excluded_fields

        return unknown

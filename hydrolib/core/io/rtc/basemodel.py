from pydantic.class_validators import root_validator
from hydrolib.core.basemodel import BaseModel
from typing import get_origin
from hydrolib.core.utils import to_list
from pydantic.fields import ModelField

class RtcBaseModel(BaseModel):
    class Config:
        allow_population_by_field_name = True

    @root_validator(pre=True)
    def validate(cls, data) -> dict:
        if not isinstance(data, dict):
            return data
    
        data = cls._get_root_data(data)
        data = cls._get_list_data(data)

        return data

    @classmethod
    def _get_root_data(cls, data: dict) -> dict:
        """Puts the provided dictionary `data` in a new dictionary with the key `__root__`.
        This is only performed when this `cls` has a `__root__` attributes but is not delivered in the provided `data`.
        Otherwise, the original data is returned.    

        Args:
            data (dict): The data to validate that is used to initialize the class.

        Returns:
            dict: A dictionary with a `__root__` key if needed, otherwise the original data.
        """

        root_field_name = "__root__"
        root_field = cls.__fields__.get(root_field_name)

        if root_field and root_field_name not in data:
                return {root_field_name: data}
        return data

    @classmethod
    def _get_list_data(cls, data: dict) -> dict:
        for key, value in data.items():

            field = cls.__fields__.get(key)
            if not field:
                continue

            field_type = cls._get_field_type(field)

            if field_type is list:
                data[key] = to_list(value)

        return data

    @classmethod
    def _get_field_type(cls, field: ModelField):
        """Gets the non-generic field type of a model field.
        For example, if the model field type is `List[str]`, 
        the returned type will be `list`.

        Args:
            field (ModelField): The model field.

        Returns:
            The non-generic type of the model field for example `list`.
        """
        # `outer_type_` returns e.g. List[str]
        field_type = field.outer_type_

        # `origin` returns e.g. list
        origin =  get_origin(field_type)
        if origin:
            return origin
        
        if hasattr(field_type, "__origin__"):
            return field_type.__origin__

        return None

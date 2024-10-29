from enum import Enum
from pydantic import BaseModel, ConfigDict, validator
from typing import Dict, List, Optional, Union
import pandas as pd


class TransformationFunction(str, Enum):
    KEEP_COLUMNS = "keep_columns"
    RENAME = "rename"
    SET_PRIMARY_SPONSOR = "set_primary_sponsor"
    DUPLICATE = "duplicate"


class KeepColumnsParams(BaseModel):
    columns: List[str]


class RenameParams(BaseModel):
    columns: Dict[str, str]


class SetPrimarySponsorParams(BaseModel):
    sponsor_type_column: str
    is_primary_column: str


class DuplicateParams(BaseModel):
    source_name: str
    destination_name: str


class Transformation(BaseModel):
    function: TransformationFunction
    parameters: Union[KeepColumnsParams, RenameParams, SetPrimarySponsorParams, DuplicateParams]

    @validator('parameters', pre=True)
    def validate_parameters(cls, v, values):
        match values.get('function'):
            case TransformationFunction.KEEP_COLUMNS:
                return KeepColumnsParams(**v)
            case TransformationFunction.RENAME:
                return RenameParams(**v)
            case TransformationFunction.SET_PRIMARY_SPONSOR:
                return SetPrimarySponsorParams(**v)
            case TransformationFunction.DUPLICATE:
                return DuplicateParams(**v)
            case _:
                raise ValueError(f"Invalid transformation function: {values.get('function')}")


class ETLConfig(BaseModel):
    source: str
    destination: str
    transformations: List[Transformation]
    dataframe: Optional[pd.DataFrame] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

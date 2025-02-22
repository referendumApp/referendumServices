from enum import Enum
from typing import Dict, List, Type

from sqlalchemy import Column, and_, func
from sqlalchemy.sql.elements import BinaryExpression, ColumnElement

from api.schemas.interactions import SortingControllerEnum
from common.database.referendum.crud import ModelType


class SearchConfig(str, Enum):
    ENGLISH = "english"
    SIMPLE = "simple"


def create_column_filter(
    model: Type[ModelType],
    filter_options: Dict[str, List],
) -> ColumnElement[bool]:
    return and_(*(getattr(model, field).in_(value) for field, value in filter_options.items()))


def create_search_filter(
    search_query: str,
    search_config: SearchConfig,
    fields: List[Column[str]],
    prefix: bool = False,
) -> BinaryExpression:
    search_text = f"{search_query}:*" if prefix else search_query
    model_fields = fields[0] if len(fields) == 1 else func.concat_ws("", *fields)
    query_func = (
        func.to_tsquery if search_config == SearchConfig.SIMPLE else func.websearch_to_tsquery
    )

    return func.to_tsvector(search_config.value, model_fields).op("@@")(
        query_func(search_config.value, search_text)
    )


def create_sort_column_list(
    model: Type[ModelType],
    sort_option: Dict[str, SortingControllerEnum],
) -> List[Column]:
    return [
        (
            getattr(model, field).desc()
            if control == SortingControllerEnum.DESC
            else getattr(model, field)
        )
        for field, control in sort_option.items()
    ]

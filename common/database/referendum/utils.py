from typing import List, Type

from sqlalchemy import Column, and_, func
from sqlalchemy.sql.elements import BinaryExpression, ColumnElement

from api.schemas import FilterOptions
from common.database.referendum.crud import ModelType


def create_column_filter(
    model: Type[ModelType],
    filter_options: FilterOptions,
) -> ColumnElement[bool]:
    return and_(
        *(getattr(model, field).in_(value) for field, value in filter_options.model_dump().items())
    )


def create_search_filter(
    search_query: str,
    fields: List[Column[str]],
) -> BinaryExpression:
    model_fields = fields[0] if len(fields) == 1 else func.concat_ws("", *fields)

    return func.to_tsvector("english", model_fields).op("@@")(
        func.websearch_to_tsquery("english", search_query)
    )

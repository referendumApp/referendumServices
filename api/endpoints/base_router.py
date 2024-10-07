from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Generic, TypeVar, Type
from pydantic import BaseModel

from common.database.referendum import crud
from common.database.referendum.crud import (
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    DatabaseException,
)

from ..database import get_db
from ..security import get_current_user_or_verify_system_token, verify_system_token
from ..schemas import ErrorResponse

T = TypeVar("T")
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)
ResponseSchema = TypeVar("ResponseSchema", bound=BaseModel)


class BaseRouter(Generic[T, CreateSchema, UpdateSchema, ResponseSchema]):
    @classmethod
    def add_crud_routes(
        cls,
        router: APIRouter,
        crud_model: crud.BaseCRUD,
        create_schema: Type[CreateSchema],
        update_schema: Type[UpdateSchema],
        response_schema: Type[ResponseSchema],
        resource: str,
        tags: List[str],
    ):
        prefix = f"/{resource}s"

        @router.post(
            f"{prefix}/",
            response_model=response_schema,
            status_code=status.HTTP_201_CREATED,
            summary=f"Create a new {resource}",
            tags=tags,
            responses={
                201: {
                    "model": response_schema,
                    "description": f"{resource} successfully created",
                },
                403: {"model": ErrorResponse, "description": "Forbidden"},
                409: {
                    "model": ErrorResponse,
                    "description": f"{resource} already exists",
                },
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def create_item(
            item: create_schema,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(verify_system_token),
        ):
            try:
                return crud_model.create(db=db, obj_in=item)
            except ObjectAlreadyExistsException:
                raise HTTPException(
                    status_code=409, detail=f"{resource} already exists"
                )
            except DatabaseException as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        @router.get(
            f"{prefix}/{{item_id}}",
            response_model=response_schema,
            summary=f"Get {resource} information",
            tags=tags,
            responses={
                200: {"model": response_schema, "description": f"{resource} retrieved"},
                401: {"model": ErrorResponse, "description": "Not authorized"},
                404: {"model": ErrorResponse, "description": f"{resource} not found"},
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def read_item(
            item_id: int,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
        ):
            try:
                return crud_model.read(db=db, obj_id=item_id)
            except ObjectNotFoundException:
                raise HTTPException(
                    status_code=404, detail=f"{resource} not found for ID: {item_id}"
                )
            except DatabaseException as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        @router.put(
            f"{prefix}/",
            response_model=response_schema,
            summary=f"Update {resource} information",
            tags=tags,
            responses={
                200: {
                    "model": response_schema,
                    "description": f"{resource} information successfully updated",
                },
                403: {"model": ErrorResponse, "description": "Forbidden"},
                404: {"model": ErrorResponse, "description": f"{resource} not found"},
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def update_item(
            item: update_schema,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(verify_system_token),
        ):
            try:
                db_item = crud_model.read(db=db, obj_id=item.id)
                return crud_model.update(db=db, db_obj=db_item, obj_in=item)
            except ObjectNotFoundException:
                raise HTTPException(
                    status_code=404, detail=f"{resource} not found for ID: {item.id}"
                )
            except DatabaseException as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        @router.delete(
            f"{prefix}/{{item_id}}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary=f"Delete a {resource}",
            tags=tags,
            responses={
                204: {"description": f"{resource} successfully deleted"},
                403: {"model": ErrorResponse, "description": "Forbidden"},
                404: {"model": ErrorResponse, "description": f"{resource} not found"},
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def delete_item(
            item_id: int,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(verify_system_token),
        ):
            try:
                return crud_model.delete(db=db, obj_id=item_id)
            except ObjectNotFoundException:
                raise HTTPException(
                    status_code=404, detail=f"{resource} not found for ID: {item_id}"
                )
            except DatabaseException as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        @router.get(
            f"{prefix}/",
            response_model=List[response_schema],
            summary=f"Get all {resource}s",
            tags=tags,
            responses={
                200: {
                    "model": List[response_schema],
                    "description": f"{resource}s successfully retrieved",
                },
                401: {"model": ErrorResponse, "description": "Not authorized"},
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def read_items(
            skip: int = 0,
            limit: int = 100,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
        ):
            try:
                return crud_model.read_all(db=db, skip=skip, limit=limit)
            except DatabaseException as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

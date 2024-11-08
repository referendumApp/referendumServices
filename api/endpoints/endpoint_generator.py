import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Generic, TypeVar, Type, Optional, Callable
from pydantic import BaseModel, ConfigDict

from common.database.referendum import crud
from common.database.referendum.crud import (
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    DatabaseException,
)

from ..database import get_db
from ..security import get_current_user_or_verify_system_token, verify_system_token
from ..schemas import ErrorResponse

logger = logging.getLogger(__name__)

T = TypeVar("T")
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)
ResponseSchema = TypeVar("ResponseSchema", bound=BaseModel)


class CRUDPermissions(BaseModel):
    create: Callable
    read: Callable
    update: Callable
    delete: Callable
    read_all: Callable

    model_config = ConfigDict(arbitrary_types_allowed=True)


class EndpointGenerator(Generic[T, CreateSchema, UpdateSchema, ResponseSchema]):
    @classmethod
    def add_crud_routes(
        cls,
        router: APIRouter,
        crud_model: crud.BaseCRUD,
        create_schema: Type[CreateSchema],
        update_schema: Type[UpdateSchema],
        response_schema: Type[ResponseSchema],
        resource_name: str,
        permissions: Optional[CRUDPermissions] = None,
    ):
        logger.info(f"Generating CRUD routes for resource: {resource_name}")
        if not permissions:
            permissions = CRUDPermissions(
                create=verify_system_token,
                read=get_current_user_or_verify_system_token,
                update=verify_system_token,
                delete=verify_system_token,
                read_all=get_current_user_or_verify_system_token,
            )

        @router.post(
            "/",
            response_model=response_schema,
            status_code=status.HTTP_201_CREATED,
            summary=f"Create a new {resource_name}",
            responses={
                201: {
                    "model": response_schema,
                    "description": f"{resource_name} successfully created",
                },
                403: {"model": ErrorResponse, "description": "Forbidden"},
                409: {
                    "model": ErrorResponse,
                    "description": f"{resource_name} already exists",
                },
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def create_item(
            item: create_schema,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.create),
        ):
            logger.info(f"Attempting to create new {resource_name}")
            logger.error(item)
            try:
                created_item = crud_model.create(db=db, obj_in=item)
                logger.info(f"Successfully created {resource_name} with ID: {created_item.id}")
                return created_item
            except ObjectAlreadyExistsException:
                logger.warning(f"Attempt to create duplicate {resource_name}")
                raise HTTPException(status_code=409, detail=f"{resource_name} already exists")
            except DatabaseException as e:
                logger.error(f"Database error while creating {resource_name}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        @router.get(
            "/{item_id}",
            response_model=response_schema,
            summary=f"Get {resource_name} information",
            responses={
                200: {
                    "model": response_schema,
                    "description": f"{resource_name} retrieved",
                },
                401: {"model": ErrorResponse, "description": "Not authorized"},
                404: {
                    "model": ErrorResponse,
                    "description": f"{resource_name} not found",
                },
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def read_item(
            item_id: int,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.read),
        ):
            logger.info(f"Attempting to read {resource_name} with ID: {item_id}")
            try:
                item = crud_model.read(db=db, obj_id=item_id)
                logger.info(f"Successfully retrieved {resource_name} with ID: {item_id}")
                return item
            except ObjectNotFoundException:
                logger.warning(f"{resource_name} not found for ID: {item_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"{resource_name} not found for ID: {item_id}",
                )
            except DatabaseException as e:
                logger.error(f"Database error while reading {resource_name}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        @router.put(
            "/",
            response_model=response_schema,
            summary=f"Update {resource_name} information",
            responses={
                200: {
                    "model": response_schema,
                    "description": f"{resource_name} information successfully updated",
                },
                403: {"model": ErrorResponse, "description": "Forbidden"},
                404: {
                    "model": ErrorResponse,
                    "description": f"{resource_name} not found",
                },
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def update_item(
            item: update_schema,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.update),
        ):
            logger.info(f"Attempting to update {resource_name} with ID: {item.id}")
            try:
                db_item = crud_model.read(db=db, obj_id=item.id)
                updated_item = crud_model.update(db=db, db_obj=db_item, obj_in=item)
                logger.info(f"Successfully updated {resource_name} with ID: {item.id}")
                return updated_item
            except ObjectNotFoundException:
                logger.warning(f"{resource_name} not found for ID: {item.id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"{resource_name} not found for ID: {item.id}",
                )
            except DatabaseException as e:
                logger.error(f"Database error while updating {resource_name}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        @router.put(
            "/bulk",
            response_model=List[response_schema],
            summary=f"Bulk update {resource_name} information",
            responses={
                200: {
                    "model": List[response_schema],
                    "description": f"{resource_name} information successfully updated",
                },
                403: {"model": ErrorResponse, "description": "Forbidden"},
                404: {
                    "model": ErrorResponse,
                    "description": f"{resource_name} not found",
                },
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def bulk_update_item(
            item_list: List[update_schema],
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.update),
        ):
            try:
                updated_item_list = []
                for item in item_list:
                    logger.info(f"Attempting to update {resource_name} with ID: {item.id}")
                    db_item = crud_model.read(db=db, obj_id=item.id)
                    updated_item = crud_model.update(db=db, db_obj=db_item, obj_in=item)
                    updated_item_list.append(updated_item)
                    logger.info(f"Successfully updated {resource_name} with ID: {item.id}")
                return updated_item_list
            except DatabaseException as e:
                logger.error(f"Database error while updating {resource_name}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        @router.delete(
            "/{item_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary=f"Delete a {resource_name}",
            responses={
                204: {"description": f"{resource_name} successfully deleted"},
                403: {"model": ErrorResponse, "description": "Forbidden"},
                404: {
                    "model": ErrorResponse,
                    "description": f"{resource_name} not found",
                },
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def delete_item(
            item_id: int,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.delete),
        ):
            logger.info(f"Attempting to delete {resource_name} with ID: {item_id}")
            try:
                crud_model.delete(db=db, obj_id=item_id)
                logger.info(f"Successfully deleted {resource_name} with ID: {item_id}")
                return
            except ObjectNotFoundException:
                logger.warning(f"{resource_name} not found for ID: {item_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"{resource_name} not found for ID: {item_id}",
                )
            except DatabaseException as e:
                logger.error(f"Database error while deleting {resource_name}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        @router.get(
            "/",
            response_model=List[response_schema],
            summary=f"Get all {resource_name}s",
            responses={
                200: {
                    "model": List[response_schema],
                    "description": f"{resource_name}s successfully retrieved",
                },
                401: {"model": ErrorResponse, "description": "Not authorized"},
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def read_items(
            skip: int = 0,
            limit: int = 100,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.read_all),
        ):
            logger.info(f"Attempting to read all {resource_name}s (skip: {skip}, limit: {limit})")
            try:
                items = crud_model.read_all(db=db, skip=skip, limit=limit)
                logger.info(f"Successfully retrieved {len(items)} {resource_name}s")
                return items
            except DatabaseException as e:
                logger.error(f"Database error while reading all {resource_name}s: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

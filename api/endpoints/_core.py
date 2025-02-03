import logging
from functools import wraps
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from common.database.referendum import crud
from common.database.referendum.crud import (
    DatabaseException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
)

from ..database import get_db
from ..schemas.interactions import ErrorResponse
from ..security import get_current_user_or_verify_system_token, verify_system_token

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


def handle_general_exceptions() -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException as e:
                logger.error(f"HTTP Exception: {str(e)}", exc_info=True)
                raise e
            except DatabaseException as e:
                exception_message = f"Database error: {str(e)}"
                logger.error(f"{exception_message}. Exception: {str(e)}", exc_info=True)
                raise HTTPException(status_code=400, detail=exception_message)
            except Exception as e:
                exception_message = (
                    f"Internal server error. Type: {type(e).__name__} Exception: {str(e)}"
                )
                logger.error(exception_message, exc_info=True)
                raise HTTPException(status_code=500, detail=exception_message)

        return wrapper

    return decorator


def handle_crud_exceptions(resource_name: str) -> Callable:
    """Specific exception handler for CRUD operations.
    Handles ObjectNotFound and ObjectAlreadyExists in addition to handle_general_exceptions
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @handle_general_exceptions()
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ObjectNotFoundException as e:
                exception_message = f"{resource_name} not found"
                logger.error(f"{exception_message}. Exception: {str(e)}", exc_info=True)
                raise HTTPException(status_code=404, detail=exception_message)
            except ObjectAlreadyExistsException as e:
                exception_message = f"Attempt to create duplicate {resource_name}"
                logger.warning(f"{exception_message}. Exception: {str(e)}", exc_info=True)
                raise HTTPException(status_code=409, detail=f"{resource_name} already exists")

        return wrapper

    return decorator


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
        @handle_crud_exceptions(resource_name)
        async def create_item(
            item: create_schema,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.create),
        ):
            created_item = crud_model.create(db=db, obj_in=item)
            logger.info(f"Successfully created {resource_name} with ID: {created_item.id}")
            return created_item

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
        @handle_crud_exceptions(resource_name)
        async def read_item(
            item_id: int,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.read),
        ):
            item = crud_model.read(db=db, obj_id=item_id)
            logger.info(f"Successfully retrieved {resource_name} with ID: {item_id}")
            return item

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
        @handle_crud_exceptions(resource_name)
        async def update_item(
            item: update_schema,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.update),
        ):
            db_item = crud_model.read(db=db, obj_id=item.id)
            updated_item = crud_model.update(db=db, db_obj=db_item, obj_in=item)
            logger.info(f"Successfully updated {resource_name} with ID: {item.id}")
            return updated_item

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
        @handle_crud_exceptions(resource_name)
        async def bulk_update_item(
            item_list: List[update_schema],
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.update),
        ):
            updated_item_list = []
            for item in item_list:
                logger.info(f"Attempting to update {resource_name} with ID: {item.id}")
                db_item = crud_model.read(db=db, obj_id=item.id)
                updated_item = crud_model.update(db=db, db_obj=db_item, obj_in=item)
                updated_item_list.append(updated_item)
                logger.info(f"Successfully updated {resource_name} with ID: {item.id}")
            return updated_item_list

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
        @handle_crud_exceptions(resource_name)
        async def delete_item(
            item_id: int,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.delete),
        ):
            crud_model.delete(db=db, obj_id=item_id)
            logger.info(f"Successfully deleted {resource_name} with ID: {item_id}")
            return

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
        @handle_crud_exceptions(resource_name)
        async def read_items(
            skip: int | None = None,
            limit: int | None = None,
            db: Session = Depends(get_db),
            _: Dict[str, Any] = Depends(permissions.read_all),
        ):
            items = crud_model.read_all(db=db, skip=skip, limit=limit)
            logger.info(f"Successfully retrieved {len(items)} {resource_name}s")
            return items

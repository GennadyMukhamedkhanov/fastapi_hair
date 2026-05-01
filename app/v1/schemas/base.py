from typing import Annotated, Generic, TypeVar, List

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class PageParams(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: Annotated[int, Field(ge=1, description="Номер страницы")]
    page_size: Annotated[int, Field(ge=1, le=100, description="Количество элементов на странице")]


class SortParams(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sort_by: Annotated[str, Field(pattern=r"^[a-z_]+$", description="Поле для сортировки")]
    sort_order: Annotated[str, Field(pattern=r"^(asc|desc)$", description="Направление сортировки")]


class PaginationResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True,
                              alias_generator=lambda x: x[0].upper() + x[1:])

    items: Annotated[List[T], Field(..., description="Список элементов")]
    total: Annotated[int, Field(ge=0, description="Общее количество")]
    page: Annotated[int, Field(ge=1, description="Текущая страница")]
    page_size: Annotated[int, Field(ge=1, description="Размер страницы")]
    pages: Annotated[int, Field(ge=0, description="Общее количество страниц")]

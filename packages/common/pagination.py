from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class PageMeta(BaseModel):
    model_config = ConfigDict(frozen=True)

    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_items: int = Field(..., ge=0)


class Page(BaseModel, Generic[T]):
    model_config = ConfigDict(frozen=True)

    items: list[T]
    meta: PageMeta

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    model_config = ConfigDict(frozen=True)

    value: T

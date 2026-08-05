from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from .base import DTOModel


class NextLink(DTOModel):
    href: str | None = None


class Links(DTOModel):
    next: NextLink | None = None


T = TypeVar("T", bound=BaseModel)


class Page(BaseModel, Generic[T]):
    items: list[T]
    links: Links | None = Field(None, validation_alias="_links")

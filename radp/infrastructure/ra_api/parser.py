from typing import Type, TypeVar

from pydantic import BaseModel

from radp.infrastructure.ra_api.dto.pages import Page
from radp.infrastructure.transport.response import HTTPResponse

T = TypeVar("T", bound=BaseModel)


def parse_response(response: HTTPResponse, model: Type[T]) -> T:
    return model.model_validate(response.json())


def parse_page(response: HTTPResponse, model: Type[T]) -> Page[T]:
    return Page[model].model_validate(response.json())

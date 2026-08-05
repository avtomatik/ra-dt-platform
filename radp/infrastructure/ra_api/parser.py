from typing import Type, TypeVar

import requests
from pydantic import BaseModel

from radp.infrastructure.ra_api.dto.pages import Page

T = TypeVar("T", bound=BaseModel)


def parse_response(response: requests.Response, model: Type[T]) -> T:
    return model.model_validate(response.json())


def parse_page(response: requests.Response, model: Type[T]) -> Page[T]:
    return Page[model].model_validate(response.json())

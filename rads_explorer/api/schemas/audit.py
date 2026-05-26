from pydantic import Field

from .base import APIModel


class CreatorMixin(APIModel):
    creator_id: str = Field(validation_alias="creatorId")
    creator_name: str = Field(validation_alias="creatorName")
    creator_login: str = Field(validation_alias="creatorLogin")


class ResolverMixin(APIModel):
    resolver_id: str = Field(validation_alias="resolverId")
    resolver_name: str = Field(validation_alias="resolverName")
    resolver_login: str = Field(validation_alias="resolverLogin")

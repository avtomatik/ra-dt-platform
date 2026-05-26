from .base import APIModel


class NextLink(APIModel):
    href: str | None = None


class Links(APIModel):
    next: NextLink | None = None

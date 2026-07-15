from .base import DTOModel


class NextLink(DTOModel):
    href: str | None = None


class Links(DTOModel):
    next: NextLink | None = None

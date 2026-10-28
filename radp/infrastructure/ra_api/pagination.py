from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TypeVar

from pydantic import BaseModel

from radp.infrastructure.ra_api.dto.pages import Page

T = TypeVar("T", bound=BaseModel)


class PaginationLoopError(RuntimeError):
    """Raised when the API returns a repeated pagination URL."""


async def paginate_pages(
    first_page: Page[T],
    fetch_page: Callable[[str], Awaitable[Page[T]]],
) -> AsyncIterator[Page[T]]:
    page = first_page
    visited_hrefs: set[str] = set()
    while True:
        yield page
        next_link = page.links.next if page.links else None
        href = next_link.href if next_link else None
        if not href:
            return
        if href in visited_hrefs:
            raise PaginationLoopError(f"Pagination loop detected: {href}.")
        visited_hrefs.add(href)
        page = await fetch_page(href)


async def paginate(
    first_page: Page[T],
    fetch_page: Callable[[str], Awaitable[Page[T]]],
) -> AsyncIterator[Page[T]]:
    async for page in paginate_pages(first_page, fetch_page):
        for item in page.items:
            yield item

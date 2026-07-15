def paginate(first_page, fetch_page):
    page = first_page
    visited = set()

    while page is not None:
        yield from page.items

        href = page.links.next.href if page.links and page.links.next else None

        if href is None:
            break

        if href in visited:
            raise RuntimeError(f"Pagination loop detected ({href})")

        visited.add(href)

        page = fetch_page(href)

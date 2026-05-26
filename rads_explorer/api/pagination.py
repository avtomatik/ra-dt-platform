def paginate(first_page, fetch_page):
    page = first_page
    visited = set()

    while page:
        for item in getattr(page, "items", []):
            yield item

        links = getattr(page, "links", None)

        if not links:
            break

        next_link = getattr(links, "next", None)

        if not next_link:
            break

        href = getattr(next_link, "href", None)

        if not href:
            break

        if href in visited:
            raise RuntimeError(f"Pagination loop detected: {href}")

        visited.add(href)

        page = fetch_page(href)

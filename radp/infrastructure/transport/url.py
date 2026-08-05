from urllib.parse import urlencode, urlparse


def build_url(api_base_url: str, api_root: str, path: str, params=None) -> str:
    base = api_base_url.rstrip("/")
    parsed = urlparse(path)

    if parsed.scheme and parsed.netloc:
        url = path

    elif parsed.path.startswith(api_root):
        root = urlparse(base)
        url = f"{root.scheme}://{root.netloc}{path}"

    else:
        url = f"{base}/{path.lstrip('/')}"

    if params:
        separator = "&" if "?" in url else "?"
        url += separator + urlencode(params, doseq=True)

    return url

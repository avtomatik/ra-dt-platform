from functools import lru_cache

from radp.runtime import Runtime


@lru_cache
def get_runtime() -> Runtime:
    return Runtime()

from functools import lru_cache

from radp.bootstrap.container import Container


@lru_cache(maxsize=1)
def get_container() -> Container:
    return Container()

from radp.bootstrap.runtime import get_runtime


def initialize_runtime(reset: bool) -> int:
    container = get_runtime()
    if reset:
        container.database.reset()
    else:
        container.database.create()
    return container.bootstrap.initialize()

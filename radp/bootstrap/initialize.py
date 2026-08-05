from radp.bootstrap.database import reset_database
from radp.bootstrap.runtime import get_runtime


def initialize_runtime(is_reset_required: bool):
    runtime = get_runtime()
    if is_reset_required:
        reset_database(runtime.settings)
    runtime.initialize()

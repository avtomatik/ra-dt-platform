from radp.bootstrap.runtime import get_runtime


def excel(_args) -> None:
    runtime = get_runtime()
    runtime.reporting.export_excel()

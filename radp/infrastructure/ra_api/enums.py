from enum import StrEnum


class SearchParameter(StrEnum):
    FILTER = "filter"
    Q = "q"
    QUERY = "query"
    SEARCH = "search"
    TEXT = "text"
    VALUE = "value"

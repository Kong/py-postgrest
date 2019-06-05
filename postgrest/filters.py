from datetime import datetime
from urllib.parse import quote as urlquote
from uuid import UUID


class Filter:
    """
    A generic abstraction over the PostgREST horizontal filters
    See http://postgrest.org/en/v5.2/api.html#horizontal-filtering-rows

    This class should be subclassed for each operator.
    Except for logic operators (and/or) that have their own 'Combinatoric' class below.
    """

    def encode_parameter(self, v, top_level):
        if type(v) == str:
            if top_level:
                return urlquote(v)
            else:
                # See http://postgrest.org/en/v5.2/api.html#reserved-characters
                return urlquote('"' + v.replace('"', '\\"') + '"')
        elif type(v) == int:
            return "%d" % v
        elif type(v) == float:
            return "%.17g" % v
        elif type(v) == set:
            return "{" + ",".join([self.encode_parameter(x, False) for x in v]) + "}"
        elif type(v) == list or type(v) == tuple:
            return "(" + ",".join([self.encode_parameter(x, False) for x in v]) + ")"
        elif v is True:
            return "true"
        elif v is False:
            return "false"
        elif v is None:
            return "null"
        elif isinstance(v, UUID):
            return v.hex
        elif isinstance(v, datetime):
            return v.isoformat()
        else:
            raise TypeError("invalid filter parameter type")

    def __init__(self, value):
        self.value = value

    def prepare_query(self, top_level):
        return self.encode_parameter(self.value, top_level)


class Equal(Filter):
    """
    Corresponds to the PostgreSQL operator `=`
    """

    operator = "eq"


class GreaterThan(Filter):
    """
    Corresponds to the PostgreSQL operator `>`
    """

    operator = "gt"


class GreaterThanEqual(Filter):
    """
    Corresponds to the PostgreSQL operator `>=`
    """

    operator = "gte"


class LessThan(Filter):
    """
    Corresponds to the PostgreSQL operator `<`
    """

    operator = "lt"


class LessThanEqual(Filter):
    """
    Corresponds to the PostgreSQL operator `<=`
    """

    operator = "lte"


class NotEqual(Filter):
    """
    Corresponds to the PostgreSQL operator `!=`
    """

    operator = "neq"


class Like(Filter):
    """
    LIKE operator (use * in place of %)
    Corresponds to the PostgreSQL operator `LIKE`
    """

    operator = "like"


class ILike(Filter):
    """
    ILIKE operator (use * in place of %)
    Corresponds to the PostgreSQL operator `ILIKE`
    """

    operator = "ilike"


class In(Filter):
    """
    One of a list of values
    Corresponds to the PostgreSQL operator `IN`
    """

    operator = "in"


class Is(Filter):
    """
    Exact equality (null,true,false)
    Corresponds to the PostgreSQL operator `IS`
    """

    operator = "is"


class FullTextSearch(Filter):
    """
    Full-Text Search using `to_tsquery`
    Corresponds to the PostgreSQL operator `@@`
    """

    operator = "fts"


class PlainFullTextSearch(Filter):
    """
    Full-Text Search using `plainto_tsquery`
    Corresponds to the PostgreSQL operator `@@`
    """

    operator = "plfts"


class PhraseFullTextSearch(Filter):
    """
    Full-Text Search using `phraseto_tsquery`
    Corresponds to the PostgreSQL operator `@@`
    """

    operator = "phfts"


class Contains(Filter):
    """
    Contains
    Corresponds to the PostgreSQL operator `@>`
    """

    operator = "cs"


class ContainedIn(Filter):
    """
    Contained in
    Corresponds to the PostgreSQL operator `<@`
    """

    operator = "cd"


class Overlap(Filter):
    """
    Overlap (have points in common)
    Corresponds to the PostgreSQL operator `&&`
    """

    operator = "ov"


class StrictlyLeft(Filter):
    """
    Strictly left of
    Corresponds to the PostgreSQL operator `<<`
    """

    operator = "sl"


class StrictlyRight(Filter):
    """
    Strictly right of
    Corresponds to the PostgreSQL operator `>>`
    """

    operator = "sr"


class NotExtendRight(Filter):
    """
    Does not extend to the right of
    Corresponds to the PostgreSQL operator `&<`
    """

    operator = "nxr"


class NotExtendLeft(Filter):
    """
    Does not extend to the left of
    Corresponds to the PostgreSQL operator `&>`
    """

    operator = "nxl"


class AdjacentTo(Filter):
    """
    Is adjacent to
    Corresponds to the PostgreSQL operator `-|-`
    """

    operator = "adj"


class Not(Filter):
    """
    negates another filter
    """

    def __init__(self, filter):
        assert isinstance(filter, Filter)
        self.filter = filter

    @property
    def operator(self):
        return "not." + self.filter.operator

    def prepare_query(self, top_level):
        return self.filter.prepare_query(top_level)


class Combinatoric:
    """
    This class should be subclassed for each operator.
    """

    def __init__(self, *args):
        self.filters = args

    def prepare_query(self):
        filters = []
        for f in self.filters:
            if isinstance(f, Combinatoric):
                filters.append(f.operator + f.prepare_query())
            elif type(f[0]) == str and isinstance(f[1], Filter):
                field, filter = f
                # TODO: escape field?
                filters.append(
                    f"{urlquote(field)}.{filter.operator}.{filter.prepare_query(top_level=False)}"
                )
            else:
                raise TypeError("expected Combinatoric or named Filter")
        return "(" + ",".join(filters) + ")"


class And(Combinatoric):
    operator = "and"


class NotAnd(Combinatoric):
    operator = "not.and"


class Or(Combinatoric):
    operator = "or"


class NotOr(Combinatoric):
    operator = "not.and"

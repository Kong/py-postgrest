import aiohttp
from datetime import datetime
import json
from urllib.parse import urljoin, quote as urlquote
from uuid import UUID
from .filters import And, Combinatoric, Filter


class Error(aiohttp.ClientResponseError):
    def __init__(self, request_info, history, error_data, status=None, headers=None):
        self.details = error_data.get("details", None)
        self.hint = error_data.get("hint", None)

        super().__init__(
            request_info,
            history,
            status=status,
            message=error_data["message"],
            headers=headers,
        )

    @classmethod
    async def from_response(cls, response):
        return cls(
            response.request_info,
            response.history,
            status=response.status,
            headers=response.headers,
            error_data=await response.json(),
        )


class JSONEncoder(json.JSONEncoder):
    """
    A JSONEncoder that supports serialising UUID and datetime objects
    """

    def default(self, o):
        if isinstance(o, UUID):
            return o.hex
        elif isinstance(o, datetime):
            return o.isoformat()
        return super().default(self, o)


class Client:
    def __init__(self, instance_url, default_headers=None):
        self.instance_url = instance_url
        self.session = aiohttp.ClientSession(
            headers=default_headers, json_serialize=JSONEncoder().encode
        )

    async def close(self):
        await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, type, value, tb):
        await self.close()

    reserved_query_parameters = set(
        [
            "select",
            "columns",
            "order",
            "limit",
            "offset",
            "and",
            "not.and",
            "or",
            "not.or",
        ]
    )

    @staticmethod
    def prepare_query(select=None, filters=None, limit=None, offset=None):
        query_args = []

        if select is not None:
            select_fields = []
            for col in select:
                # TODO: aliases
                # TODO: embedding
                # TODO: embedded filters?
                # TODO: escaping
                select_fields.append(col)
            query_args.append("select=" + ",".join(select_fields))

        if filters is not None:
            for f in filters:
                if isinstance(f, Combinatoric):
                    query_args.append(f.operator + "=" + f.prepare_query())
                elif type(f[0]) == str and isinstance(f[1], Filter):
                    field, filter = f
                    if field in Client.reserved_query_parameters or "." in field:
                        # wrap in 'and' operation to avoid reserved query params
                        # or accidental interpretation as an embedded filter
                        query_args.append("and=" + And(f).prepare_query())
                    else:
                        query_args.append(
                            f"{urlquote(field)}={filter.operator}.{filter.prepare_query(top_level=True)}"
                        )
                else:
                    raise TypeError("expected Combinatoric or named Filter")

        if limit is not None:
            assert type(limit) == int
            query_args.append("limit=%d" % limit)

        if offset is not None:
            assert type(offset) == int
            query_args.append("offset=%d" % offset)

        return "&".join(query_args)

    def prepare_url(
        self, entity_type, select=None, filters=None, limit=None, offset=None
    ):
        assert entity_type != "rpc"
        return urljoin(
            self.instance_url,
            f"{urlquote(entity_type, safe='')}?{self.prepare_query(select, filters, limit, offset)}",
        )

    async def select(
        self,
        entity_type,
        select=None,
        filters=None,
        singular=False,
        limit=None,
        offset=None,
    ):
        headers = {}
        # TODO: support other return formats (e.g. CSV, application/octet-stream)
        if singular:
            headers["accept"] = "application/vnd.pgrst.object+json"
        else:
            headers["accept"] = "application/json"

        async with self.session.get(
            self.prepare_url(entity_type, select, filters, limit=limit, offset=offset),
            headers=headers,
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise await Error.from_response(response)

    async def insert(self, entity_type, item, returning="minimal", select=None):
        """
        See http://postgrest.org/en/v5.2/api.html#insertions-updates

        item: if an array, insert each member as a row.
            Otherwise, insert just the passed item

        returning: pass:
            `"minimal"` to return nothing (required if you don't have read permissions)
            `"url"` returns the url of the created object
            `"representation"` to return the inserted row(s)

        select: can be used to return related data (e.g. computed columns);
            only useful when `returning` is `"representation"`
        """
        headers = {"accept": "application/json"}
        if returning == "minimal":
            headers["prefer"] = "return=minimal"
        elif returning == "representation":
            headers["prefer"] = "return=representation"
        elif returning == "url":
            pass
        else:
            raise ValueError("invalid 'returning' argument")

        async with self.session.post(
            self.prepare_url(entity_type, select, None), headers=headers, json=item
        ) as response:
            if response.status != 201:
                raise await Error.from_response(response)

            if returning == "minimal":
                return
            elif returning == "representation":
                return await response.json()
            elif returning == "url":
                location = response.headers["location"]
                return urljoin(self.instance_url, location)

    async def update(self, entity_type, patch, filters, returning=None, select=None):
        """

        filters: which rows to update. Beware that providing None will update all rows!

        returning: pass:
            `None` returns the url of the created object
            `"representation"` to return the inserted row(s)

        select: can be used to return related data (e.g. computed columns);
            only useful when `returning` is `"representation"`
        """
        headers = {"accept": "application/json"}
        if returning == "representation":
            headers["prefer"] = "return=representation"
        else:
            assert returning is None

        async with self.session.patch(
            self.prepare_url(entity_type, select, filters), headers=headers, json=patch
        ) as response:
            if returning == "representation":
                if response.status == 200:
                    return await response.json()
            else:
                if response.status == 204:
                    return

            raise await Error.from_response(response)

    async def delete(self, entity_type, filters):
        """

        filters: which rows to update. Beware that providing None will update all rows!
        """
        async with self.session.delete(
            self.prepare_url(entity_type, None, filters), headers=None
        ) as response:
            if response.status != 204:
                raise await Error.from_response(response)

    # TODO: async def rpc

    # TODO: fetch OpenAPI specification

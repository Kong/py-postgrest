#!/usr/bin/env python3

import asyncio
from datetime import datetime
import postgrest


async def main():
    async with postgrest.Client("http://localhost:3000/") as client:
        # print *all* foos (should be empty)
        print("All foos:")
        print("  ", await client.select("foo"))

        # Add a foo
        await client.insert("foo", {"name": "my foo"})

        # print *all* foos
        print("All foos (after insert):")
        print("  ", await client.select("foo"))

        # Add another foo
        await client.insert("foo", {"name": "a different name"})

        # get a foo who's name contains "different"
        print("Contains 'different':")
        print(
            "  ",
            await client.select(
                "foo", filters=[("name", postgrest.ILike("*different*"))], singular=True
            ),
        )
        # list of foos created before the year 2010
        print("Before 2010:")
        print(
            "  ",
            await client.select(
                "foo",
                filters=[("created_at", postgrest.LessThan(datetime(2010, 1, 1)))],
            ),
        )

        # try to delete all the foos
        # will fail with permission denied
        try:
            await client.delete("foo", filters=[])
        except postgrest.Error as e:
            if e.status != 401:
                raise e from None

    async with postgrest.Client(
        "http://localhost:3001/", default_headers={"role": "administrator"}
    ) as client:
        # delete all the foos (now should work as an administrator)
        await client.delete("foo", filters=[])

        # print *all* foos (should be empty)
        print("All foos (after delete):")
        print("  ", await client.select("foo"))


if __name__ == "__main__":
    asyncio.run(main())

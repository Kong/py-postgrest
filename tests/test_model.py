import unittest
from collections import UserDict
from datetime import datetime
from enum import Enum
from uuid import UUID
from postgrest.client import Client, JSONEncoder
from postgrest.model import Model

client = Client(instance_url="https://example.com")


class TestModel(unittest.TestCase):
    def test_Model(self):
        class Foo(Model):
            entity_type = "foo"
            field_types = {"id": UUID, "name": str}

        class MyEnum(str, Enum):
            x = "x"
            y = "y"
            z = "z"

        class Bar(Model):
            entity_type = "bar"
            field_types = {
                "id": UUID,
                "owner": Foo.reference("id"),
                "created_at": datetime,
                "subtype": MyEnum,
                "details": dict,
            }

        # Check that arguments are validated
        with self.assertRaises(TypeError):
            Foo(client, id="not a uuid")

        foo = Foo(client)

        self.assertIsInstance(foo, UserDict)

        with self.assertRaises(TypeError):
            foo["id"] = "not a uuid"

        foo["id"] = UUID("7a21f0f4-3900-4ae2-b065-a19f36e01cb1")

        # Check serialisation of a partial object has expected result
        self.assertEqual(
            JSONEncoder().encode(foo.shallowDict()),
            '{"id": "7a21f0f4-3900-4ae2-b065-a19f36e01cb1"}',
        )

        with self.assertRaises(TypeError):
            foo["name"] = 42

        foo["name"] = "some name"

        self.assertEqual(
            JSONEncoder().encode(foo.shallowDict()),
            '{"id": "7a21f0f4-3900-4ae2-b065-a19f36e01cb1", "name": "some name"}',
        )

        bar = Bar(
            client,
            {
                "id": UUID("49b49b06-b8d8-4cfe-88a9-42187ea7d1be"),
                "owner": foo,
                "subtype": MyEnum("x"),
            },
        )

        self.assertIsInstance(bar, UserDict)

        # Check that shallowDict follows the reference field
        self.assertEqual(
            JSONEncoder().encode(bar.shallowDict()),
            '{"id": "49b49b06-b8d8-4cfe-88a9-42187ea7d1be", "owner": "7a21f0f4-3900-4ae2-b065-a19f36e01cb1", "subtype": "x"}',
        )


if __name__ == "__main__":
    unittest.main()

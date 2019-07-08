import unittest
import asyncio
from datetime import datetime
from enum import Enum
from uuid import UUID
from postgrest.model import Model
from postgrest.model_client import ModelClient


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

class TestModelClient(unittest.TestCase):
    def test_ModelClient(self):
        # Should be an error to pass non-model objects as entities
        with self.assertRaises(TypeError):
            class MyAPI(ModelClient):
                entities = ["not a model"]

        # Should be an error if user tries to set __postgrest_entity_map__ themselves
        with self.assertRaises(Exception):
            class MyAPI(ModelClient):
                entities = [Foo, Bar]
                __postgrest_entity_map__ = {}

        # Correct Usage
        class MyAPI(ModelClient):
            entities = [Foo, Bar]
        # metaclass should have added __postgrest_entity_map__ field
        assert MyAPI.__postgrest_entity_map__

if __name__ == "__main__":
    unittest.main()

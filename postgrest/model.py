from collections import UserDict
from datetime import datetime
from enum import Enum
from uuid import UUID


class ModelReference:
    def __init__(self, model, field):
        assert model.field_types[field], "field doesn't exist"
        self.model = model
        self.field = field

    def validate(self, value):
        return isinstance(value, self.model)


class Model(UserDict):
    entity_type = None
    field_types = None

    def __init__(self, client, data={}):
        assert self.entity_type is not None
        assert self.field_types is not None
        for key, value in data.items():
            self.validate(key, value)

        super().__init__(data)

        self.client = client

    @classmethod
    def fromJSON(cls, client, ob):
        data = {}

        for key, value in ob.items():
            if value is not None:
                field_type = cls.field_types[key]
                if isinstance(field_type, ModelReference):
                    value = field_type.model.fromJSON(client, {field_type.field: value})
                elif issubclass(field_type, Model):
                    assert isinstance(value, dict)
                    value = field_type.fromJSON(client, value)
                elif field_type == UUID:
                    value = UUID(hex=value)
                elif field_type == datetime:
                    # datetime.fromisoformat isn't suitable as it demands seconds to have 0, 3 or 6 decimal places
                    value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
                elif issubclass(field_type, Enum):
                    value = field_type(value)
                else:
                    assert isinstance(
                        value, field_type
                    ), f"{value} is not valid a {field_type}"
            data[key] = value

        return cls(client, data)

    @classmethod
    def validate(cls, key, value):
        field_type = cls.field_types[key]

        if isinstance(field_type, ModelReference):
            return field_type.validate(value)

        if value is not None and not isinstance(value, field_type):
            raise TypeError(
                f'invalid type for "{key}" (expected {field_type.__name__}, got {type(value).__name__})'
            )

    def __setitem__(self, key, value):
        self.validate(key, value)

        self.data[key] = value

    @classmethod
    def reference(cls, field):
        """
        Used to create a reference to the current Model from another Model
        """
        return ModelReference(cls, field)

    def shallowDict(self):
        """
        Makes a shallow copy of the Model data.
        Any references to other models are followed and rendered
        """

        data_dict = {}

        for key, value in self.data.items():
            field_type = self.field_types[key]
            if isinstance(field_type, ModelReference):
                assert field_type.validate(value)
                value = value[field_type.field]

            data_dict[key] = value

        return data_dict

    async def insert(self, headers=None, returning="minimal"):
        r = await self.client.insert(
            self.entity_type, self.shallowDict(), headers=headers, returning=returning
        )
        if returning == "representation":
            assert len(r) == 1
            for key, value in r[0].items():
                if value is not None:
                    field_type = self.field_types[key]
                    if field_type == UUID:
                        value = UUID(hex=value)
                self.data[key] = value

    # TODO: patch

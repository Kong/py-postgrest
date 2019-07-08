from abc import abstractmethod, ABCMeta
from .client import Client
from .model import Model


class ModelClientMetaClass(ABCMeta):
    def __new__(cls, name, bases, clsdict, **kwargs):
        assert "__postgrest_entity_map__" not in clsdict
        entities = clsdict.get("entities", None)
        if entities is not None and not isinstance(entities, property):
            clsdict["__postgrest_entity_map__"] = ModelClientMetaClass.getEntityMap(
                entities
            )

        return super().__new__(cls, name, bases, clsdict, **kwargs)

    def __setattr__(cls, key, value):
        # keep __postgrest_entity_map__ in sync with entities
        if key == "entities":
            entity_map = ModelClientMetaClass.getEntityMap(value)
            super().__setattr__("__postgrest_entity_map__", entity_map)

        super().__setattr__(key, value)

    @staticmethod
    def getEntityMap(entities):
        assert isinstance(entities, list)
        entity_map = {}
        for entity in entities:
            assert issubclass(entity, Model)
            entity_type = entity.entity_type
            if entity_type in entity_map:
                raise ValueError(f"duplicate entity_type: '{entity_type}'")
            entity_map[entity_type] = entity
        return entity_map


class ModelClient(Client, metaclass=ModelClientMetaClass):
    @property
    @abstractmethod
    def entities(self):
        pass

    async def select(
        self,
        entity_type,
        # select=None,
        filters=None,
        headers=None,
        singular=False,
        limit=None,
        offset=None,
    ):
        # Fetch upfront so we get a potential unknown entity failure *before*
        # performing a network operation
        entity = self.__postgrest_entity_map__[entity_type]

        r = await super().select(
            entity_type,
            filters=filters,
            headers=headers,
            singular=singular,
            limit=limit,
            offset=offset,
        )

        if singular:
            return entity.fromJSON(self, r)
        else:
            return [entity.fromJSON(self, o) for o in r]

    async def update(
        self,
        entity_type,
        patch,
        filters,
        headers=None,
        returning=None,
        # select=None,
    ):
        # Fetch upfront so we get a potential unknown entity failure *before*
        # performing a network operation
        entity = self.__postgrest_entity_map__[entity_type]

        r = await super().update(
            entity_type,
            patch=patch,
            filters=filters,
            headers=headers,
            returning=returning,
            # select=select,
        )

        if returning == "representation":
            return [entity.fromJSON(self, o) for o in r]

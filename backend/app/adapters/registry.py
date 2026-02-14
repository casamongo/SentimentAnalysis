from typing import Type

from app.adapters.base import AbstractSourceAdapter

_ADAPTER_REGISTRY: dict[str, Type[AbstractSourceAdapter]] = {}


def register_adapter(source_name: str):
    """Decorator to register an adapter class."""

    def decorator(cls: Type[AbstractSourceAdapter]):
        _ADAPTER_REGISTRY[source_name] = cls
        return cls

    return decorator


def get_adapter(source_name: str, **kwargs) -> AbstractSourceAdapter:
    """Factory: instantiate an adapter by source name."""
    if source_name not in _ADAPTER_REGISTRY:
        raise ValueError(f"No adapter registered for source: {source_name}")
    return _ADAPTER_REGISTRY[source_name](**kwargs)


def get_all_adapter_names() -> list[str]:
    return list(_ADAPTER_REGISTRY.keys())

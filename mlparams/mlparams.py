from collections.abc import Iterable, Mapping, Callable
from dataclasses import asdict, is_dataclass
from inspect import isclass
from types import GenericAlias, UnionType
from typing import Any, Mapping, Type, TypeVar, cast, get_args, get_origin

import yaml

__all__ = ["from_yaml", "to_yaml", "update"]

T = TypeVar("T")


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def _assert_type(val: Any, typ: Type):
    if not isinstance(val, typ):
        raise ValueError(f"{val} is not of type {typ}")


def parse(typ: Type[T], value: Any, strict: bool) -> T:
    if is_dataclass(typ):
        return parse_data_class(typ, value, strict=strict)
    elif isinstance(typ, GenericAlias):
        return parse_generic_alias(typ, value, strict=strict)
    elif isinstance(typ, UnionType):
        return parse_union_type(typ, value, strict=strict)
    elif not isclass(typ):
        raise ValueError(f"Cannot handle non-class type {typ}.")
    elif issubclass(typ, Mapping):
        return cast(T, parse_mapping(Any, Any, value, strict=strict))
    elif issubclass(typ, tuple | list):
        return cast(T, parse_iterable(Any, value, strict=strict))
    else:
        if strict:
            if isinstance(value, typ):
                return value
            else:
                if value is not None:
                    return typ(value)
        else:
            return value
    raise ValueError(f"Cannot parse {value} to {typ}.")


def parse_iterable(
    value_type: Type[Any] | Iterable[Type[Any]], values: Any, strict: bool
) -> tuple[T, ...]:
    _assert_type(values, tuple | list)
    if not isinstance(value_type, Iterable):
        return tuple(parse(value_type, val, strict=strict) for val in values)
    else:
        return tuple(
            parse(typ, val, strict=strict)
            for typ, val in zip(value_type, values, strict=True)
        )


def parse_data_class(clz: Type, kwargs: dict, strict: bool):
    if not is_dataclass(clz):
        raise ValueError(f"{clz} is not a dataclass")
    _assert_type(kwargs, dict)
    parsed_kwargs = {}
    for name, field in clz.__dataclass_fields__.items():
        if name in kwargs:
            value = parse(field.type, kwargs[name], strict=strict)
            parsed_kwargs[name] = value
        elif not strict:
            parsed_kwargs[name] = None
    return clz(**parsed_kwargs)


def parse_mapping(
    key_type: Type[Any], value_type: Type[Any], value: dict, strict: bool
) -> dict[Any, Any]:
    _assert_type(value, dict)
    return {
        parse(key_type, k, strict=True): parse(value_type, v, strict=strict)
        for k, v in value.items()
    }


def parse_generic_alias(alias: Type[Any], value: Any, strict: bool) -> Any:
    _assert_type(alias, GenericAlias)

    assert isinstance(alias, GenericAlias)
    origin = get_origin(alias)
    assert origin is not None

    args = get_args(alias)
    if issubclass(origin, tuple):
        if len(args) == 1 or args[1] == ...:
            return parse_iterable(args[0], value, strict=strict)
        else:
            return parse_iterable(args, value, strict=strict)
    elif issubclass(origin, Mapping):
        key_type, value_type = args
        return parse_mapping(key_type, value_type, value, strict=strict)
    elif issubclass(origin, Iterable):
        return parse_iterable(args[0], value, strict=strict)
    else:
        raise ValueError(f"Cannot parse generic alias {origin}")


def parse_union_type(union_type: UnionType, value: Any, strict: bool):
    # parse greedily
    for type in union_type.__args__:
        try:
            return parse(type, value, strict=strict)
        except:
            pass
    raise ValueError(f"Cannot process {union_type} for {value}")


def to_yaml(obj, stream=None):
    assert is_dataclass(type(obj))
    return yaml.dump(asdict(obj), stream, Dumper=NoAliasDumper)


def from_yaml(clz: Type[T], stream, strict: bool = True) -> T:
    return parse(clz, yaml.load(stream, yaml.Loader), strict=strict)


def _mutable_nested_dict_update(
    old: dict,
    new: dict,
    strict_keys: bool = True,
    ignore_value: Callable[[Any], bool] | None = None,
) -> dict:
    print(old, new)
    if ignore_value is None:
        ignore_value = lambda v: v is None
    for key, val in new.items():
        if key in old:
            if not ignore_value(val):
                if isinstance(val, dict):
                    print(key, val)
                    old[key] = _mutable_nested_dict_update(
                        old[key],
                        val,
                        strict_keys=strict_keys,
                        ignore_value=ignore_value,
                    )
                else:
                    old[key] = val
        elif strict_keys:
            raise ValueError(f"Update key {key} not in {old.keys()}.")
    return old


def update(
    clz: Type[T],
    old: T,
    update: T,
    strict: bool,
    ignore_value: Callable[[Any], bool] | None = None,
) -> T:
    return parse(
        clz,
        _mutable_nested_dict_update(
            asdict(old),
            asdict(update),
            ignore_value=ignore_value,
            strict_keys=strict,
        ),
        strict=strict,
    )

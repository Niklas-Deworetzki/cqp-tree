from argparse import Namespace
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar, Optional

type Configuration = Namespace


@dataclass(kw_only=True, unsafe_hash=True)
class DeclaredConfig[V]:
    key: str
    readable_name: str
    readable_description: str

    default_value: Optional[V] = None
    validation_type: Optional[type] = None
    validation_options: Optional[list[str]] = None

    SUPPORTED_TYPE_VALIDATORS: ClassVar[set[type]] = {bool, int, float, str}

    def __post_init__(self):
        if self.validation_type:
            allowed_type_names = sorted([t.__name__ for t in self.SUPPORTED_TYPE_VALIDATORS])
            error_message = (
                f'Cannot validate type {self.validation_type.__name__}. '
                f'Must be a subclass of {StrEnum.__name__} or '
                f'one of ' + ', '.join(allowed_type_names)
            )

            if self.validation_type not in self.SUPPORTED_TYPE_VALIDATORS and not issubclass(
                self.validation_type, StrEnum
            ):
                raise ValueError(error_message)

        elif self.validation_options is not None:
            if len(self.validation_options) == 0:
                raise ValueError('Cannot create configuration accepting no valid value.')
            setattr(self, 'validation_options', tuple(self.validation_options))

    def parse_value(self, value: str) -> V:
        if self.validation_type == bool:
            return value.lower() == 'true'
        elif self.validation_type:
            return self.validation_type(value)
        elif self.validation_options:
            if value not in self.validation_options:
                allowed_values = ', '.join(self.validation_options)
                raise ValueError(
                    f'Invalid configuration value `{value}´ must be one of {allowed_values}'
                )
        return value


GLOBAL_CONFIGURATION: str = ''
CONFIGURATION_VALUES: dict[DeclaredConfig, Any] = {}
CONFIGURATION_ENTRIES: dict[str, list[DeclaredConfig]] = defaultdict(list)


def declare_configuration(entry: DeclaredConfig, frontend: Optional[str] = None):
    """
    Declares a configuration key.

    :raises ValueError: If the same configuration key for
    the same frontend already has been declared.
    """
    conflicting_entries = {
        cfg.key for cfg in CONFIGURATION_ENTRIES[frontend or GLOBAL_CONFIGURATION]
    }
    if entry.key in conflicting_entries:
        raise ValueError(f'Configuration {entry.key} already declared.')
    CONFIGURATION_ENTRIES[frontend or GLOBAL_CONFIGURATION].append(entry)


def _add_config_value_to_namespace(cf: DeclaredConfig, ns: Namespace):
    value = CONFIGURATION_VALUES.get(cf, None)
    if value is not None:
        setattr(ns, cf.key, value)
    else:
        setattr(ns, cf.key, cf.default_value)


def get_global_config() -> Configuration:
    """
    Gets all global configuration values.
    """
    ns = Namespace()
    for cf in CONFIGURATION_ENTRIES[GLOBAL_CONFIGURATION]:
        _add_config_value_to_namespace(cf, ns)
    return ns


def get_frontend_configuration(
    frontend: str,
    inherited_config: Optional[Configuration] = None,
) -> Configuration:
    """
    Gets all configuration values for a given translation frontend.
    Inherits values from the given (global) config.
    """

    if inherited_config is None:
        inherited_config = get_global_config()

    ns = Namespace()
    for k, v in vars(inherited_config).items():
        setattr(ns, k, v)
    for cf in CONFIGURATION_ENTRIES[frontend]:
        _add_config_value_to_namespace(cf, ns)
    return ns


def set_config_value(key: str, value: Any, frontend: Optional[str] = None):
    """
    Set the value for a declared configuration.

    :raises KeyError: If configuration key is not declared.
    :raises ValueError: If the value is not accepted by the configuration key.
    """
    for cfg in CONFIGURATION_ENTRIES[frontend or GLOBAL_CONFIGURATION]:
        if cfg.key == key:
            CONFIGURATION_VALUES[cfg] = cfg.parse_value(value)
            return

    formatted_key = f'{frontend}.{key}' if frontend else key
    raise KeyError(f'Cannot set value for undeclared configuration: {formatted_key}')

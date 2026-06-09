from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, Iterable, Optional

type ConfigurationSection = str

GENERAL_CONFIG_SECTION: ConfigurationSection = 'general'
ANNOTATIONS_CONFIG_SECTION: ConfigurationSection = 'annotation_scheme'


@dataclass(kw_only=True, unsafe_hash=True)
class DeclaredConfig[V]:
    key: str
    readable_name: str
    readable_description: str

    default_value: Optional[V] = None
    validation_type: Optional[type] = None
    validation_options: Optional[list[str]] = None

    SUPPORTED_TYPE_VALIDATORS: ClassVar[set[type]] = {bool, int, float, str}

    def metavar(self) -> str:
        if self.validation_type == bool:
            return 'BOOL'
        elif self.validation_type in {int, float}:
            return 'NUM'
        else:
            return 'VAL'

    def __post_init__(self):
        if not self.key.isidentifier():
            raise ValueError('Key must only contain alphanumeric characters or underscore.')

        if self.validation_type:
            allowed_type_names = sorted([t.__name__ for t in self.SUPPORTED_TYPE_VALIDATORS])
            error_message = (
                f'Cannot validate type {self.validation_type.__name__}. '
                f'Must be a subclass of {StrEnum.__name__} or '
                f'one of ' + ', '.join(allowed_type_names)
            )

            if self.validation_type not in self.SUPPORTED_TYPE_VALIDATORS:
                if issubclass(self.validation_type, StrEnum):
                    self.validation_options = [
                        enum_value.value for enum_value in self.validation_type
                    ]
                else:
                    raise ValueError(error_message)

        if self.validation_options is not None:
            if len(self.validation_options) == 0:
                raise ValueError('Cannot create configuration accepting no valid value.')
            setattr(self, 'validation_options', tuple(self.validation_options))

    def parse_value(self, value: str) -> V:
        if not isinstance(value, str):
            return value

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


DECLARED_CONFIGURATION: dict[str, list[DeclaredConfig]] = defaultdict(list)


def get_declared_configuration(section: str, key: str) -> Optional[DeclaredConfig]:
    for entry in DECLARED_CONFIGURATION.get(section, []):
        if entry.key == key:
            return entry
    return None


def get_declared_configuration_sections() -> Iterable[DeclaredConfigurationSection]:
    # Sort sections alphabetically, making sure that the default section comes first.
    sections = set(DECLARED_CONFIGURATION.keys())
    sections.remove(GENERAL_CONFIG_SECTION)
    sections.remove(ANNOTATIONS_CONFIG_SECTION)
    sections = list(sorted(sections))
    sections = [ANNOTATIONS_CONFIG_SECTION, GENERAL_CONFIG_SECTION] + sections
    return [
        DeclaredConfigurationSection(
            name=name,
            entries=DECLARED_CONFIGURATION[name],
        )
        for name in sections
    ]


@dataclass(frozen=True)
class DeclaredConfigurationSection:
    name: str
    entries: Iterable[DeclaredConfig]

    def __iter__(self):
        return iter(self.entries)

    def __bool__(self):
        return bool(self.entries)


def declare_configuration(
    section: ConfigurationSection,
    *entries: DeclaredConfig,
):
    """
    Declares a configuration key.

    :raises ValueError: If the same configuration key for
    the same section already has been declared.
    """
    conflicting_keys = {cfg.key for cfg in DECLARED_CONFIGURATION[section]}
    for entry in entries:
        if entry.key in conflicting_keys:
            raise ValueError(f'Configuration {entry.key} in {section} already declared.')
        conflicting_keys.add(entry.key)

        DECLARED_CONFIGURATION[section].append(entry)


def iterate_declared_configurations() -> Iterable[tuple[str, Iterable[DeclaredConfig]]]:
    return DECLARED_CONFIGURATION.items()

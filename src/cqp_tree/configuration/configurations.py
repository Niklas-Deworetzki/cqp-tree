import tomllib
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from functools import reduce
from pathlib import Path
from typing import Any, ClassVar, Container, IO, Iterable, Optional

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
ALL_DECLARED_NAMES: set[str] = set()


def declare_configuration(
    section: ConfigurationSection,
    *entries: DeclaredConfig,
):
    """
    Declares a configuration key.

    :raises ValueError: If the same configuration key for
    the same section already has been declared.
    """
    active_section = DECLARED_CONFIGURATION[section]
    for entry in entries:
        if entry.key in ALL_DECLARED_NAMES:
            raise ValueError(f'Configuration {entry.key} is already declared.')

        ALL_DECLARED_NAMES.add(entry.key)
        active_section.append(entry)


def get_declared_configuration(section: ConfigurationSection, key: str) -> Optional[DeclaredConfig]:
    """Get declared configuration by key and section.
    Returns None if no such configuration has been declared"""
    for entry in DECLARED_CONFIGURATION[section]:
        if entry.key == key:
            return entry
    return None


@dataclass(frozen=True)
class DeclaredConfigurationSection:
    """Class representing a section of declared configurations."""

    name: str
    entries: Iterable[DeclaredConfig]

    def __iter__(self):
        return iter(self.entries)

    def __bool__(self):
        return bool(self.entries)


def get_declared_configuration_sections() -> Iterable[DeclaredConfigurationSection]:
    """Iterates DeclaredConfigurationSection objects."""

    # Sort sections alphabetically, making sure that the default sections come first.
    sections = set(DECLARED_CONFIGURATION.keys())
    sections -= {GENERAL_CONFIG_SECTION, ANNOTATIONS_CONFIG_SECTION}
    sections = [ANNOTATIONS_CONFIG_SECTION, GENERAL_CONFIG_SECTION] + list(sorted(sections))
    for name in sections:
        section = DeclaredConfigurationSection(
            name=name,
            entries=DECLARED_CONFIGURATION[name],
        )
        if section:
            yield section


def iterate_declared_configurations() -> Iterable[tuple[str, Iterable[DeclaredConfig]]]:
    return DECLARED_CONFIGURATION.items()


class Configuration:
    _inherited: Optional['Configuration']
    _values: dict[str, Any]

    def __init__(self, inherited: Optional['Configuration'], sections: dict[str, dict[str, Any]]):
        object.__setattr__(self, '_inherited', inherited)

        values = reduce(dict.__or__, sections.values(), {})
        object.__setattr__(self, '_values', values)

    def get(self, key: str) -> Any:
        if key in self._values:
            return self._values[key]
        elif self._inherited is not None:
            return self._inherited.get(key)
        else:
            return None

    def set(self, key: str, value: Any):
        self._values[key] = value

    def __getitem__(self, item: str) -> Any:
        return self.get(item)

    def __getattr__(self, name: str) -> Any:
        return self.get(name)

    def __setitem__(self, item: str, value: Any):
        self.set(item, value)

    def __setattr__(self, name: str, value: Any):
        self.set(name, value)

    def flatten(self) -> dict[str, Any]:
        flattened = self._inherited.flatten() if self._inherited is not None else {}
        return flattened | self._values


def default_configuration() -> Configuration:
    """
    Create Configuration with all declared default values.
    """

    value_sections = {
        section.name: {entry.key: entry.default_value for entry in section}
        for section in get_declared_configuration_sections()
    }
    return Configuration(inherited=None, sections=value_sections)


def configuration_from_file(
    file: Path,
    inherited: Optional[Configuration] = None,
    inherit_from_default: bool = False,
) -> Configuration:
    """
    Load Configuration from TOML file.
    """
    assert not (
        inherited and inherit_from_default
    ), 'Configuration can only inherit from either default or another configuration.'

    try:
        with file.open('rb') as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f'Invalid configuration file: {file}') from e

    loaded_config = {}
    for section, entries in data.items():
        parsed_section = {}
        if isinstance(entries, dict):
            for key, unparsed_value in entries.items():
                if declared := get_declared_configuration(section, key):
                    parsed_section[key] = declared.parse_value(unparsed_value)
                else:
                    parsed_section[key] = unparsed_value
        loaded_config[section] = parsed_section

    if not inherited and inherit_from_default:
        inherited = default_configuration()
    return Configuration(inherited=inherited, sections=loaded_config)


def print_configuration_file(f: IO[str], active_configuration: Configuration) -> None:
    """Print the active configuration to a file."""

    def _toml_escape(val) -> str:
        if isinstance(val, str):
            return f'"{val}"'
        return repr(val)

    print('# CQP/Tree profile configuration template.', file=f)
    print(file=f)

    for section in get_declared_configuration_sections():
        if not section:
            continue  # Do not generate empty sections.

        print(f'[{section.name}]', file=f)
        for entry in section:
            print(f'# {entry.readable_description}', file=f)

            if entry.validation_options is not None:
                available_values = (_toml_escape(opt) for opt in entry.validation_options)
                print('# Available values: ' + ', '.join(available_values), file=f)

            value = _toml_escape(active_configuration[entry.key])
            print(f'#{entry.key} = {value}', file=f)
        print(file=f)


def iterate_configurations_by_section(
    active_configuration: Configuration,
    hidden_sections: Container[str] = frozenset(),
    hidden_entries: dict[str, Container[str]] = None,
) -> Iterable[tuple[str, Iterable[tuple[DeclaredConfig, Any]]]]:
    hidden_entries = hidden_entries or {}

    for section in get_declared_configuration_sections():
        if section.name in hidden_sections:
            continue

        hidden_entries_for_section = hidden_entries.get(section.name, set())
        entries_with_values = [
            (entry, active_configuration[entry.key])
            for entry in section
            if entry.key not in hidden_entries_for_section
        ]
        if entries_with_values:
            yield section.name, entries_with_values

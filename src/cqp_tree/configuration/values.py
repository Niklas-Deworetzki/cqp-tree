import tomllib
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Container, IO, Iterable, Optional

from cqp_tree.configuration.declaration import (
    DECLARED_CONFIGURATION,
    DEFAULT_CONFIGURATION_SECTION,
    DeclaredConfig,
)

type Configuration = Namespace


@dataclass
class ActiveConfig:
    """
    Data structure holding all active configuration values.
    """

    inherited: Optional['ActiveConfig']
    sections: dict[str, dict[str, Any]]

    def put(self, section: str, key: str, value: Any):
        if section not in self.sections:
            self.sections[section] = {key: value}
        else:
            self.sections[section][key] = value

    def get[V](self, section: str, key: str, default: V = None) -> V:
        if section in self.sections:
            active_section = self.sections[section]
            if key in active_section:
                return active_section[key]

        if self.inherited is not None:
            return self.inherited.get(section, key, default)

        return default

    def project(self, *sections: str) -> Configuration:
        ns = Namespace() if self.inherited is None else self.inherited.project(*sections)
        for section in sections:
            for key, value in self.sections.get(section, {}).items():
                setattr(ns, key, value)
        return ns


def default_configuration() -> ActiveConfig:
    """
    Create Configuration with all declared default values.
    """

    value_sections = {
        section: {entry.key: entry.default_value for entry in entries}
        for section, entries in DECLARED_CONFIGURATION.items()
    }
    return ActiveConfig(inherited=None, sections=value_sections)


def configuration_from_file(file: Path, inherited: ActiveConfig) -> ActiveConfig:
    """
    Load Configuration from TOML file.
    """
    with file.open('rb') as f:
        data = tomllib.load(f)
        value_sections = {section: dict(entries) for section, entries in data.items()}
        return ActiveConfig(inherited=inherited, sections=value_sections)


def _nice_section_order() -> Iterable[str]:
    # Sort sections alphabetically, making sure that the default section comes first.
    sections = set(DECLARED_CONFIGURATION.keys())
    sections.remove(DEFAULT_CONFIGURATION_SECTION)
    sections = list(sorted(sections))
    sections.insert(0, DEFAULT_CONFIGURATION_SECTION)
    return sections


def print_configuration_file(f: IO[str], active_configuration: ActiveConfig) -> None:
    """Print the active configuration to a file."""

    print('# CQP/Tree profile configuration template.', file=f)
    print(file=f)

    for section in _nice_section_order():
        if not DECLARED_CONFIGURATION[section]:
            continue  # Do not generate empty sections.

        print(f'[{section}]', file=f)
        for entry in DECLARED_CONFIGURATION[section]:
            print(f'# {entry.readable_description}', file=f)

            if entry.validation_options is not None:
                print('# Available values: ' + ', '.join(entry.validation_options), file=f)

            value = active_configuration.get(section, entry.key)
            if isinstance(value, str):
                value = f'"{value}"'
            elif value is None:
                value = ''
            print(f'#{entry.key} = {value}', file=f)
        print(file=f)


def iterate_configurations_by_section(
    active_configuration: ActiveConfig,
    hidden_sections: Container[str] = frozenset(),
    hidden_entries: dict[str, Container[str]] = None,
) -> Iterable[tuple[str, Iterable[tuple[DeclaredConfig, Any]]]]:
    hidden_entries = hidden_entries or {}

    for section in _nice_section_order():
        if section in hidden_sections:
            continue

        hidden_entries_for_section = hidden_entries.get(section, set())
        entries_with_values = [
            (entry, active_configuration.get(section, entry.key))
            for entry in DECLARED_CONFIGURATION[section]
            if entry.key not in hidden_entries_for_section
        ]
        if entries_with_values:
            yield section, entries_with_values

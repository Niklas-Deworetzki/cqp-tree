import tomllib
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Container, IO, Iterable, Optional

from cqp_tree.configuration.declaration import (
    DECLARED_CONFIGURATION,
    DeclaredConfig,
    get_declared_configuration,
    get_declared_configuration_sections,
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
        section.name: {entry.key: entry.default_value for entry in section}
        for section in get_declared_configuration_sections()
    }
    return ActiveConfig(inherited=None, sections=value_sections)


def read_corpus_config(file: Path) -> dict:
    with file.open('rb') as f:
        return tomllib.load(f)

def configuration_from_file(file: Path, inherited: ActiveConfig) -> ActiveConfig:
    """
    Load Configuration from TOML file.
    """
    data = read_corpus_config(file)
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
    return ActiveConfig(inherited=inherited, sections=loaded_config)


def print_configuration_file(f: IO[str], active_configuration: ActiveConfig) -> None:
    """Print the active configuration to a file."""

    print('# CQP/Tree profile configuration template.', file=f)
    print(file=f)

    for section in get_declared_configuration_sections():
        if not section:
            continue  # Do not generate empty sections.

        print(f'[{section.name}]', file=f)
        for entry in section:
            print(f'# {entry.readable_description}', file=f)

            if entry.validation_options is not None:
                print('# Available values: ' + ', '.join(entry.validation_options), file=f)

            value = active_configuration.get(section.name, entry.key)
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

    for section in get_declared_configuration_sections():
        if section.name in hidden_sections:
            continue

        hidden_entries_for_section = hidden_entries.get(section.name, set())
        entries_with_values = [
            (entry, active_configuration.get(section.name, entry.key))
            for entry in section
            if entry.key not in hidden_entries_for_section
        ]
        if entries_with_values:
            yield section.name, entries_with_values

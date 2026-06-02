from pathlib import Path
from typing import TextIO
import tomllib

from cqp_tree.configuration.configuration import CONFIGURATION_ENTRIES, set_config_value

GLOBAL_SECTION_NAME = 'general'
PROFILES_DIR = Path(__file__).parent / 'profiles'


def discover_builtin_profiles() -> dict[str, Path]:
    """Returns builtin profiles by name and their path."""
    return {
        file.stem: file
        for file in PROFILES_DIR.iterdir()
        if file.is_file() and file.suffix == '.toml'
    }


def load_builtin_profile(name: str):
    """Load one of the builtin profiles."""
    for profile_name, profile_file in discover_builtin_profiles().items():
        if profile_name.casefold() == name.casefold():
            load_profile(profile_file)
    raise ValueError(f'No profile named "{name}" found.')


def load_profile(file: Path):
    """Load a profile/configuration from file."""
    with file.open('r') as f:
        data = tomllib.load(f)

        for section, entries in data.items():
            if section == GLOBAL_SECTION_NAME:
                section = None
            for key, value in entries.items():
                set_config_value(key, value, section)


def print_profile_template(f: TextIO):
    """Print the currently active configuration to a file."""
    print('# CQP/Tree profile configuration template.', file=f)
    print(file=f)

    for section, entries in CONFIGURATION_ENTRIES.items():
        if section is None:
            section = GLOBAL_SECTION_NAME
        print(f'[{section}]', file=f)
        for entry in entries:
            print(f'# {entry.readable_description}', file=f)

            if entry.validation_options is not None:
                print('# Available values: ' + ', '.join(entry.validation_options), file=f)

            value = entry.get()
            if isinstance(value, str):
                value = f'"{value}"'
            elif value is None:
                value = ''
            print(f'#{entry.key} = {value}', file=f)
        print(file=f)

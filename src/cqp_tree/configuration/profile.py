from pathlib import Path
from typing import Optional

from cqp_tree.configuration.configurations import Configuration, configuration_from_file

PROFILES_DIR = Path(__file__).parent / 'profiles'


def _fetch_available_profiles() -> dict[str, Path]:
    return {
        file.stem: file
        for file in PROFILES_DIR.iterdir()
        if file.is_file() and file.suffix == '.toml'
    }


def available_profiles() -> set[str]:
    """Set of names from available profiles."""
    return set(_fetch_available_profiles().keys())


def configuration_from_profile(
    name: str,
    inherited: Optional[Configuration] = None,
    inherit_from_default: bool = False,
) -> Configuration:
    """
    Attempt to load an ActiveConfig from a profile file.

    :raises KeyError: If profile with the given name does not exist.
    """
    profile_file = _fetch_available_profiles().get(name)
    if profile_file is None:
        raise KeyError(f'No profile named {name}.')
    return configuration_from_file(profile_file, inherited, inherit_from_default)

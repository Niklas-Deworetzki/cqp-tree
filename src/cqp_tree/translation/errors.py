from dataclasses import dataclass
from typing import Any

from cqp_tree.utils import NonEmpty


@dataclass(frozen=True)
class InputError:
    """
    Error discovered while parsing input.
    """

    position: Any
    message: str

    def __repr__(self) -> str:
        return f'{self.position}: {self.message}'


@dataclass(frozen=True)
class ParsingFailed(Exception):
    """
    Exception raised when parsing fails.
    """

    errors: NonEmpty[InputError]

    def __post_init__(self):
        super().__init__(f'Parsing failed. Detected {len(self.errors)} error(s).')
        assert self.errors, 'Expected at least 1 InputError as an argument.'


class NotSupported(Exception):
    """
    Exception raised when a query construct cannot (yet) be translated.
    """

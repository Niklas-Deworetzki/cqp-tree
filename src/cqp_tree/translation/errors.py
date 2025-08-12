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


class ParsingFailed(Exception):
    """
    Exception raised when parsing fails.
    """

    errors: NonEmpty[InputError]

    def __init__(self, *errors: InputError):
        assert errors, 'Expected at least 1 InputError as an argument.'
        super().__init__(f'Parsing failed. Detected {len(errors)} error(s).')
        self.errors = tuple(errors)


class NotSupported(Exception):
    """
    Exception raised when a query construct cannot (yet) be translated.
    """

from dataclasses import dataclass
from typing import Any, Tuple


@dataclass(frozen=True)
class ParseError:
    """
    Error discovered while parsing.
    """

    position: Any
    message: str

    def __repr__(self) -> str:
        return f'{self.position}: {self.message}'


NonEmpty = Tuple[ParseError, *tuple[ParseError, ...]]


@dataclass
class ParsingFailed(Exception):
    """
    Exception raised when parsing fails.
    """

    errors: NonEmpty

    def __post_init__(self):
        super().__init__(f'Parsing failed. Detected {len(self.errors)} error(s).')


class NotSupported(Exception):
    """
    Exception raised when a query construct cannot (yet) be translated.
    """

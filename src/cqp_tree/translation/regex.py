CHARACTERS_TO_ESCAPE = "\\.|+?*[]()"


def escape_regex_string(string: str) -> str:
    for char in CHARACTERS_TO_ESCAPE:
        string = string.replace(char, '\\' + char)
    return string

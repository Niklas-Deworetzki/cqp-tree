from subprocess import run
from typing import Optional


def execute(*cmd: str) -> str | None:
    try:
        return run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        return None


def get_version() -> Optional[str]:
    tag = execute('git', 'describe', '--tags', '--always', '--dirty')
    if tag:
        date = execute('git', 'show', '-s', '--format=%cs', 'HEAD')
        return f'{tag} ({date})'
    return None

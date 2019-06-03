# myfin/finance/debug_scripts/get_dirs.py

from pathlib import Path

def get_dirs(path):
    """
    Returns a dict whose keys are the directories in path.
    Values are lists of file paths.
    """
    path = Path(path)

    dirs_out = {}

    for dir in path.iterdir():
        if dir.is_dir() and not dir.name.startswith('.'):
            dirs_out[dir.name] = list(dir.iterdir())

    return dirs_out



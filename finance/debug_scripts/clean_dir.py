# myfin/finance/debug_scripts/clean_dir.py

def clean_dir(dir_path, remove_self=False):
    """
    Removes all contents of a directory, and optionally the directory itself
    """

    print('clean_dir called with dir_path', dir_path)

    for f in dir_path.iterdir():
        if f.is_dir():
            clean_dir(f, remove_self=True)
        else:
            f.unlink()

    if remove_self:
        dir_path.rmdir()



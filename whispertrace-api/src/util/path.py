"""
Utility functions for working with file paths.
"""

import pathlib

from common.constants import DIR_RESOURCE


def get_resource_path(
    *children: str,
    ensure_parent_exists: bool = False,
) -> str:
    """
    Get the absolute path to a resource file or directory.

    Args:
        *children (str): Subdirectories or file names to append to the base resource path.

    Returns:
        str: The absolute path to the specified resource.
    """
    base_path = pathlib.Path(__file__).parent.parent.parent.resolve()
    resource_path = base_path / DIR_RESOURCE / pathlib.Path(*children)

    if ensure_parent_exists:
        ensure_dir(str(resource_path.parent))

    return str(resource_path.resolve())


def ensure_dir(path: str) -> None:
    """
    Ensure that a directory exists; create it if it doesn't.

    Args:
        path (str): The directory path to ensure.

    Returns:
        None
    """
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

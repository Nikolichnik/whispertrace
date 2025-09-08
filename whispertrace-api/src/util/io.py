"""
Utility functions for working with I/O.
"""

from logging import getLogger

import pathlib

from sklearn.metrics import roc_curve, auc

import numpy as np

import pandas as pd

import matplotlib
import matplotlib.pyplot as plt

from common.constants import ENCODING_UTF8, NEWLINE, MIA_THRESHOLD
from common.exception import ObjectNotFoundException

from util.path import get_resource_path, ensure_dir


logger = getLogger(__file__)


matplotlib.use("Agg")

# ANSI formatting codes
BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"


def get_resource_children(
    *children: str,
) -> list[str]:
    """
    Get names of all children in a resource directory.

    Args:
        *children (str): Subdirectories to append to the base resource path.

    Returns:
        list[str]: Names of all children in the specified directory.
    """
    dir_path = get_resource_path(*children)
    p = pathlib.Path(dir_path)

    if not p.exists() or not p.is_dir():
        return []

    return sorted([f.name for f in p.iterdir()])


def read_resource_file(
    *children: str,
    encoding: str = ENCODING_UTF8,
) -> str:
    """
    Read the contents of a resource file.

    Args:
        *children (str): Subdirectories or file names to append to the base resource path.
        encoding (str): The encoding to use when reading the file.

    Returns:
        str: The contents of the file.
    """
    file_path = get_resource_path(*children)

    try:
        return pathlib.Path(file_path).read_text(encoding=encoding)
    except (FileNotFoundError, UnicodeDecodeError, OSError) as e:
        logger.error("Error reading resource file '%s': %s", file_path, e)

        raise ObjectNotFoundException(
            f"Resource file '{file_path}' not found or unreadable.",
        ) from e


def write_resource_file(
    *children: str,
    content: str,
    encoding: str = ENCODING_UTF8,
) -> None:
    """
    Write content to a resource file, creating directories as needed.

    Args:
        *children (str): Subdirectories or file names to append to the base resource path.
        content (str): The content to write to the file.
        encoding (str): The encoding to use when writing the file.

    Returns:
        None
    """
    file_path = get_resource_path(*children)
    dir_path = str(pathlib.Path(file_path).parent)

    ensure_dir(dir_path)

    pathlib.Path(file_path).write_text(content, encoding=encoding)


def save_table(
    output_path: str,
    headers: list[str],
    rows: list[list[str]],
    padding: int = 1,
    max_column_width: int = 80,
) -> None:
    """
    Log a formatted table to the console.

    Args:
        output_path (str): Directory to save the formatted table file.
        headers (list[str]): The table headers.
        rows (list[list[str]]): The table rows.
        padding (int): Number of blank lines to log before and after the table.
        max_column_width (int): Maximum width of a table column.

    Returns:
        None
    """
    def truncate_text(text: str, max_width: int) -> str:
        """
        Truncate text to max_width, adding '...' if needed.

        Args:
            text (str): The text to truncate.
            max_width (int): The maximum allowed width.

        Returns:
            str: The truncated text.
        """
        if len(text) <= max_width:
            return text

        return text[:max_width - 3] + "..."

    def create_line(join_with: str, col_widths: list[int]) -> str:
        """
        Create a line of repeated characters for table borders.

        Args:
            join_with (str): The string to join the segments with.
            col_widths (list[int]): The widths of each column.

        Returns:
            str: The constructed line.
        """
        return join_with.join("─" * col_width for col_width in col_widths)

    # Ensure all rows have the same number of columns as headers
    num_columns = len(headers)
    normalized_rows = []
    for row in rows:
        # Pad row with empty strings if it's too short, or truncate if too long
        normalized_row = row[:num_columns] + [""] * (num_columns - len(row))
        normalized_rows.append(normalized_row)

    # Truncate all content first
    truncated_headers = [truncate_text(header, max_column_width) for header in headers]
    truncated_rows = [
        [truncate_text(str(item), max_column_width) for item in row]
        for row in normalized_rows
    ]

    # Calculate column widths based on truncated content
    col_widths = [
        max(len(str(item)) for item in col) 
        for col in zip(*([truncated_headers] + truncated_rows))
    ]

    header_line = " │ ".join(f"{header:<{col_widths[i]}}" for i, header in enumerate(truncated_headers))

    output_lines = []

    for _ in range(padding):
        output_lines.append(NEWLINE)

    output_lines.append(create_line("─┬─", col_widths))
    output_lines.append(header_line)
    output_lines.append(create_line("─┼─", col_widths))

    for row in truncated_rows:
        row_line = " │ ".join(f"{str(item):<{col_widths[i]}}" for i, item in enumerate(row))
        output_lines.append(row_line.strip())

    output_lines.append(create_line("─┴─", col_widths))

    for _ in range(padding):
        output_lines.append(NEWLINE)

    output = NEWLINE.join(output_lines)

    logger.info(output)

    write_resource_file(
        output_path,
        content=output.replace(BOLD, "").replace(RED, "").replace(RESET, ""),
    )


def save_csv_table(
    csv_path: str,
    output_path: str,
    separator: str = ",",
    max_column_width: int = 80,
    percentage_columns: list[str] = None,
    highlight_threshold: float = MIA_THRESHOLD,
) -> None:
    """
    Log a CSV file as a formatted table to the console using pandas.

    Args:
        csv_path (str): The path to the CSV file.
        output_path (str): Directory to save the formatted CSV file.
        separator (str): The delimiter used in the CSV file.
        max_column_width (int): Maximum width of a table column.
        percentage_columns (list[str]): Column names to format as percentages for display.
        highlight_threshold (float): Threshold for highlighting percentage values.

    Returns:
        None
    """

    def highlight_percentage(value: float, threshold: float) -> str:
        """
        Apply color highlighting to percentage values above threshold.

        Args:
            value (float): The percentage value.
            threshold (float): The threshold for highlighting.

        Returns:
            str: The formatted (and possibly highlighted) percentage string.
        """
        formatted_value = f"{value:.1f}"

        if value >= threshold:
            return f"{BOLD}{RED}{formatted_value}{RESET}"

        return formatted_value

    try:
        # Read CSV with pandas
        df = pd.read_csv(get_resource_path(csv_path), sep=separator)

        if df.empty:
            logger.info("No data to display.")

            return

        # Create a copy for display formatting (don't modify original)
        display_df = df.copy()

        # Format specified columns as percentages
        if percentage_columns:
            for col in percentage_columns:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(
                        lambda x: highlight_percentage(x * 100, highlight_threshold * 100)
                    )

        # Convert to the format expected by log_table
        headers = []

        for col in display_df.columns:
            header = str(col).strip().capitalize().replace("_", " ")

            # Add [%] suffix to percentage column headers
            if percentage_columns and col in percentage_columns:
                header += " [%]"

            headers.append(header)

        rows = [
            [str(item) for item in row]
            for row in display_df.values
        ]

        save_table(
            output_path=output_path,
            headers=headers,
            rows=rows,
            max_column_width=max_column_width,
        )

    except FileNotFoundError:
        logger.error("Error: File '%1s' not found.", csv_path)
    except pd.errors.EmptyDataError:
        logger.error("Error: The CSV file is empty.")
    except pd.errors.ParserError as e:
        logger.error("Error parsing CSV file: %1s", e)


def save_plots(
    train_losses: np.ndarray,
    held_losses: np.ndarray,
    y_true: np.ndarray,
    scores: np.ndarray,
    output_dir: str,
) -> None:
    """
    Save plots for loss distributions and ROC curve.

    Args:
        train_losses (np.ndarray): Losses for training (member) data.
        held_losses (np.ndarray): Losses for held-out (non-member) data.
        y_true (np.ndarray): True membership labels.
        scores (np.ndarray): Membership scores.
        output_path (str): Directory to save the plots.

    Returns:
        None
    """

    plot_dir = f"{output_dir}/plot"
    ensure_dir(plot_dir)
    plot_dir_name = f"{output_dir.split('/')[-1]}/plot"

    # Plot histograms of losses
    plt.figure(figsize=(6,4))
    plt.hist(train_losses, bins=30, alpha=0.6, label="Members (train)")
    plt.hist(held_losses, bins=30, alpha=0.6, label="Non-members (held-out)")
    plt.xlabel("Per-sequence loss")
    plt.ylabel("Count")
    plt.title("Membership inference: loss distributions")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{plot_dir}/loss_histogram.png")
    plt.close()

    # ROC curve
    fpr, tpr, _ = roc_curve(y_true, scores)
    roc_auc = auc(fpr, tpr)

    plt.figure(figsize=(5, 5))
    plt.plot(fpr, tpr, label=f"ROC curve (AUC = {roc_auc:.3f})")
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Membership inference ROC")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{plot_dir}/roc_curve.png")
    plt.close()

    logger.debug("Histogram and ROC plots available in %1s.", plot_dir_name)

"""
Checkpoint domain model.
"""

from dataclasses import dataclass

from typing import Optional


@dataclass
class Checkpoint:
    """
    Represents a model checkpoint.
    """

    name: str
    corpus: str
    epochs: Optional[int] = 100
    batch_size: Optional[int] = 64
    learning_rate: Optional[float] = 2e-3

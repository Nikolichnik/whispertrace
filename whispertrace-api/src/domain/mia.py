"""
This module contains the Membership Inference Attack (MIA) domain logic.
"""

from dataclasses import dataclass

from typing import Optional


@dataclass
class Sentence:
    """
    Domain model for sentences used in Membership Inference Attacks (MIA).
    """

    content: str
    score: Optional[float] = None
    normalized_score: Optional[float] = None
    is_member: Optional[bool] = None

    def dict(self):
        return {
            "content": self.content,
            "is_member": self.is_member,
            "score": self.score,
            "normalized_score": self.normalized_score,
        }


@dataclass
class Mia:
    """
    Domain model for Membership Inference Attack (MIA) results.
    """

    checkpoint: str
    corpus: str
    batch_size: int
    auc: Optional[float] = None
    input: Optional[str] = None
    timestamp: Optional[str] = None
    sentences: Optional[list[Sentence]] = None

"""
Domain models for the Corpus API.
"""

from dataclasses import dataclass

from typing import Optional


@dataclass
class Corpus:
    """
    Represents a corpus in the system.
    """

    name: str
    content: Optional[str] = None


@dataclass
class SyntheticCorpus(Corpus):
    """
    Represents a synthetic corpus.
    """
    n: Optional[int] = None


@dataclass
class WebScrapedCorpus(Corpus):
    """
    Represents a corpus built from web scraping.
    """

    url: Optional[str] = None

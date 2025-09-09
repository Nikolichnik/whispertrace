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
    n: Optional[int] = None
    url: Optional[str] = None
    content: Optional[str] = None


@dataclass
class SyntheticCorpus(Corpus):
    """
    Represents a synthetic corpus.
    """


@dataclass
class WebScrapedCorpus(Corpus):
    """
    Represents a corpus built from web scraping.
    """

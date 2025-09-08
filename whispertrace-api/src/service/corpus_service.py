"""
Service layer for managing corpora.
"""

from logging import getLogger

import random

import re

import requests

from bs4 import BeautifulSoup

from common.constants import (
    NEWLINE,
    DIR_CORPORA,
    EXTENSION_TXT,
)
from common.exception import WebScrapingException

from domain.corpus import Corpus, SyntheticCorpus, WebScrapedCorpus

from util.io import write_resource_file, read_resource_file, get_resource_children


random.seed(7)

logger = getLogger(__file__)


# pylint: disable=line-too-long
SUBJECTS = ["Alice", "Bob", "Carol", "Dave", "Eve", "Mallory", "Peggy", "Trent", "Victor", "Walter"]
VERBS = ["paints", "writes", "composes", "sketches", "records", "designs", "curates", "edits", "crafts", "imagines"]
OBJECTS = ["portraits", "stories", "poems", "melodies", "landscapes", "comics", "scenes", "lyrics", "haikus", "essays"]
STYLES = ["in watercolor", "in oil", "in charcoal", "with synths", "in pastel", "with ink", "in pencil", "with strings"]
CONTEXT = ["at dawn", "at night", "on weekends", "in spring", "by the river", "on stage", "in the studio", "in Vienna"]


class CorpusService:
    """
    Service class for managing corpora.
    """

    def create(
        self,
        corpus: Corpus,
    ) -> Corpus:
        """
        Create a new corpus based on the provided configuration.

        Args:
            corpus (Corpus): The corpus configuration.

        Returns:
            Corpus: The created corpus object.
        """
        logger.debug("Creating corpus of type: %s", type(corpus).__name__)

        if isinstance(corpus, SyntheticCorpus):
            content = self._get_synthetic_corpus_content(
                n=corpus.n,
            )
        elif isinstance(corpus, WebScrapedCorpus):
            content = self._get_web_scraped_corpus_content(
                url=corpus.url,
            )
        else:
            raise ValueError("Unsupported corpus type.")

        corpus.content = content

        self._write_corpus_to_file(
            corpus=corpus,
        )

        logger.debug("Corpus created successfully.")

        return corpus

    def get_all(self) -> list[Corpus]:
        """
        Retrieve a list of all available corpora.

        Returns:
            list[Corpus]: List of available corpora.
        """
        logger.debug("Retrieving list of available corpora...")

        corpora_file_names = get_resource_children(DIR_CORPORA)
        corpora = [
            Corpus(
                name=corpora_file_name.split(".")[0],
                content=read_resource_file(DIR_CORPORA, corpora_file_name),
            ) for corpora_file_name in corpora_file_names
        ]

        logger.debug("Retrieved %d corpora.", len(corpora))

        return corpora

    def _make_sentence(self) -> str:
        """
        Generate a random sentence.

        Returns:
            str: A randomly constructed sentence.
        """
        s = random.choice(SUBJECTS)
        v = random.choice(VERBS)
        o = random.choice(OBJECTS)
        st = random.choice(STYLES)
        c = random.choice(CONTEXT)

        return f"{s} {v} {o} {st} {c}."

    def _get_synthetic_corpus_content(
        self,
        n: int = 2000,
    ) -> str:
        """
        Generate synthetic corpus content.

        Args:
            n (int): The number of sentences in the corpus.

        Returns:
            str: Generated synthetic corpus content.
        """
        logger.debug("Generating synthetic corpus content with %d sentences...", n)

        sentences = [self._make_sentence() for _ in range(n)]
        content = NEWLINE.join(sentences)

        logger.debug("Synthetic corpus content created successfully.")

        return content

    def _get_web_scraped_corpus_content(
        self,
        url: str,
    ) -> str:
        """
        Generate web-scraped corpus content.

        Args:
            url (str): URL to scrape the content from.

        Returns:
            str: Generated web-scraped corpus content.

        Raises:
            WebScrapingException: If there is an error during web scraping.
        """
        logger.debug("Generating web-scraped corpus content from URL: %s", url)

        try:
            web_content = self._scrape_web_content(url)
            sentences = self._text_to_sentences(web_content)
            content = NEWLINE.join(sentences)

            logger.debug("Web-scraped content of %d sentences generated successfully.", len(sentences))

            return content
        except WebScrapingException as e:
            logger.error("Error scraping web content: %s", e)

            raise e

    def _scrape_web_content(self, url: str) -> str:
        """
        Scrape text content from a web page.

        Args:
            url (str): The URL to scrape.

        Returns:
            str: The extracted text content.
        
        Raises:
            requests.RequestException: If the web request fails.
            Exception: If content extraction fails.
        """
        try:
            # Add headers to avoid being blocked by some websites
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text_elements = soup.find_all(["p", "article", "section", "div", "h1", "h2", "h3", "h4", "h5", "h6"])
            text_content = []

            for element in text_elements:
                text = element.get_text().strip()

                if text and len(text) > 10:  # Filter out very short text snippets
                    text_content.append(text)

            if not text_content:
                # Fallback: get all text if no specific elements found
                text_content = [soup.get_text().strip()]

            full_text = " ".join(text_content)
            full_text = re.sub(r"\s+", " ", full_text)
            full_text = re.sub(r"\n+", NEWLINE, full_text)

            return full_text.strip()

        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch content from {url}: {e}")
        except Exception as e:
            raise WebScrapingException(f"Failed to extract content from {url}: {e}") from e

    def _text_to_sentences(self, text: str) -> list[str]:
        """
        Convert text into individual sentences.

        Args:
            text (str): The input text.

        Returns:
            list[str]: List of sentences.
        """
        # Split on sentence-ending punctuation
        sentences = re.split(r"[.!?]+", text)
        cleaned_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()

            # Filter out very short or very long sentences
            if 10 <= len(sentence) <= 300:
                cleaned_sentences.append(sentence + ".")

        return cleaned_sentences

    def _write_corpus_to_file(
        self,
        corpus: Corpus,
    ) -> None:
        """
        Write the corpus to a text file.

        Args:
            corpus (Corpus): The corpus object.
        """
        logger.debug("Writing corpus '%s' to file...", corpus.name)

        write_resource_file(
            DIR_CORPORA,
            f"{corpus.name}{EXTENSION_TXT}",
            content=corpus.content,
        )

        logger.debug("Corpus written to file successfully.")

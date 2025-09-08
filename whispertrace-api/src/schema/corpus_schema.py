"""
Schema definitions for the Corpus API.
"""

from marshmallow import EXCLUDE, Schema, fields, validate


class CorpusSchema(Schema):
    """
    Schema for a corpus.
    """

    class Meta:
        """
        Provide metadata for the enclosing class.

        Attributes:
            unknown: Specifies the behavior when encountering unknown fields.
        """

        unknown = EXCLUDE

    name = fields.String(
        metadata={
            "title": "Name",
            "description": "Name of the corpus. Will be used as a prefix to system-defined name.",
        },
        required=False,
    )
    content = fields.String(
        metadata={
            "title": "Content",
            "description": "The actual content of the corpus as a single string.",
        },
        required=False,
    )


class SyntheticCorpusSchema(CorpusSchema):
    """
    Schema for a synthetic corpus.
    """

    n = fields.Integer(
        metadata={
            "title": "Number of Sentences",
            "description": "Number of sentences in the corpus.",
        },
        validate=validate.Range(min=1, max=10000),
        required=True,
    )


class WebScrapedCorpusSchema(CorpusSchema):
    """
    Schema for a web-scraped corpus.
    """

    url = fields.String(
        metadata={
            "title": "URL",
            "description": "URL to scrape the content from."
        },
        required=True,
    )

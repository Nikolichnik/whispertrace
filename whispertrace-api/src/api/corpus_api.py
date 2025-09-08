"""
This module contains the Corpus API Blueprint.
"""

from logging import getLogger

from flask.views import MethodView

from flask_smorest import Blueprint

from common.constants import (
    APPLICATION_JSON,
    JSON,
    KEY_N,
    KEY_NAME,
    KEY_URL,
    CORPUS_NAME_SYNTHETIC,
    CORPUS_NAME_WEB,
)
from common.exception import ObjectNotFoundException

from schema.corpus_schema import CorpusSchema, SyntheticCorpusSchema, WebScrapedCorpusSchema

from domain.corpus import Corpus, SyntheticCorpus, WebScrapedCorpus

from service.corpus_service import CorpusService

from util.api import handle_exception_impl


logger = getLogger(__file__)

corpus_blueprint = Blueprint(
    "corpora", __name__, url_prefix="/corpora", description="Corpus API"
)


@corpus_blueprint.route("")
class CorpusApi(MethodView):
    """
    Define /corpora endpoint.
    """

    corpus_list_response_example = [
        {
            "name": "custom_corpus_name",
            "content": "This is the content of the corpus.",
        }
    ]

    @corpus_blueprint.response(
        status_code=200,
        schema=CorpusSchema(many=True),
        content_type=APPLICATION_JSON,
        description="List of available corpora.",
        example=corpus_list_response_example,
    )
    def get(self) -> list[Corpus]:
        """
        Retrieve a list of all available corpora.

        Use this endpoint to get a list of all available corpora.
        """
        logger.debug("Retrieving list of available corpora...")

        return CorpusService().get_all()


@corpus_blueprint.route("/synthetic")
class SyntheticCorpusApi(MethodView):
    """
    Define /corpora endpoint
    """

    synthetic_corpus_create_example = {
        "name": "custom_corpus_name",
        "n": 100,
    }

    synthetic_corpus_create_response_example = {
        "name": "custom_corpus_name",
        "n": 100,
        "content": "This is the content of the corpus.",
    }

    @corpus_blueprint.arguments(
        schema=SyntheticCorpusSchema(
            only=("name", "n")
        ),
        location=JSON,
        description="Corpus creation data.",
        example=synthetic_corpus_create_example,
    )
    @corpus_blueprint.response(
        status_code=201,
        schema=SyntheticCorpusSchema,
        content_type=APPLICATION_JSON,
        description="Information about the created corpus.",
        example=synthetic_corpus_create_response_example,
    )
    def post(self, corpus_data: dict) -> SyntheticCorpus:
        """
        Create a new corpus.

        Use this endpoint to create a new corpus by generating a set of sentences through randomized procedure.
        """
        logger.debug("Creating new synthetic corpus...")

        n = int(corpus_data.get(KEY_N))

        corpus_to_create = SyntheticCorpus(
            name=f"{corpus_data.get(KEY_NAME, CORPUS_NAME_SYNTHETIC)}_{n}",
            n=n,
        )

        return CorpusService().create(
            corpus=corpus_to_create
        )


@corpus_blueprint.route("/web")
class WebScrapedCorpusApi(MethodView):
    """
    Define /corpora endpoint
    """

    web_scraped_corpus_create_example = {
        "name": "custom_corpus_name",
        "url": "https://en.wikipedia.org/wiki/Landau%E2%80%93Lifshitz%E2%80%93Gilbert_equation",
    }

    web_scraped_corpus_create_response_example = {
        "name": "custom_corpus_name",
        "url": "https://en.wikipedia.org/wiki/Landau%E2%80%93Lifshitz%E2%80%93Gilbert_equation",
        "content": "This is the content of the corpus.",
    }

    @corpus_blueprint.arguments(
        schema=WebScrapedCorpusSchema(
            only=("name", "url")
        ),
        location=JSON,
        description="Corpus creation instructions.",
        example=web_scraped_corpus_create_example,
    )
    @corpus_blueprint.response(
        status_code=201,
        schema=WebScrapedCorpusSchema,
        content_type=APPLICATION_JSON,
        description="Information about the created corpus.",
        example=web_scraped_corpus_create_response_example,
    )
    def post(self, corpus_data: dict) -> WebScrapedCorpus:
        """
        Create a new web-scraped corpus.

        Use this endpoint to create a new corpus by scraping text content from a specified URL.
        """
        logger.debug("Creating new web scraped corpus...")

        corpus_to_create = WebScrapedCorpus(
            name=corpus_data.get(KEY_NAME, CORPUS_NAME_WEB),
            url=corpus_data.get(KEY_URL),
        )

        return CorpusService().create(
            corpus=corpus_to_create
        )


@corpus_blueprint.errorhandler(ObjectNotFoundException)
def handle_exception(exception: Exception) -> tuple[dict, int]:
    """
    Handle exceptions thrown during execution.

    Args:
        exception (Exception): The exception that was thrown.

    Returns:
        tuple[dict, int]: The error response and the HTTP status code.
    """
    return handle_exception_impl(
        exception=exception,
        logger=logger,
    )

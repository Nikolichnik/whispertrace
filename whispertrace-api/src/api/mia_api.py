"""
This module contains the Membership Inference Attack (MIA) API Blueprint.
"""

from logging import getLogger

from flask.views import MethodView

from flask_smorest import Blueprint

from common.constants import (
    APPLICATION_JSON,
    JSON,
)
from common.exception import ObjectNotFoundException

from schema.mia_schema import MiaSchema

from domain.mia import Mia

from service.mia_service import MiaService

from util.api import handle_exception_impl


logger = getLogger(__file__)

mia_blueprint = Blueprint(
    "mia", __name__, url_prefix="/mia", description="Membership Inference Attack (MIA) API"
)


@mia_blueprint.route("")
class MiaApi(MethodView):
    """
    Define /mia endpoint.
    """

    mia_request_example = {
        "checkpoint": "synthetic_2000__100__5__64__0.002",
        "corpus": "synthetic_2000",
        "batch_size": 64,
        "input": "This is a sample sentence for MIA.",
    }

    mia_response_example = {
        "checkpoint": "synthetic_2000__100__5__64__0.002",
        "corpus": "synthetic_2000",
        "batch_size": 64,
        "auc": 0.873,
        "input": "This is a sample sentence for MIA.",
        "sentences": [
            {
                "content": "This is a sample sentence for MIA.",
                "score": -12.345,
                "is_member": False,
            }
        ],
    }

    @mia_blueprint.arguments(
        MiaSchema,
        location=JSON,
        description="Checkpoint creation data.",
        example=mia_request_example,
    )
    @mia_blueprint.response(
        status_code=201,
        schema=MiaSchema,
        content_type=APPLICATION_JSON,
        description="Information about the created checkpoint.",
        example=mia_response_example,
    )
    def post(self, mia_data: dict) -> Mia:
        """
        Perform a new MIA.

        Args:
            mia_data (dict): The MIA data.

        Returns:
            Mia: The information about the newly performed MIA.
        """
        logger.debug("Performing new MIA with data: %s", mia_data)

        return MiaService().perform(
            mia=Mia(**mia_data)
        )

    @mia_blueprint.response(
        status_code=200,
        schema=MiaSchema(
            many=True,
            only=(
                "checkpoint",
                "corpus",
                "batch_size",
                "auc",
                "timestamp",
            )
        ),
        content_type=APPLICATION_JSON,
        description="Information about the performed MIAs.",
    )
    def get(self) -> Mia:
        """
        Get information about a specific MIA.

        Args:
            mia_id (str): The ID of the MIA.

        Returns:
            Mia: The information about the specified MIA.
        """
        logger.debug("Retrieving list of performed MIAs...")

        return MiaService().get_all()


@mia_blueprint.errorhandler(ObjectNotFoundException)
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

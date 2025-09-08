"""
This module contains the Checkpoint API Blueprint.
"""

from logging import getLogger

from flask.views import MethodView

from flask_smorest import Blueprint

from common.constants import (
    APPLICATION_JSON,
    JSON,
)
from common.exception import ObjectNotFoundException

from schema.checkpoint_schema import CheckpointSchema

from domain.checkpoint import Checkpoint

from service.checkpoint_service import CheckpointService

from util.api import handle_exception_impl


logger = getLogger(__file__)

checkpoint_blueprint = Blueprint(
    "checkpoints", __name__, url_prefix="/checkpoints", description="Checkpoint API"
)


@checkpoint_blueprint.route("")
class CheckpointApi(MethodView):
    """
    Define /checkpoints endpoint.
    """

    checkpoint_create_request_example = {
        "name": "custom_checkpoint_name",
        "corpus": "synthetic_2000",
        "epochs": 100,
    }

    checkpoint_create_response_example = {
        "name": "custom_checkpoint_name__synthetic_2000__100",
        "corpus": "synthetic_2000",
        "epochs": 100,
    }

    @checkpoint_blueprint.arguments(
        CheckpointSchema,
        location=JSON,
        description="Checkpoint creation data.",
        example=checkpoint_create_request_example,
    )
    @checkpoint_blueprint.response(
        status_code=201,
        schema=CheckpointSchema,
        content_type=APPLICATION_JSON,
        description="Information about the created checkpoint.",
        example=checkpoint_create_response_example,
    )
    def post(self, checkpoint_data: dict) -> Checkpoint:
        """
        Create a new checkpoint.

        Args:
            checkpoint_data (dict): The checkpoint data.

        Returns:
            Checkpoint: The created checkpoint.
        """
        logger.debug("Creating new checkpoint with data: %s", checkpoint_data)

        return CheckpointService().create(
            checkpoint=Checkpoint(**checkpoint_data)
        )

    checkpoint_list_response_example = [
        {
            "name": "synthetic_2000__100__5__64__0.002",
            "corpus": "100",
            "epochs": 5,
            "batch_size": 64,
            "learning_rate": 0.002,
        },
        {
            "name": "wiki_llg_equation__100__5__64__0.002",
            "corpus": "100",
            "epochs": 5,
            "batch_size": 64,
            "learning_rate": 0.002,
        }
    ]

    @checkpoint_blueprint.response(
        status_code=200,
        schema=CheckpointSchema(
            many=True,
        ),
        content_type=APPLICATION_JSON,
        description="List of available checkpoints.",
        example=checkpoint_list_response_example,
    )
    def get(self) -> list[Checkpoint]:
        """
        Retrieve a list of all available checkpoints.

        Use this endpoint to get a list of all available checkpoints.
        """
        logger.debug("Retrieving list of available checkpoints...")

        return CheckpointService().get_all()


@checkpoint_blueprint.errorhandler(ObjectNotFoundException)
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

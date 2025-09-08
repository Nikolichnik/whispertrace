"""
Checkpoint schema.
"""

from marshmallow import Schema, fields, validate


class CheckpointSchema(Schema):
    """
    Schema for a model checkpoint.
    """

    name = fields.String(
        metadata={
            "title": "Name",
            "description": "The name of the checkpoint."
        },
        required=True,
    )
    corpus = fields.String(
        metadata={
            "title": "Corpus",
            "description": "The name of the training corpus."
        },
        required=True,
    )
    epochs = fields.Int(
        metadata={
            "title": "Epochs",
            "description": "The number of training epochs."
        },
        validate=validate.Range(min=1, max=1000),
        required=True,
    )
    batch_size = fields.Int(
        metadata={
            "title": "Batch Size",
            "description": "The batch size for training."
        },
        validate=validate.Range(min=1, max=1024),
        required=False,
    )
    learning_rate = fields.Float(
        metadata={
            "title": "Learning Rate",
            "description": "The learning rate for the optimizer."
        },
        validate=validate.Range(min=1e-6, max=1.0),
        required=False,
    )

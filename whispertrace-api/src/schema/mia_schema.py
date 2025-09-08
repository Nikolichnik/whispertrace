"""
Schema for Membership Inference Attack (MIA) results.
"""

from marshmallow import Schema, fields


class SentenceSchema(Schema):
    """
    Schema for sentences used in Membership Inference Attacks (MIA).
    """

    content = fields.Str(
        metadata={
            "title": "Content",
            "description": "The content of the sentence.",
        },
        required=True,
    )
    score = fields.Float(
        metadata={
            "title": "Score",
            "description": "The score assigned to the sentence."
        },
        required=False,
    )
    normalized_score = fields.Float(
        metadata={
            "title": "Normalized Score",
            "description": "The normalized score of the sentence."
        },
        required=False,
    )
    is_member = fields.String(
        metadata={
            "title": "Is Member",
            "description": "Indicates if the sentence is a member of the training set."
        },
        required=False,
    )


class MiaSchema(Schema):
    """
    Schema for Membership Inference Attack (MIA) results.
    """

    checkpoint = fields.Str(
        metadata={
            "title": "Checkpoint",
            "description": "The name of the checkpoint used in the MIA.",
        },
        required=True,
    )
    corpus = fields.Str(
        metadata={
            "title": "Corpus",
            "description": "The corpus used for the MIA.",
        },
        required=True,
    )
    batch_size = fields.Int(
        metadata={
            "title": "Batch Size",
            "description": "The batch size used during the MIA.",
        },
        required=True,
    )
    auc = fields.Float(
        metadata={
            "title": "AUC",
            "description": "The Area Under the Curve (AUC) metric for the MIA results.",
        },
        required=False,
    )
    input = fields.Str(
        metadata={
            "title": "Input",
            "description": "The input data used for the MIA.",
        },
        required=False,
    )
    timestamp = fields.Str(
        metadata={
            "title": "Timestamp",
            "description": "The timestamp when the MIA was performed.",
        },
        required=False,
    )
    sentences = fields.List(
        fields.Nested(SentenceSchema),
        metadata={
            "title": "Sentences",
            "description": "List of sentences evaluated in the MIA.",
        },
        required=False,
    )

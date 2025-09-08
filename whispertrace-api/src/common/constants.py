"""
Common constants used throughout the codebase.
"""


# Environment variables
ENV_CORS_ORIGIN = "CORS_ORIGIN"

# Device types
DEVICE_CUDA = "cuda"
DEVICE_CPU = "cpu"

# Directories
DIR_RESOURCE = "resource"
DIR_CORPORA = "corpora"
DIR_CHECKPOINTS = "checkpoints"
DIR_MIAS = "mias"

# Keys
KEY_N = "n"
KEY_NAME = "name"
KEY_URL = "url"
KEY_MODEL = "model"
KEY_VOCAB = "vocab"

# Extensions
EXTENSION_TXT = ".txt"
EXTENSION_PT = ".pt"
EXTENSION_CSV = ".csv"

# Format strings
FORMAT_DATETIME = "%Y%m%d%H%M%S"
FORMAT_CHECKPOINT_NAME = "{name_prefix}{corpus}__{epochs}__{batch_size}__{learning_rate}"
FORMAT_MIA_DIR_NAME = "{datetime}__{checkpoint}__{corpus}__{batch_size}__{auc}"

# Default values
SPACER_DEFAULT = "__"
LOGO_DEFAULT = "shadow"
CORPUS_NAME_SYNTHETIC = "synthetic"
CORPUS_NAME_WEB = "web"

# Various
ENCODING_UTF8 = "utf-8"
NEWLINE = "\n"
JSON = "json"
APPLICATION_JSON = "application/json"
MIA_THRESHOLD = 0.7

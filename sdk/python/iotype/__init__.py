"""Official Python SDK for the iotype API.

Quickstart::

    from iotype import Iotype

    io = Iotype()                       # reads IOTYPE_TOKEN from the environment
    print(io.translate("سلام دنیا", "fa", "en"))
    print(io.ocr("contract.pdf", wait=True))
"""

from .client import Iotype
from .errors import (
    IotypeError,
    AuthenticationError,
    InsufficientTokensError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    ProcessingTimeout,
)
from .models import File, Process
from .realtime import RealtimeSession

__version__ = "1.0.0"

__all__ = [
    "Iotype",
    "RealtimeSession",
    "File",
    "Process",
    "IotypeError",
    "AuthenticationError",
    "InsufficientTokensError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "ProcessingTimeout",
    "__version__",
]

"""Official Python SDK for the iotype API.

Quickstart::

    from iotype import Iotype

    io = Iotype()                       # reads IOTYPE_TOKEN from the environment
    print(io.translate("سلام دنیا", "fa", "en"))
    print(io.ocr("contract.pdf", wait=True))
"""

from .client import Iotype
from .errors import (
    AuthenticationError,
    InsufficientTokensError,
    IotypeError,
    NotFoundError,
    ProcessingTimeout,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import File, Process
from .realtime import RealtimeSession

__version__ = "1.0.0"

__all__ = [
    "AuthenticationError",
    "File",
    "InsufficientTokensError",
    "Iotype",
    "IotypeError",
    "NotFoundError",
    "Process",
    "ProcessingTimeout",
    "RateLimitError",
    "RealtimeSession",
    "ServerError",
    "ValidationError",
    "__version__",
]

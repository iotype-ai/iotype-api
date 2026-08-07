<?php

declare(strict_types=1);

namespace Iotype;

/** HTTP 5xx — safe to retry with backoff. */
class ServerException extends IotypeException
{
}

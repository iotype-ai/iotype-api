<?php

declare(strict_types=1);

namespace Iotype;

/** HTTP 429 — too many requests. Status code inferred. */
class RateLimitException extends IotypeException
{
}

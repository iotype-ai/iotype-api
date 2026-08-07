<?php

declare(strict_types=1);

namespace Iotype;

/**
 * An asynchronous job did not finish within the deadline.
 *
 * The job is still running server-side. Keep the uuid and resume tracking
 * rather than re-uploading, which would be billed again.
 */
class ProcessingTimeoutException extends IotypeException
{
    public ?string $uuid;

    public function __construct(string $message, ?string $uuid = null)
    {
        parent::__construct($message);
        $this->uuid = $uuid;
    }
}

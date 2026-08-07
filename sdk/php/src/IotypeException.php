<?php

declare(strict_types=1);

namespace Iotype;

/** Base class for every error raised by this SDK. */
class IotypeException extends \RuntimeException
{
    public ?int $status;

    /** @var array<string, mixed>|null */
    public ?array $body;

    /** @param array<string, mixed>|null $body */
    public function __construct(string $message, ?int $status = null, ?array $body = null)
    {
        parent::__construct($status !== null ? "[{$status}] {$message}" : $message);
        $this->status = $status;
        $this->body   = $body;
    }
}

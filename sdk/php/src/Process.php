<?php

declare(strict_types=1);

namespace Iotype;

/** One unit of work running on an uploaded file. */
final class Process
{
    public ?string $type;

    /**
     * Not enumerated upstream. Do not branch on this — use result !== null as
     * the completion signal.
     */
    public ?string $status;

    public ?string $result;

    public function __construct(?string $type, ?string $status, ?string $result)
    {
        $this->type   = $type;
        $this->status = $status;
        $this->result = $result;
    }

    public function isDone(): bool
    {
        return $this->result !== null;
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        return new self(
            isset($data['type']) ? (string) $data['type'] : null,
            isset($data['status']) ? (string) $data['status'] : null,
            isset($data['result']) ? (string) $data['result'] : null
        );
    }
}

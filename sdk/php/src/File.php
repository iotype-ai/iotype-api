<?php

declare(strict_types=1);

namespace Iotype;

/** An uploaded file and the processes running on it. */
final class File
{
    public ?string $uuid;
    public ?string $name;
    public ?string $filename;

    /** @var list<Process> */
    public array $processes;

    /** @param list<Process> $processes */
    public function __construct(?string $uuid, ?string $name, ?string $filename, array $processes)
    {
        $this->uuid      = $uuid;
        $this->name      = $name;
        $this->filename  = $filename;
        $this->processes = $processes;
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        return new self(
            isset($data['uuid']) ? (string) $data['uuid'] : null,
            isset($data['name']) ? (string) $data['name'] : null,
            isset($data['filename']) ? (string) $data['filename'] : null,
            array_map(
                static fn (array $p): Process => Process::fromArray($p),
                $data['processes'] ?? []
            )
        );
    }

    /**
     * First finished result, optionally filtered by process type.
     *
     * Always match by type rather than by list position — when summarisation is
     * requested there is more than one process and the order is not guaranteed.
     */
    public function result(?string $processType = null): ?string
    {
        foreach ($this->processes as $process) {
            if ($processType !== null && $process->type !== $processType) {
                continue;
            }
            if ($process->isDone()) {
                return $process->result;
            }
        }

        return null;
    }

    /**
     * Every finished result, keyed by process type.
     *
     * @return array<string, string>
     */
    public function results(): array
    {
        $out = [];
        foreach ($this->processes as $i => $process) {
            if ($process->isDone() && $process->result !== null) {
                $out[$process->type ?? "process_{$i}"] = $process->result;
            }
        }

        return $out;
    }

    /** True when every process has produced a result. */
    public function isDone(): bool
    {
        if ($this->processes === []) {
            return false;
        }
        foreach ($this->processes as $process) {
            if (!$process->isDone()) {
                return false;
            }
        }

        return true;
    }
}

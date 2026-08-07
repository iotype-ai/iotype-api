<?php
// IOTYPE_TOKEN=... php examples/ocr_and_wait.php contract.pdf

declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

use Iotype\Client;
use Iotype\ProcessingTimeoutException;

$path = $argv[1] ?? null;
if ($path === null) {
    fwrite(STDERR, "usage: ocr_and_wait.php <file.pdf|file.jpg>\n");
    exit(1);
}

$io = new Client();

$file = $io->ocr($path, true);
echo "uuid: {$file->uuid}  (store this — you can resume tracking after a restart)\n";

try {
    $text = $io->waitFor($file->uuid, 'ocr', 1800);
} catch (ProcessingTimeoutException $e) {
    echo "still processing; resume later with waitFor('{$e->uuid}')\n";
    exit(0);
}

echo "\n--- extracted text ---\n{$text}\n";

$summary = $io->track($file->uuid)->result('summarize');
if ($summary !== null) {
    echo "\n--- summary ---\n{$summary}\n";
}

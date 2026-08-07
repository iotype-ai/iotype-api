<?php
// IOTYPE_TOKEN=... php examples/quickstart.php

declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

use Iotype\Client;
use Iotype\IotypeException;

try {
    $io = new Client();

    echo 'translate: ' . $io->translate('سلام! امروز هوا بسیار عالی است.', 'fa', 'en') . PHP_EOL;

    $url = $io->synthesize('سلام دنیا', 'tanaz');
    echo 'synthesize: ' . $url . PHP_EOL;
    if ($url !== '') {
        $io->download($url, 'narration.mp3');
        echo 'saved -> narration.mp3' . PHP_EOL;
    }

    $files = $io->files();
    echo 'files: ' . count($files) . ' submitted' . PHP_EOL;
    foreach (array_slice($files, 0, 5) as $file) {
        printf("  %s  %s  done=%s\n", $file->uuid, $file->filename, $file->isDone() ? 'yes' : 'no');
    }
} catch (IotypeException $e) {
    fwrite(STDERR, 'iotype error: ' . $e->getMessage() . PHP_EOL);
    exit(1);
}

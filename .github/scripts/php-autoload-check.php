<?php

/**
 * Smoke test for the root composer manifest.
 *
 * composer.json lives at the repository root, not in sdk/php, because
 * Packagist only reads the root file. That makes the PSR-4 mapping
 * (Iotype\ -> sdk/php/src/) easy to get wrong and easy to break silently, so
 * CI runs this after `composer install`.
 *
 * It lives in a file rather than inline `php -r '...'` on purpose: a namespace
 * separator inside a shell-quoted one-liner is a backslash-escaping trap, and
 * getting it wrong yields a bare "exit code 254" with no explanation.
 *
 * Run from the repository root:  php .github/scripts/php-autoload-check.php
 */

declare(strict_types=1);

$autoload = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoload)) {
    fwrite(STDERR, "vendor/autoload.php not found. Run `composer install` first.\n");
    exit(1);
}

require $autoload;

$expected = [
    Iotype\Client::class,
    Iotype\File::class,
    Iotype\Process::class,
    Iotype\Errors::class,
    Iotype\RealtimeSession::class,
    Iotype\IotypeException::class,
    Iotype\AuthenticationException::class,
    Iotype\ProcessingTimeoutException::class,
    Iotype\RealtimeException::class,
];

$missing = [];
foreach ($expected as $class) {
    if (!class_exists($class)) {
        $missing[] = $class;
    }
}

if ($missing !== []) {
    fwrite(STDERR, "PSR-4 autoloading failed for:\n  " . implode("\n  ", $missing) . "\n");
    fwrite(STDERR, "Check the autoload.psr-4 mapping in the root composer.json.\n");
    exit(1);
}

// The constructor must not touch the network, so this is safe in CI.
$client = new Iotype\Client('test-token');

if (!$client instanceof Iotype\Client) {
    fwrite(STDERR, "Iotype\\Client did not instantiate.\n");
    exit(1);
}

// A bad token must be rejected up front rather than at request time.
try {
    new Iotype\Client('');
    fwrite(STDERR, "An empty token should have been rejected.\n");
    exit(1);
} catch (Iotype\IotypeException $e) {
    // expected
}

printf("autoload OK — %d classes resolved from sdk/php/src/\n", count($expected));

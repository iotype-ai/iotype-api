<?php

declare(strict_types=1);

namespace Iotype;

final class Errors
{
    /**
     * Translate an HTTP status into the matching exception.
     *
     * Only 401 is documented upstream; the rest are inferred and may change.
     *
     * @param array<string, mixed>|null $body
     *
     * @throws IotypeException
     */
    public static function raiseForStatus(int $status, ?array $body, string $text): void
    {
        if ($status >= 200 && $status < 300) {
            return;
        }

        $message = substr($text, 0, 500);
        if ($body !== null) {
            $message = (string) ($body['message'] ?? $body['error'] ?? $message);
        }

        if ($status >= 500) {
            throw new ServerException($message, $status, $body);
        }

        switch ($status) {
            case 401:
                throw new AuthenticationException(
                    $message . ' — the token is missing, malformed, expired, or its balance is exhausted.',
                    $status,
                    $body
                );
            case 402: throw new InsufficientTokensException($message, $status, $body);
            case 404: throw new NotFoundException($message, $status, $body);
            case 413: throw new PayloadTooLargeException($message, $status, $body);
            case 422: throw new ValidationException($message, $status, $body);
            case 429: throw new RateLimitException($message, $status, $body);
            default:  throw new IotypeException($message, $status, $body);
        }
    }
}

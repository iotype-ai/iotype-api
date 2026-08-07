<?php

declare(strict_types=1);

namespace Iotype;

/**
 * Official PHP client for the iotype API.
 *
 * ```php
 * $io = new \Iotype\Client();          // reads IOTYPE_TOKEN
 * echo $io->translate('سلام دنیا', 'fa', 'en');
 * ```
 */
final class Client
{
    public const DEFAULT_BASE_URL = 'https://iotype.com';

    /** @var list<string> */
    public const SPEAKERS = [
        'behrooz', 'mehran', 'farshid', 'sara', 'mitra', 'siavash',
        'shirin', 'kaveh', 'amir', 'tanaz', 'mahsa',
    ];

    /** @var list<string> */
    public const LANGUAGES = ['fa', 'en', 'ar'];

    /** @var list<int> */
    private const RETRY_STATUSES = [408, 429, 500, 502, 503, 504];

    private string $token;
    private string $baseUrl;
    private int $timeout;
    private int $maxRetries;

    /**
     * @param string|null $token   Falls back to $_ENV['IOTYPE_TOKEN'] / getenv().
     * @param string|null $baseUrl Falls back to IOTYPE_BASE_URL, then the default.
     * @param int         $timeout Per-request timeout in seconds.
     *
     * @throws IotypeException when no token is available.
     */
    public function __construct(
        ?string $token = null,
        ?string $baseUrl = null,
        int $timeout = 120,
        int $maxRetries = 3
    ) {
        $this->token = $token ?? (getenv('IOTYPE_TOKEN') ?: '');
        if ($this->token === '') {
            throw new IotypeException(
                'No token. Pass one to the constructor or set IOTYPE_TOKEN. '
                . 'Generate one at https://iotype.com/api-service/authentication'
            );
        }

        $this->baseUrl    = rtrim($baseUrl ?? (getenv('IOTYPE_BASE_URL') ?: self::DEFAULT_BASE_URL), '/');
        $this->timeout    = $timeout;
        $this->maxRetries = $maxRetries;
    }

    // ------------------------------------------------------------ synchronous

    /**
     * Translate text between fa / en / ar.
     *
     * @throws IotypeException
     */
    public function translate(string $text, string $sourceLang, string $destinationLang): string
    {
        $this->assertIn($sourceLang, self::LANGUAGES, 'source_lang');
        $this->assertIn($destinationLang, self::LANGUAGES, 'destination_lang');

        $body = $this->requestJson('/io/v1/translate', [
            'source_lang'      => $sourceLang,
            'destination_lang' => $destinationLang,
            'text'             => $text,
        ], 30);

        return (string) ($body['result'] ?? '');
    }

    /**
     * Generate speech from text. Returns the URL of the resulting MP3.
     *
     * Retention of generated files is not published upstream — download it if
     * you need it long-term.
     *
     * @throws IotypeException
     */
    public function synthesize(string $text, string $speaker = 'tanaz', string $tone = 'general'): string
    {
        $this->assertIn($speaker, self::SPEAKERS, 'speaker');
        $this->assertIn($tone, ['general', 'formal'], 'tone');

        $body = $this->requestJson('/io/v1/synthesis', [
            'tone'    => $tone,
            'speaker' => $speaker,
            'text'    => $text,
        ], 60);

        return (string) ($body['url'] ?? '');
    }

    /**
     * Transcribe a short MP3 synchronously.
     *
     * For long recordings use {@see transcribe()}, which is slower but more accurate.
     *
     * @throws IotypeException
     */
    public function transcribeInstant(string $path): string
    {
        $body = $this->requestMultipart('/io/v1/transcribe/instant', $path, []);

        return (string) ($body['result'] ?? '');
    }

    // ----------------------------------------------------------- asynchronous

    /**
     * Transcribe an MP3 with high accuracy. **Asynchronous.**
     *
     * Returns a {@see File}. Pass $wait = true to poll until the transcript is
     * ready and receive the text directly instead.
     *
     * @return File|string
     *
     * @throws IotypeException
     */
    public function transcribe(
        string $path,
        bool $summarize = false,
        ?string $sourceLang = null,
        bool $wait = false,
        int $timeout = 1800
    ) {
        $fields = ['should_summarize' => $summarize ? 'true' : 'false'];
        if ($sourceLang !== null) {
            $this->assertIn($sourceLang, self::LANGUAGES, 'source_lang');
            $fields['source_lang'] = $sourceLang;
        }

        $body = $this->requestMultipart('/io/v1/transcribe', $path, $fields);
        $file = File::fromArray($body['file'] ?? []);

        return $wait ? $this->waitFor($file->uuid, 'transcribe', $timeout) : $file;
    }

    /**
     * Extract text from a PDF or JPG. **Asynchronous.**
     *
     * @return File|string
     *
     * @throws IotypeException
     */
    public function ocr(string $path, bool $summarize = false, bool $wait = false, int $timeout = 1800)
    {
        $body = $this->requestMultipart('/io/v1/ocr', $path, [
            'should_summarize' => $summarize ? 'true' : 'false',
        ]);
        $file = File::fromArray($body['file'] ?? []);

        return $wait ? $this->waitFor($file->uuid, 'ocr', $timeout) : $file;
    }

    // ------------------------------------------------------------------ files

    /**
     * List every file submitted with this token.
     *
     * @return list<File>
     *
     * @throws IotypeException
     */
    public function files(): array
    {
        $body = $this->requestJson('/io/v1/files', [], 30);

        return array_map(
            static fn (array $f): File => File::fromArray($f),
            $body['files'] ?? []
        );
    }

    /**
     * Fetch the current state of one file.
     *
     * @throws IotypeException
     */
    public function track(string $uuid): File
    {
        $body = $this->requestJson('/io/v1/file/track', ['uuid' => $uuid], 30);

        return File::fromArray($body['file'] ?? []);
    }

    /**
     * Poll $uuid until a process carries a result, then return it.
     *
     * Backoff starts at 5s and doubles to a 60s ceiling. Completion is detected
     * by result !== null, not by status — the status vocabulary is not published
     * upstream.
     *
     * @throws ProcessingTimeoutException when the deadline passes. The job keeps
     *         running server-side; resume with the same uuid rather than
     *         re-uploading, which would be billed again.
     * @throws IotypeException
     */
    public function waitFor(
        ?string $uuid,
        ?string $processType = null,
        int $timeout = 1800,
        int $initialInterval = 5,
        int $maxInterval = 60
    ): string {
        if ($uuid === null || $uuid === '') {
            throw new IotypeException('No uuid to track — the upload response had no file.uuid.');
        }

        $deadline = time() + $timeout;
        $interval = $initialInterval;

        while (true) {
            $result = $this->track($uuid)->result($processType);
            if ($result !== null) {
                return $result;
            }

            if (time() >= $deadline) {
                throw new ProcessingTimeoutException(
                    sprintf(
                        'File %s did not finish within %ds. It is still processing — '
                        . 'resume with waitFor() rather than re-uploading.',
                        $uuid,
                        $timeout
                    ),
                    $uuid
                );
            }

            sleep(min($interval, max(1, $deadline - time())));
            $interval = min($interval * 2, $maxInterval);
        }
    }

    /**
     * Open a realtime ASR session.
     *
     * Defaults to access_token because this SDK runs server-side. Never ship an
     * access token to a browser or mobile client — mint a Flash Token instead.
     */
    public function realtime(
        string $model = 'io-fa',
        ?string $token = null,
        string $tokenType = 'access_token'
    ): RealtimeSession {
        return new RealtimeSession(
            str_replace(['https://', 'http://'], ['wss://', 'ws://'], $this->baseUrl) . '/socket/realtime',
            $token ?? $this->token,
            $tokenType,
            $model
        );
    }

    /**
     * Download a generated file, e.g. the MP3 returned by {@see synthesize()}.
     *
     * @throws IotypeException
     */
    public function download(string $url, string $destination): string
    {
        $in = @fopen($url, 'rb');
        if ($in === false) {
            throw new IotypeException("Could not open {$url}");
        }
        $out = fopen($destination, 'wb');
        stream_copy_to_stream($in, $out);
        fclose($in);
        fclose($out);

        return $destination;
    }

    // -------------------------------------------------------------- internals

    /**
     * @param array<string, mixed> $payload
     *
     * @return array<string, mixed>
     *
     * @throws IotypeException
     */
    private function requestJson(string $path, array $payload, ?int $timeout = null): array
    {
        return $this->send($path, [
            CURLOPT_POST       => true,
            CURLOPT_POSTFIELDS => json_encode($payload, JSON_UNESCAPED_UNICODE) ?: '{}',
            CURLOPT_HTTPHEADER => $this->headers(true),
        ], $timeout);
    }

    /**
     * @param array<string, string> $fields
     *
     * @return array<string, mixed>
     *
     * @throws IotypeException
     */
    private function requestMultipart(string $path, string $filePath, array $fields, ?int $timeout = null): array
    {
        if (!is_file($filePath)) {
            throw new IotypeException("File not found: {$filePath}");
        }

        // Note: no Content-Type header — cURL sets it with the multipart boundary.
        $post = $fields + ['file' => new \CURLFile($filePath, '', basename($filePath))];

        return $this->send($path, [
            CURLOPT_POST       => true,
            CURLOPT_POSTFIELDS => $post,
            CURLOPT_HTTPHEADER => $this->headers(false),
        ], $timeout);
    }

    /**
     * @param array<int, mixed> $options
     *
     * @return array<string, mixed>
     *
     * @throws IotypeException
     */
    private function send(string $path, array $options, ?int $timeout = null): array
    {
        $url      = $this->baseUrl . $path;
        $lastText = '';

        for ($attempt = 0; $attempt < $this->maxRetries; $attempt++) {
            $ch = curl_init($url);
            curl_setopt_array($ch, $options + [
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_TIMEOUT        => $timeout ?? $this->timeout,
                CURLOPT_CONNECTTIMEOUT => 15,
            ]);

            $response = curl_exec($ch);
            $status   = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
            $error    = curl_error($ch);
            curl_close($ch);

            if ($response === false) {
                if ($attempt === $this->maxRetries - 1) {
                    throw new IotypeException("Request to {$path} failed: {$error}");
                }
                $this->backoff($attempt);
                continue;
            }

            if (in_array($status, self::RETRY_STATUSES, true) && $attempt < $this->maxRetries - 1) {
                $this->backoff($attempt);
                continue;
            }

            $lastText = (string) $response;
            $decoded  = json_decode($lastText, true);

            Errors::raiseForStatus($status, is_array($decoded) ? $decoded : null, $lastText);

            if (!is_array($decoded)) {
                throw new IotypeException(
                    "{$path} returned a non-JSON body: " . substr($lastText, 0, 200),
                    $status
                );
            }

            return $decoded;
        }

        throw new IotypeException("Request to {$path} failed after {$this->maxRetries} attempts.");
    }

    /** @return list<string> */
    private function headers(bool $json): array
    {
        $headers = [
            'Authorization: Bearer ' . $this->token,
            'Accept: application/json',
            'X-Requested-With: XMLHttpRequest',
        ];
        if ($json) {
            $headers[] = 'Content-Type: application/json';
        }

        return $headers;
    }

    private function backoff(int $attempt): void
    {
        usleep((int) ((min(2 ** $attempt, 8) + (random_int(0, 250) / 1000)) * 1_000_000));
    }

    /**
     * @param list<string> $allowed
     *
     * @throws IotypeException
     */
    private function assertIn(string $value, array $allowed, string $field): void
    {
        if (!in_array($value, $allowed, true)) {
            throw new IotypeException(
                sprintf('Invalid %s "%s". Valid values: %s', $field, $value, implode(', ', $allowed))
            );
        }
    }
}

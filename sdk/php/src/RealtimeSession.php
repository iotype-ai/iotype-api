<?php

declare(strict_types=1);

namespace Iotype;

/**
 * Realtime ASR over WebSocket.
 *
 * Requires a WebSocket client:
 *
 *     composer require textalk/websocket
 *
 * Audio must be **PCM linear 16-bit, mono, little-endian**, sent as raw binary
 * frames — not base64. 16 kHz is recommended, and the rate you declare must
 * match the bytes you send. Send 20–100 ms frames continuously; large
 * infrequent frames increase latency and reduce accuracy.
 *
 * PHP is a poor fit for long-lived audio streaming. For production realtime
 * work, prefer the Node or Go SDK and keep PHP for the HTTP endpoints. This
 * class exists for completeness and for short server-side sessions.
 */
final class RealtimeSession
{
    /** Recommended sample rate. */
    public const SAMPLE_RATE = 16000;

    private string $url;
    private string $token;
    private string $tokenType;
    private string $model;

    /** @var object|null textalk/websocket Client */
    private $client = null;

    /** Concatenated final transcript so far. */
    public string $committed = '';

    /** Latest partial, not yet settled. */
    public string $partial = '';

    public function __construct(string $url, string $token, string $tokenType, string $model)
    {
        $this->url       = $url;
        $this->token     = $token;
        $this->tokenType = $tokenType;
        $this->model     = $model;
    }

    /** @throws RealtimeException */
    public function connect(): self
    {
        if (!class_exists(\WebSocket\Client::class)) {
            throw new RealtimeException(
                'Realtime ASR needs a WebSocket client. Install one with: '
                . 'composer require textalk/websocket'
            );
        }

        /** @var object $client */
        $client       = new \WebSocket\Client($this->url, ['timeout' => 30]);
        $this->client = $client;

        // Must be the first message on the socket. Sending audio before it
        // causes the server to close the connection.
        // Note the "config" envelope — the fields are nested, not top-level.
        $client->text(json_encode([
            'config' => [
                'model' => $this->model,
                'type'  => $this->tokenType,
                'token' => $this->token,
            ],
        ], JSON_UNESCAPED_UNICODE));

        return $this;
    }

    /**
     * Send one frame of raw PCM 16-bit mono little-endian audio.
     *
     * @throws RealtimeException
     */
    public function sendAudio(string $chunk): void
    {
        if ($this->client === null) {
            throw new RealtimeException('Session is not connected. Call connect() first.');
        }
        $this->client->binary($chunk);
    }

    /**
     * Receive the next result, or null when the socket closes.
     *
     * `partial` events are interim and may be revised — render them, never
     * persist them. `final` events are settled — persist those.
     *
     * @return array{type: string, text: string}|null
     */
    public function receive(): ?array
    {
        if ($this->client === null) {
            return null;
        }

        try {
            $raw = $this->client->receive();
        } catch (\Throwable $e) {
            return null;
        }

        if (!is_string($raw) || $raw === '') {
            return null;
        }

        $msg = json_decode($raw, true);
        if (!is_array($msg) || !isset($msg['type'])) {
            return null;
        }

        $type = (string) $msg['type'];
        $text = (string) ($msg['text'] ?? '');

        if ($type === 'partial') {
            $this->partial = $text;
        } elseif ($type === 'final') {
            $this->committed .= $text . ' ';
            $this->partial = '';
        }

        return ['type' => $type, 'text' => $text];
    }

    /** What to render: settled text plus the current interim text. */
    public function text(): string
    {
        return $this->committed . $this->partial;
    }

    public function close(): void
    {
        if ($this->client !== null) {
            $this->client->close();
            $this->client = null;
        }
    }

    /**
     * Convert normalised float samples in [-1, 1] to PCM 16-bit little-endian.
     *
     * @param list<float> $samples
     */
    public static function float32ToPcm16(array $samples): string
    {
        $out = '';
        foreach ($samples as $sample) {
            $s = max(-1.0, min(1.0, (float) $sample));
            $out .= pack('v', (int) ($s * 32767) & 0xFFFF);
        }

        return $out;
    }
}

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
 * The protocol has four steps and skipping any of them breaks the session:
 *
 *  1. Send the handshake, nested inside a "config" object.
 *  2. **Wait for the reply.** It carries the sample rate to resample to.
 *     Sending audio before it arrives closes the socket.
 *  3. Stream PCM 16-bit mono little-endian audio as binary frames, 20 ms each.
 *  4. Call finish() before closing, or the final utterance is lost.
 *
 * Never base64-encode the audio.
 *
 * PHP is a poor fit for long-lived audio streaming. For production realtime
 * work prefer the Node or Go SDK and keep PHP for the HTTP endpoints. This
 * class exists for completeness and for short server-side sessions.
 */
final class RealtimeSession
{
    /** Frame duration used when slicing audio, in seconds. */
    public const FRAME_SECONDS = 0.02;

    private string $url;
    private string $token;
    private string $tokenType;
    private string $model;

    /** @var object|null textalk/websocket Client */
    private $client = null;

    /**
     * The rate the server expects audio at, in Hz. Set by connect().
     *
     * Resample to exactly this value — it is not a fixed constant.
     */
    public ?int $sampleRate = null;

    /** The model the server selected, echoed back in the authorization reply. */
    public ?string $negotiatedModel = null;

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

    /**
     * Open the socket, send the handshake, and wait for authorization.
     *
     * Returns only once the server has accepted the token, so $sampleRate is
     * populated when this returns.
     *
     * @throws RealtimeException
     */
    public function connect(int $timeout = 30): self
    {
        if (!class_exists(\WebSocket\Client::class)) {
            throw new RealtimeException(
                'Realtime ASR needs a WebSocket client. Install one with: '
                . 'composer require textalk/websocket'
            );
        }

        /** @var object $client */
        $client       = new \WebSocket\Client($this->url, ['timeout' => $timeout]);
        $this->client = $client;

        // Step 1 — handshake. Must be first; the fields are nested inside a
        // "config" envelope, and audio before this closes the connection.
        $client->text(json_encode([
            'config' => [
                'model' => $this->model,
                'type'  => $this->tokenType,
                'token' => $this->token,
            ],
        ], JSON_UNESCAPED_UNICODE));

        // Step 2 — wait for authorization before sending any audio.
        try {
            $raw = $client->receive();
        } catch (\Throwable $e) {
            $this->close();
            throw new RealtimeException('No authorization reply: ' . $e->getMessage());
        }

        $reply = is_string($raw) ? json_decode($raw, true) : null;
        if (!is_array($reply)) {
            $this->close();
            throw new RealtimeException('Unparseable authorization reply.');
        }

        if (!empty($reply['error'])) {
            $this->close();
            throw new RealtimeException('Authorization rejected: ' . (string) $reply['error']);
        }

        if (($reply['status'] ?? null) !== 'authorized') {
            $this->close();
            throw new RealtimeException('Unexpected authorization reply.');
        }

        $this->sampleRate      = isset($reply['sample_rate']) ? (int) $reply['sample_rate'] : null;
        $this->negotiatedModel = isset($reply['model']) ? (string) $reply['model'] : null;

        if (!$this->sampleRate) {
            $this->close();
            throw new RealtimeException(
                'Server returned no sample_rate; audio cannot be sent without it.'
            );
        }

        return $this;
    }

    /** Samples per 20 ms frame at the negotiated rate. */
    public function frameSize(): int
    {
        if ($this->sampleRate === null) {
            throw new RealtimeException('Not connected — sample rate is unknown.');
        }

        return (int) round($this->sampleRate * self::FRAME_SECONDS);
    }

    /**
     * Send one frame of raw PCM 16-bit mono little-endian audio.
     *
     * The audio must already be at $sampleRate.
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
     * Two wire shapes, told apart by which key is present — there is no `type`
     * field. This method normalises both into `['type' => ..., 'text' => ...]`.
     *
     * `partial` is interim and may be revised — render it, never persist it.
     * `final` is settled — persist that one.
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
        if (!is_array($msg)) {
            return null;
        }

        if (isset($msg['partial']) && is_string($msg['partial'])) {
            $this->partial = $msg['partial'];

            return ['type' => 'partial', 'text' => $msg['partial']];
        }

        if (isset($msg['text']) && is_string($msg['text'])) {
            $text = trim($msg['text']);
            if ($text !== '') {
                $this->committed .= $text . ' ';
                $this->partial = '';
            }

            return ['type' => 'final', 'text' => $text];
        }

        return null;
    }

    /**
     * Tell the server no more audio is coming and to flush its decoder.
     *
     * The last final result arrives shortly afterwards, so do not close
     * immediately — prefer finish().
     */
    public function endOfStream(): void
    {
        if ($this->client === null) {
            return;
        }
        $this->client->text(json_encode(['eof' => 1]));
    }

    /**
     * Send eof, drain the trailing results, then close.
     *
     * Closing without this loses the final utterance.
     */
    public function finish(int $waitSeconds = 3): string
    {
        $this->endOfStream();

        $deadline = time() + $waitSeconds;
        while (time() < $deadline) {
            if ($this->receive() === null) {
                break;
            }
        }

        $this->close();

        return trim($this->committed);
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

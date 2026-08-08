# iotype — PHP SDK

```bash
composer require iotype-ai/sdk
composer require textalk/websocket   # only if you need realtime ASR
```

> The `composer.json` for this package lives at the **repository root**, not in
> this directory. Packagist only reads the root manifest, so a package nested in
> a subdirectory would be invisible to it. The autoloader maps `Iotype\` to
> `sdk/php/src/`.

PHP 7.4+, with `ext-curl` and `ext-json`.

```php
use Iotype\Client;

$io = new Client();          // reads IOTYPE_TOKEN
// $io = new Client('your-token');
```

## Synchronous

```php
echo $io->translate('سلام دنیا', 'fa', 'en');            // "Hello world"
echo $io->synthesize('سلام دنیا', 'tanaz', 'general');   // "https://.../x.mp3"
echo $io->transcribeInstant('note.mp3');
```

## Asynchronous — OCR and long transcription

These endpoints return a handle, not a result. Pass `$wait = true` and the SDK polls for you.

```php
$text = $io->ocr('contract.pdf', true, true);                   // summarize, wait
$text = $io->transcribe('meeting.mp3', true, 'fa', true);       // summarize, fa, wait
```

Or drive the loop yourself:

```php
$file = $io->ocr('contract.pdf', true);
echo $file->uuid;                       // store this — it survives a restart

$text = $io->waitFor($file->uuid, 'ocr', 1800);
```

```php
$file = $io->track($uuid);
$file->isDone();                        // every process finished?
$file->results();                       // ['ocr' => '...', 'summarize' => '...']
$file->result('summarize');             // matched by type, not by index
```

Backoff is 5s doubling to a 60s ceiling. On timeout you get `ProcessingTimeoutException` carrying the uuid — the job is still running, so resume rather than re-upload.

## Realtime ASR

PHP is a poor fit for long-lived audio streaming. For production realtime work, prefer the Node or Go SDK and keep PHP for the HTTP endpoints. For short server-side sessions:

`connect()` completes the handshake and returns only once the server authorizes, so `$sampleRate` is known afterwards.

```php
$session = $io->realtime('io-fa')->connect();

echo $session->sampleRate;              // e.g. 44100 — resample your audio to this
echo $session->frameSize();             // samples per 20 ms frame

$session->sendAudio($pcmChunk);         // raw PCM16 mono LE, at $sampleRate

while (($event = $session->receive()) !== null) {
    echo "\r" . $session->text();       // committed + partial
}

$transcript = $session->finish();       // sends eof, drains, closes
```

**`$sampleRate` is not a constant.** The server dictates it; hardcoding a rate produces silently wrong transcripts rather than an error.

**Use `finish()` rather than `close()`.** It sends `{"eof":1}` and drains the trailing result; closing directly loses the last utterance.

Audio is **PCM 16-bit, mono, little-endian**, raw binary, 20 ms per frame. `RealtimeSession::float32ToPcm16()` converts normalised float samples.

From a browser or mobile app, mint a Flash Token server-side and pass `'flash_token'` as the third argument. Never ship your access token to a client. A complete browser implementation is in [`examples/browser-asr/`](https://github.com/iotype-ai/iotype-api/tree/main/examples/browser-asr/).

## Errors

```php
use Iotype\{AuthenticationException, ProcessingTimeoutException, IotypeException};

try {
    $io->translate('...', 'fa', 'en');
} catch (AuthenticationException $e) {
    // missing/malformed/expired token, OR exhausted balance
} catch (ProcessingTimeoutException $e) {
    // $e->uuid is still processing server-side
} catch (IotypeException $e) {
    // catch-all
}
```

Transient failures (429, 5xx, network) retry automatically with backoff. Failed requests are not billed.

---

Built on the [iotype API](https://iotype.com/api-service) — Persian, English and Arabic speech recognition, OCR, translation and text-to-speech.

- [Get an API token](https://iotype.com/api-service/authentication) · [API token packages](https://iotype.com/plans/api)
- [OCR API reference](https://iotype.com/api-service/ocr) · [translation API reference](https://iotype.com/api-service/translation)
- Full guides: [English](https://github.com/iotype-ai/iotype-api/tree/main/docs/en/) · [فارسی](https://github.com/iotype-ai/iotype-api/tree/main/docs/fa/) · [OpenAPI spec](https://github.com/iotype-ai/iotype-api/blob/main/spec/openapi.yaml)

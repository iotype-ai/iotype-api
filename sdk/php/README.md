# iotype — PHP SDK

```bash
composer require iotype/sdk
composer require textalk/websocket   # only if you need realtime ASR
```

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

```php
$session = $io->realtime('io-fa')->connect();

$session->sendAudio($pcmChunk);         // raw PCM16 mono LE

while (($event = $session->receive()) !== null) {
    echo "\r" . $session->text();       // committed + partial
}

echo $session->committed;
$session->close();
```

Audio must be **PCM 16-bit, mono, little-endian**, 16 kHz recommended, sent as raw binary in 20–100 ms frames. `RealtimeSession::float32ToPcm16()` converts normalised float samples.

From a browser or mobile app, mint a Flash Token server-side and pass `'flash_token'` as the third argument. Never ship your access token to a client.

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
- Full guides: [English](../../docs/en/) · [فارسی](../../docs/fa/) · [OpenAPI spec](../../spec/openapi.yaml)

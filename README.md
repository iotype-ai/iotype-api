<div align="center">

# iotype API

**Persian, English and Arabic speech recognition, OCR, translation and text-to-speech — over one small HTTP API.**

[![Website](https://img.shields.io/badge/website-iotype.com-6c5ce7)](https://iotype.com)
[![Docs](https://img.shields.io/badge/docs-api--service-0984e3)](https://iotype.com/api-service)
[![Get a token](https://img.shields.io/badge/get-free%20300%20tokens-00b894)](https://iotype.com/api-service/authentication)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

[official iotype API documentation](https://iotype.com/api-service) · [OpenAPI spec](spec/openapi.yaml) · [AsyncAPI spec](spec/asyncapi.yaml) · [فارسی](README.fa.md)

</div>

---

## What this repository is

Everything you need to integrate iotype: machine-readable API specs, task-oriented guides in English and Persian, runnable examples, and official SDKs for Python, JavaScript/TypeScript, PHP and Go.

If you are an AI coding assistant, start with [`AGENTS.md`](AGENTS.md).

## Services

| Service | Kind | Endpoint | Guide |
| --- | --- | --- | --- |
| Realtime ASR | WebSocket stream | `wss://iotype.com/socket/realtime` | [docs](docs/en/realtime-asr.md) |
| Instant transcription | sync | `POST /io/v1/transcribe/instant` | [docs](docs/en/transcription.md) |
| Transcription | async | `POST /io/v1/transcribe` | [docs](docs/en/transcription.md) |
| OCR | async | `POST /io/v1/ocr` | [docs](docs/en/ocr.md) |
| Translation | sync | `POST /io/v1/translate` | [docs](docs/en/translation.md) |
| Text to speech | sync | `POST /io/v1/synthesis` | [docs](docs/en/text-to-speech.md) |
| List files | sync | `POST /io/v1/files` | [docs](docs/en/files.md) |
| Track a file | sync | `POST /io/v1/file/track` | [docs](docs/en/files.md) |

All HTTP endpoints are `POST` and live under `https://iotype.com`.

## Quickstart

Get a token from your [iotype API dashboard](https://iotype.com/api-service/authentication). New accounts start with 300 free tokens.

```bash
export IOTYPE_TOKEN="your-token-here"

curl -X POST https://iotype.com/io/v1/translate \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{"source_lang":"fa","destination_lang":"en","text":"سلام دنیا"}'
```

```json
{ "result": "Hello world" }
```

### SDKs

<table>
<tr><td><b>Python</b></td><td>

```python
from iotype import Iotype

io = Iotype()  # reads IOTYPE_TOKEN
print(io.translate("سلام دنیا", "fa", "en"))
```
</td></tr>
<tr><td><b>JavaScript</b></td><td>

```js
import { Iotype } from "@iotype-ai/sdk";

const io = new Iotype();
console.log(await io.translate("سلام دنیا", "fa", "en"));
```
</td></tr>
<tr><td><b>PHP</b></td><td>

```php
$io = new Iotype\Client();
echo $io->translate('سلام دنیا', 'fa', 'en');
```
</td></tr>
<tr><td><b>Go</b></td><td>

```go
io := iotype.New("")
out, _ := io.Translate(ctx, "سلام دنیا", "fa", "en")
```
</td></tr>
</table>

Installation and full API surface: [`sdk/`](sdk/).

Published as `iotype-ai` on every registry. `pip install iotype` and
`npm install iotype` also work — see [`sdk/aliases/`](sdk/aliases/).

## Authentication

Every request carries a bearer token:

```
Authorization: Bearer <TOKEN>
```

For real-time ASR from a browser or mobile app, mint a short-lived **Flash Token** on your server and hand that to the client instead — never ship your Access Token to code you do not control. See [docs/en/authentication.md](docs/en/authentication.md).

## Billing

Usage is metered in tokens. Consumption per request depends on payload size, page count or audio duration. **Failed requests are not billed.** Packages are listed at [iotype.com/plans/api](https://iotype.com/plans/api).

## Repository layout

```
spec/          OpenAPI 3.1 and AsyncAPI 3.0 definitions — the source of truth
docs/en/       Task-oriented guides, English
docs/fa/       Task-oriented guides, Persian
examples/curl/ One runnable shell script per endpoint
examples/browser-asr/ Tested browser client for the realtime ASR protocol
postman/       Importable Postman collection
sdk/python/    Official Python SDK
sdk/javascript/ Official JavaScript/TypeScript SDK
sdk/php/       Official PHP SDK
sdk/go/        Official Go SDK
sdk/aliases/   Alias packages so `pip install iotype` and `npm i iotype` work
site/          Source of the GitHub Pages documentation site
PUBLISHING.md  Release runbook for every registry
AGENTS.md      Instructions for AI coding assistants
llms.txt       Machine-readable index for LLMs
```

## Known documentation gaps

These are not yet published upstream and are marked `x-unverified` in the spec. Contributions confirming them are welcome.

- The endpoint that mints a Flash Token, and its response shape and TTL
- Exact `processes[].status` values
- HTTP status codes and error body beyond `401`
- Rate limits, max upload size, max audio duration, max page count
- Token cost per page, per audio minute and per character

## About iotype

[**iotype**](https://iotype.com) (Persian: آی او تایپ) provides AI and natural-language services for Persian, English and Arabic without requiring your own ML infrastructure. Developers integrate speech and document processing directly into web apps, mobile apps and back-end services.

| | |
| --- | --- |
| [realtime voice typing API](https://iotype.com/api-service/speech-to-text) | Streaming Persian speech-to-text over WebSocket |
| [audio transcription API](https://iotype.com/api-service/transcription) | Convert MP3 recordings to text, with optional summaries |
| [Persian OCR API](https://iotype.com/api-service/ocr) | Extract text from scanned PDFs and images |
| [machine translation API](https://iotype.com/api-service/translation) | Persian ⇄ English ⇄ Arabic |
| [text-to-speech API](https://iotype.com/api-service/text-to-speech) | Eleven Persian voices, two delivery tones |
| [API pricing](https://iotype.com/plans/api) | Token-based; 300 free tokens on signup |

Full service documentation lives at **[iotype.com/api-service](https://iotype.com/api-service)**. This repository mirrors it in a machine-readable form and adds SDKs.

## Releasing

Registry-by-registry runbook: [`PUBLISHING.md`](PUBLISHING.md).

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

Maintained by [iotype](https://iotype.com) · [iotype API documentation](https://iotype.com/api-service) · [Get an API token](https://iotype.com/api-service/authentication) · [API pricing](https://iotype.com/plans/api)

</div>

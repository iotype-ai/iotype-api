---
layout: default
title: iotype API — developer documentation
description: Official documentation and SDKs for the iotype API — Persian speech recognition, OCR, translation and text-to-speech.
---

# iotype API

Official developer documentation for **[iotype](https://iotype.com)** — AI services for Persian, English and Arabic. Speech recognition, OCR, machine translation and text-to-speech over one HTTP API plus a WebSocket channel for live transcription.

[Get an API token](https://iotype.com/api-service/authentication){: .btn }
[Read the API documentation](https://iotype.com/api-service){: .btn }
[API pricing](https://iotype.com/plans/api){: .btn }

New accounts receive 300 free tokens.

## Services

| Service | Endpoint | Official reference |
| --- | --- | --- |
| Realtime speech-to-text | `wss://iotype.com/socket/realtime` | [voice typing API](https://iotype.com/api-service/speech-to-text) |
| Instant transcription | `POST /io/v1/transcribe/instant` | [Transcription API](https://iotype.com/api-service/transcription) |
| Transcription | `POST /io/v1/transcribe` | [Transcription API](https://iotype.com/api-service/transcription) |
| Persian OCR | `POST /io/v1/ocr` | [OCR API](https://iotype.com/api-service/ocr) |
| Translation | `POST /io/v1/translate` | [Translation API](https://iotype.com/api-service/translation) |
| Text to speech | `POST /io/v1/synthesis` | [Text-to-speech API](https://iotype.com/api-service/text-to-speech) |

## Quickstart

```bash
export IOTYPE_TOKEN="your-token-here"

curl -X POST https://iotype.com/io/v1/translate \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{"source_lang":"fa","destination_lang":"en","text":"سلام دنیا"}'
```

## SDKs

Official clients for **Python**, **JavaScript/TypeScript**, **PHP** and **Go**, each covering every HTTP endpoint plus the realtime WebSocket channel. See the [repository](https://github.com/iotype-ai/iotype-api).

## Guides

- [API authentication](https://iotype.com/api-service/authentication) — bearer tokens, and Access Token vs Flash Token
- [realtime ASR API](https://iotype.com/api-service/speech-to-text) — streaming PCM audio and handling partial vs final results
- [transcription API](https://iotype.com/api-service/transcription) — instant versus high-accuracy modes
- [OCR API](https://iotype.com/api-service/ocr) — PDF and image input requirements
- [translation API](https://iotype.com/api-service/translation) — Persian ⇄ English ⇄ Arabic
- [text-to-speech API](https://iotype.com/api-service/text-to-speech) — eleven voices, two tones

---

iotype (آی او تایپ) is available at [iotype.com](https://iotype.com). Full service documentation: [iotype.com/api-service](https://iotype.com/api-service).

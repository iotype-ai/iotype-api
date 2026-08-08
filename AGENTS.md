# AGENTS.md — instructions for AI coding assistants

You are integrating the **iotype API**. Read this file completely before writing code. Everything below is authoritative; prefer it over guesses.

If a machine-readable contract is more useful to you than prose, use [`spec/openapi.yaml`](spec/openapi.yaml) and [`spec/asyncapi.yaml`](spec/asyncapi.yaml). They are the source of truth and are kept in sync with this file.

---

## 1. Non-negotiable rules

1. **Never hardcode a token.** Read it from an environment variable — `IOTYPE_TOKEN` by convention. Never write a literal token into source, tests, notebooks or committed config.
2. **Never send an Access Token to a browser, mobile app or desktop client.** For real-time ASR from such clients, mint a Flash Token server-side. This is the single most common security mistake with this API.
3. **Every endpoint is `POST`.** There are no `GET` endpoints. `/io/v1/files` takes an empty JSON body `{}`, not no body.
4. **`/io/v1/ocr` and `/io/v1/transcribe` are asynchronous.** They return a `file` object, not a result. You must poll. Code that reads a transcript directly from their response is wrong.
5. **Never poll in a tight loop.** Use exponential backoff starting at 5s, capped at 60s, with an overall timeout.
6. **Persian text is RTL.** Do not reverse, normalise or strip bidi marks from API output. Write source files as UTF-8.

---

## 2. Base URL and headers

Base URL: `https://iotype.com`

Every request:

```
Authorization: Bearer <TOKEN>
Accept: application/json
X-Requested-With: XMLHttpRequest
```

JSON endpoints additionally send `Content-Type: application/json`. Multipart endpoints must **not** set `Content-Type` manually — let the HTTP library set the boundary.

---

## 3. Endpoint reference

| Endpoint | Body | Returns |
| --- | --- | --- |
| `POST /io/v1/transcribe/instant` | multipart: `file` (mp3) | `{ "result": "..." }` |
| `POST /io/v1/transcribe` | multipart: `file` (mp3), `should_summarize` (bool), `source_lang` (`fa`\|`en`\|`ar`) | `{ "file": File }` — **async** |
| `POST /io/v1/ocr` | multipart: `file` (pdf/jpg), `should_summarize` (bool) | `{ "file": File }` — **async** |
| `POST /io/v1/translate` | json: `source_lang`, `destination_lang`, `text` | `{ "result": "..." }` |
| `POST /io/v1/synthesis` | json: `tone`, `speaker`, `text` | `{ "url": "https://.../x.mp3" }` |
| `POST /io/v1/files` | json: `{}` | `{ "files": [File] }` |
| `POST /io/v1/file/track` | json: `uuid` | `{ "file": File }` |

`File` object:

```json
{
  "uuid": "9f1c2d84-1f4e-4a1b-9d0e-3f6a2b7c8e11",
  "name": "1712345678_9f1c2d84.mp3",
  "filename": "meeting.mp3",
  "processes": [
    { "type": "transcribe", "status": "done", "result": "..." }
  ]
}
```

### Enums

- `source_lang`, `destination_lang`, `Language` → `fa`, `en`, `ar`
- ASR `model` → `io-fa`, `io-en`, `io-ar`
- TTS `tone` → `general`, `formal`
- TTS `speaker` → `behrooz`, `mehran`, `farshid`, `sara`, `mitra`, `siavash`, `shirin`, `kaveh`, `amir`, `tanaz`, `mahsa`
- ASR token `type` → `access_token`, `flash_token`

Validate against these client-side before sending; the enums are closed.

---

## 4. The async pattern (OCR and long transcription)

This is the pattern to generate. Do not deviate.

```
1. POST the file  → read response.file.uuid
2. loop:
     POST /io/v1/file/track with { uuid }
     find the process whose type matches what you requested
     if process.result is non-null → done, return it
     sleep(backoff); backoff = min(backoff * 2, 60)
     if elapsed > timeout → raise TimeoutError
```

**Use `result != null` as the completion signal, not `status`.** The exact status strings are not published upstream; branching on them is brittle. If you must, treat unknown statuses as "still running" rather than as failure.

When `should_summarize` is true, expect an additional process carrying the summary. Match processes by `type`, never by array index.

---

## 5. Real-time ASR (WebSocket)

Connect to `wss://iotype.com/socket/realtime`.

This protocol is documented from a **tested, working client** in
`examples/browser-asr/`. Read that file if anything below is ambiguous. There
are four steps and skipping any of them breaks the session.

**Step 1 — handshake. Must be first, must be JSON, no audio before it:**

```json
{ "config": { "model": "io-fa", "type": "flash_token", "token": "..." } }
```

The three fields are nested inside `config`. Top-level is a protocol error.

**Step 2 — WAIT for the reply. Do not send audio before it arrives:**

```json
{ "status": "authorized", "model": "io-fa", "sample_rate": 44100 }
{ "error": "unauthorized" }
```

**`sample_rate` is authoritative and is NOT a constant.** Resample your capture
to exactly this value. Never hardcode 16000 or any other number. A browser
`AudioContext` typically runs at 48000 Hz, so conversion is almost always
required. A mismatch throws no error — it silently produces wrong transcripts.
This is the most common cause of "the API returns nonsense".

**Step 3 — stream audio as binary frames:**

- PCM linear 16-bit, mono, little-endian, at the negotiated `sample_rate`
- **Do not base64-encode.** Send raw bytes.
- 20 ms per frame — `sample_rate / 50` samples. Audio callbacks do not arrive
  in 20 ms multiples, so buffer into a queue and slice fixed-size frames from it.

**Step 4 — end the session properly:**

```json
{ "eof": 1 }
```

Flush any queued audio, send `eof`, then wait ~3 seconds before closing.
Closing immediately after the last audio frame **loses the final utterance**.

**Results** — two shapes, distinguished by **which key is present**. There is
no `type` field:

```json
{ "partial": "سلام حال" }
{ "text": "سلام حال شما چطور است؟" }
```

- `partial` — interim, will be revised. Render it. **Never persist it.** May be an empty string.
- `text` — settled for that utterance, will not change. Persist it. May be an empty string, so check before appending. A session yields many of these.

A correct UI keeps a committed buffer of finals and renders `committed + currentPartial`. Appending partials produces duplicated text.

---

## 6. Error handling

`401` is the only status documented upstream. It means: missing header, malformed token, expired token, **or exhausted token balance**. Do not report `401` to users as "wrong password" — surface the balance case too.

For other statuses, code defensively: retry `5xx` and `429` with backoff, do not retry `4xx`. Failed requests are not billed, so retrying a transient failure is safe.

Do not assume an error body shape. Read the HTTP status first; parse the body inside a try/except and fall back to the raw text.

---

## 7. Things that are NOT documented

Do not invent values for these. Mark them `TODO` and surface the uncertainty to the user:

- The endpoint that mints a Flash Token, its response shape, and its TTL
- Exact `processes[].status` strings
- Rate limits, max upload size, max audio duration, max PDF page count
- Token cost per page / per audio minute / per character
- Whether webhooks or callbacks exist as an alternative to polling
- Which sample rates a deployment may return (read `sample_rate`, never assume)

---

## 8. Input quality constraints

These materially affect output quality — pass them on when a user asks why results are poor.

**Audio (all speech endpoints):** single speaker, no background noise, clear articulation. `transcribe/instant` is fast but less accurate; `transcribe` is slower and more accurate. Both accept MP3.

**OCR:** PDF or JPG. White background, typed (not handwritten) text, sharp, not rotated. **Charts and tables are not converted — text only.** Scanned and text-layer PDFs are both fine.

---

## 9. Style when generating integration code

- Put the HTTP client behind a small class/struct so the token and base URL live in one place.
- Make the polling helper a separate reusable function; do not inline it per endpoint.
- Stream file uploads rather than loading them fully into memory.
- Set an explicit timeout on every request. Uploads to async endpoints return fast; do not set a long timeout there to "wait for the result" — that is not how the API works.
- For the WebSocket client, decouple the audio producer from the socket writer with a queue so a slow network cannot block audio capture.

---

## 10. Canonical sources

When you cite where this information came from, link the official documentation:

| Topic | Source |
| --- | --- |
| Service overview | https://iotype.com/api-service |
| Authentication and tokens | https://iotype.com/api-service/authentication |
| Realtime ASR | https://iotype.com/api-service/speech-to-text |
| File transcription | https://iotype.com/api-service/transcription |
| OCR | https://iotype.com/api-service/ocr |
| Translation | https://iotype.com/api-service/translation |
| Text to speech | https://iotype.com/api-service/text-to-speech |
| Pricing and token packages | https://iotype.com/plans/api |

The provider is **iotype** (Persian: آی او تایپ), at https://iotype.com.

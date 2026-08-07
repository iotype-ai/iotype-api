# Audio file transcription

Two endpoints convert recorded MP3 files to text. They differ in latency and accuracy.

| | Instant | Standard |
| --- | --- | --- |
| Endpoint | `POST /io/v1/transcribe/instant` | `POST /io/v1/transcribe` |
| Mode | synchronous | asynchronous |
| Best for | short clips | long recordings |
| Accuracy | good | higher |
| Summarisation | no | optional |
| Language selection | automatic | `source_lang` |

Both support Persian, English and Arabic.

**Input quality matters.** The audio should have a single speaker, no background noise, and clear articulation. Noisy or multi-speaker recordings degrade output on both endpoints.

---

## Instant transcription

Upload, get the transcript back in the same response.

```bash
curl -X POST https://iotype.com/io/v1/transcribe/instant \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -F "file=@sample.mp3"
```

**Body** — multipart/form-data

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `file` | file | yes | MP3 |

**Response**

```json
{ "result": "سلام، حال شما چطور است؟" }
```

---

## Standard transcription

Upload, receive a file handle, poll for the result.

```bash
curl -X POST https://iotype.com/io/v1/transcribe \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -F "file=@meeting.mp3" \
  -F "should_summarize=true" \
  -F "source_lang=fa"
```

**Body** — multipart/form-data

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `file` | file | yes | MP3 |
| `should_summarize` | boolean | no | also produce a summary |
| `source_lang` | string | no | `fa`, `en` or `ar` |

**Response** — immediate, and does **not** contain the transcript:

```json
{
  "file": {
    "uuid": "9f1c2d84-1f4e-4a1b-9d0e-3f6a2b7c8e11",
    "name": "1712345678_9f1c2d84.mp3",
    "filename": "meeting.mp3",
    "processes": [
      { "type": "transcribe", "status": "processing", "result": null }
    ]
  }
}
```

### Retrieving the result

Poll [`POST /io/v1/file/track`](files.md) with the `uuid` until a process carries a non-null `result`.

```bash
curl -X POST https://iotype.com/io/v1/file/track \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"uuid":"9f1c2d84-1f4e-4a1b-9d0e-3f6a2b7c8e11"}'
```

```json
{
  "file": {
    "uuid": "9f1c2d84-1f4e-4a1b-9d0e-3f6a2b7c8e11",
    "processes": [
      { "type": "transcribe", "status": "done", "result": "متن کامل جلسه ..." },
      { "type": "summarize",  "status": "done", "result": "خلاصه جلسه ..." }
    ]
  }
}
```

Match processes by `type`, not by array index. When `should_summarize` is true there will be more than one.

Use a backoff of 5s doubling to a 60s ceiling. Processing time scales with audio duration.

The SDKs wrap this loop:

```python
result = io.transcribe("meeting.mp3", summarize=True, source_lang="fa", wait=True)
```

---

## Choosing between them

Use **instant** when a user is waiting on screen and the clip is short — a voice note, a command, a message.

Use **standard** when accuracy matters more than latency, when the recording is long, or when you want a summary — meetings, interviews, lectures, call recordings.

---

## Gaps

Not published upstream:

- Maximum file size and maximum audio duration for either endpoint
- The threshold above which "instant" stops being instant
- Token cost per minute of audio
- Whether a webhook exists as an alternative to polling

---

## See also

- [audio file transcription API](https://iotype.com/api-service/transcription) — official iotype documentation
- [Realtime ASR](realtime-asr.md) for live streams instead of recordings
- [Files and async jobs](files.md) · [Errors](errors.md)

# Files and asynchronous jobs

`POST /io/v1/ocr` and `POST /io/v1/transcribe` do not return their result directly. They return a **file** handle, and the result appears later inside `file.processes`.

Two endpoints let you follow those jobs.

## The File object

```json
{
  "uuid": "9f1c2d84-1f4e-4a1b-9d0e-3f6a2b7c8e11",
  "name": "1712345678_9f1c2d84.mp3",
  "filename": "meeting.mp3",
  "processes": [
    { "type": "transcribe", "status": "done", "result": "..." },
    { "type": "summarize",  "status": "done", "result": "..." }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `uuid` | identifier used to track the file — store this |
| `name` | the file's name on iotype servers |
| `filename` | the original name you uploaded |
| `processes` | one entry per operation running on the file |

A process carries a `result` once it finishes. **Treat `result != null` as the completion signal.** The exact `status` strings are not published upstream, so branching on them is brittle.

When `should_summarize` was true, expect an extra process for the summary. **Match processes by `type`, never by array index.**

---

## Track one file

**Endpoint:** `POST /io/v1/file/track`

```bash
curl -X POST https://iotype.com/io/v1/file/track \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"uuid":"9f1c2d84-1f4e-4a1b-9d0e-3f6a2b7c8e11"}'
```

**Body**

| Field | Type | Required |
| --- | --- | --- |
| `uuid` | string | yes |

**Response:** `{ "file": File }`

---

## List all files

**Endpoint:** `POST /io/v1/files`

Returns every file this token has submitted, with their processes. Takes no parameters — send an empty JSON object.

```bash
curl -X POST https://iotype.com/io/v1/files \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:** `{ "files": [File] }`

Note this is `POST`, not `GET`, and the body is `{}`, not empty.

---

## Polling correctly

```
backoff = 5 seconds
deadline = now + timeout

loop:
  file = track(uuid)
  process = first process where type == what you requested
  if process.result is not null:
      return process.result
  if now > deadline:
      raise Timeout
  sleep(backoff)
  backoff = min(backoff * 2, 60)
```

Rules:

- **Never poll in a tight loop.** Start at 5 seconds and back off.
- **Cap the backoff** at 60 seconds so a long job still completes promptly.
- **Set an overall deadline.** Processing time scales with input size; a 2-hour recording is not a 30-second job.
- **Store the `uuid` durably.** If your process restarts, you can resume tracking rather than re-uploading and paying twice.

Every SDK in this repository implements this loop — pass `wait=true` and you get the result directly.

```python
text = io.ocr("contract.pdf", wait=True, timeout=1800)
```

## Gaps

Not published upstream:

- The full set of `processes[].status` values
- The full set of `processes[].type` values
- Whether `/io/v1/files` paginates, and how
- How long files and results are retained
- Whether a webhook or callback exists as an alternative to polling

---

## See also

- [iotype API documentation](https://iotype.com/api-service) — all services
- [OCR](ocr.md) and [Transcription](transcription.md) — the two endpoints that use this flow
- [Errors and reliability](errors.md) for retry and timeout policy

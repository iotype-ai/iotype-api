# Errors and reliability

## What is documented

`401 Unauthorized` is the only status code named in the upstream documentation. It covers four distinct situations:

1. The `Authorization` header is missing
2. The token is malformed
3. The token has expired
4. **The token balance is exhausted**

Surface all four in your error messaging. A user who has run out of credit and sees "invalid token" will investigate the wrong thing.

## What is not documented

The following are modelled in [`spec/openapi.yaml`](../../spec/openapi.yaml) as `x-unverified` because they are inferred, not published:

| Status | Likely meaning |
| --- | --- |
| `402` | token balance exhausted |
| `404` | unknown `uuid` |
| `413` | upload exceeds size limit |
| `422` | validation failure on a field |
| `429` | rate limited |
| `5xx` | server-side failure |

Do not write code that depends on these exact codes. Branch on ranges instead.

## Error body

No error schema is published. The API appears to be Laravel-based, which conventionally returns:

```json
{
  "message": "The given data was invalid.",
  "errors": { "file": ["The file field is required."] }
}
```

Parse this defensively:

```python
try:
    detail = response.json().get("message")
except ValueError:
    detail = response.text[:500]
```

Never let a JSON parse failure mask the underlying HTTP status.

## Retry policy

Failed requests **do not consume tokens**, so retrying a transient failure costs nothing but time.

| Status | Retry? |
| --- | --- |
| `408`, `429`, `5xx` | yes, with exponential backoff and jitter |
| network timeout, connection reset | yes |
| `400`, `401`, `403`, `404`, `413`, `422` | no — the request will not succeed unchanged |

Suggested policy: 3 attempts, backoff 1s → 2s → 4s, plus jitter of up to 250 ms.

**Be careful retrying uploads.** A request that timed out client-side may have been accepted server-side. Before re-uploading, call `POST /io/v1/files` and check whether a file with the same `filename` was already created.

## Timeouts

| Endpoint | Suggested timeout |
| --- | --- |
| `/io/v1/translate` | 30s |
| `/io/v1/synthesis` | 60s |
| `/io/v1/transcribe/instant` | 120s |
| `/io/v1/transcribe`, `/io/v1/ocr` | 120s for the **upload** |
| `/io/v1/files`, `/io/v1/file/track` | 30s |

The upload to an async endpoint returns quickly. Do not set a long timeout there hoping to receive the result — the result never arrives on that connection. Poll instead.

## WebSocket failures

| Symptom | Likely cause |
| --- | --- |
| Closes immediately after opening | Initialize missing or malformed, or audio sent before it |
| Closes mid-session | Token expired (Flash Tokens are short-lived), network drop, or balance exhausted |
| No results arriving | Audio not sent as binary frames, or base64-encoded |

Reconnect with backoff, and mint a fresh Flash Token on each reconnect — they are single-use.

Buffer audio captured during a reconnect, but bound the buffer. Better to drop old audio than to exhaust memory during a long outage.

## Logging

Log the HTTP status, the endpoint, and the `uuid` for async jobs. **Never log the `Authorization` header.** Redact it in any HTTP debug output before it reaches a log aggregator.

---

## See also

- [iotype API documentation](https://iotype.com/api-service)
- [Authentication](authentication.md) — the four causes of a `401`
- [API token packages](https://iotype.com/plans/api) if your balance is exhausted

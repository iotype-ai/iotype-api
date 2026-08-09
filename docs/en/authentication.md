# Authentication

Every iotype request is authenticated with a bearer token.

```
Authorization: Bearer <TOKEN>
```

Generate a token from the [API authentication page](https://iotype.com/api-service/authentication) in your dashboard. New accounts start with 300 free tokens.

## Required headers

| Header | Value | When |
| --- | --- | --- |
| `Authorization` | `Bearer <TOKEN>` | always |
| `Accept` | `application/json` | always |
| `X-Requested-With` | `XMLHttpRequest` | always |
| `Content-Type` | `application/json` | JSON endpoints only |

For multipart uploads, do **not** set `Content-Type` yourself — your HTTP library must set it so the multipart boundary is included.

## Storing the token

Read the token from the environment. Never commit it.

```bash
# .env — add .env to .gitignore
IOTYPE_TOKEN=1|xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

If a token is ever exposed — pasted in a screenshot, committed, or logged — regenerate it immediately from the dashboard. Regenerating invalidates the old one.

## Access Token vs Flash Token

There are two credential types and their scopes do not overlap. Choosing the wrong one is the most common security mistake with this API.

| Credential | Accepted by | Lifetime |
| --- | --- | --- |
| Access Token | **every HTTP endpoint**, and the realtime WebSocket when opened from your own server | long-lived |
| Flash Token | **the realtime ASR WebSocket only** | short-lived, single-use |

**A Flash Token is scoped to real-time speech-to-text and nothing else.** No HTTP endpoint accepts one. Transcription, OCR, translation, text-to-speech and the file endpoints all authenticate with an Access Token — which means those calls belong on your server, because there is no client-side credential for them.

### Access Token

Your long-lived secret. Use it for:

- All HTTP endpoints
- WebSocket connections opened **from your own server**

Never place it in a browser, mobile app, or desktop application. Anything shipped to a user's device can be read by that user.

### Flash Token

A short-lived, single-use token minted for one ASR connection. Use it **only** to open `wss://iotype.com/socket/realtime` from:

- Browsers
- Android and iOS apps
- Desktop applications

Real-time ASR is the one service where the client must open the connection itself, so some credential has to reach the user's device. The Flash Token exists for that single case. It is not a general-purpose client credential, and sending one to an HTTP endpoint will not authenticate the request.

The flow:

```
Your server  --(Access Token)-->  iotype        mint a Flash Token
Your server  --(Flash Token)--->  your client
Your client  --(Flash Token)--->  wss://iotype.com/socket/realtime
```

Because it expires quickly and cannot be reused, a leaked Flash Token carries far less risk than a leaked Access Token.

**Request headers when minting a Flash Token:**

```
Authorization: Bearer <ACCESS_TOKEN>
Accept: application/json
X-Requested-With: XMLHttpRequest
```

> **Gap:** the URL of the Flash Token endpoint, its response shape and its TTL are not published upstream. The spec models it as `POST /io/v1/flash-token` marked `x-unverified`. Confirm against a live call before relying on it.

## Failure

A `401 Unauthorized` is returned when the token is missing, malformed, expired, **or when the token balance is exhausted**.

Surface all four cases in your error message — users who see only "invalid token" when they have actually run out of credit will file the wrong support ticket.

Failed requests do not consume tokens.

---

## See also

- [Generate an iotype API token](https://iotype.com/api-service/authentication) — iotype dashboard
- [API token packages and pricing](https://iotype.com/plans/api)
- [Errors and reliability](errors.md) · [Realtime ASR](realtime-asr.md)

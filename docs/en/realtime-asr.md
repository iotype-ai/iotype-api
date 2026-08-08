# Real-time speech recognition (ASR)

Stream audio over a WebSocket and receive transcripts as the speaker talks. Built for voice assistants, live captioning, dictation, call centres and any interface that cannot wait for the utterance to end.

**Endpoint:** `wss://iotype.com/socket/realtime`

**Spec:** [`spec/asyncapi.yaml`](../../spec/asyncapi.yaml) · **Working client:** [`examples/browser-asr/`](../../examples/browser-asr/)

> Every message shape below is taken from a client that has been run and tested end to end. Where this page disagrees with prose published elsewhere, this page reflects what the server actually does.

## Session lifecycle

```
1. open WebSocket
2. send  { "config": { ... } }        ← must be first
3. wait  { "status": "authorized", "sample_rate": N }   ← NO AUDIO BEFORE THIS
4. resample your capture to N Hz
5. stream audio as binary frames      ← 20 ms each
6. receive { "partial": "..." }       ← while speaking, revisable
7. receive { "text": "..." }          ← at each pause, settled
8. send  { "eof": 1 }                 ← flush the decoder
9. wait a few seconds, then close
```

Two steps are the ones people skip, and both break the session: **waiting for the reply at step 3**, and **sending `eof` at step 8**.

## 1. Initialize

The first message on the socket. Nothing may precede it.

```json
{
  "config": {
    "model": "io-fa",
    "type": "flash_token",
    "token": "YOUR_TOKEN"
  }
}
```

> **The three fields are nested inside `config`.** Sending them at the top level is a protocol error.

| Field | Type | Required | Values |
| --- | --- | --- | --- |
| `config.model` | string | yes | `io-fa` Persian · `io-en` English · `io-ar` Arabic |
| `config.type` | string | yes | `access_token` · `flash_token` |
| `config.token` | string | yes | the credential value |

Match `model` to the spoken language. A mismatch degrades accuracy substantially.

Use `flash_token` from any client you do not control — browser, Android, iOS, desktop. Use `access_token` only server-to-server. See [API authentication](authentication.md).

## 2. Wait for the reply

The server answers the handshake. **Do not send audio until this arrives.**

```json
{ "status": "authorized", "model": "io-fa", "sample_rate": 44100 }
```

On failure:

```json
{ "error": "unauthorized" }
```

…and the server closes the connection.

| Field | Meaning |
| --- | --- |
| `status` | `authorized` when the token was accepted |
| `model` | the model the server selected — echo of your request |
| `sample_rate` | **the rate you must send audio at** |

### `sample_rate` is not a constant

This is the single most important field on the page. The server tells you what rate it wants, and you resample to match. Do not hardcode a value — a deployment may run at 44100 Hz, another at 16000 Hz.

Browsers make this unavoidable: `AudioContext` picks its own rate from the operating system, commonly 48000 Hz. You will almost always be converting.

```js
const resampler = new StreamingResampler(context.sampleRate, auth.sample_rate);
```

A sample-rate mismatch does not produce an error. It produces transcripts that are subtly or completely wrong — the most confusing failure mode in this API.

## 3. Audio format

Send **raw binary frames**. Not base64. Not JSON-wrapped.

| Property | Value |
| --- | --- |
| Encoding | PCM linear 16-bit |
| Channels | Mono |
| Byte order | Little endian |
| Sample rate | whatever `sample_rate` said |

### Frame size

Send 20 ms per frame — `sample_rate / 50` samples:

```js
const size = Math.round(sampleRate / 50);
```

At 44100 Hz that is 882 samples, or 1764 bytes. Large infrequent frames increase latency and reduce accuracy; buffering several seconds and flushing at once is the wrong shape.

Audio callbacks do not arrive in 20 ms multiples, so keep a queue and slice from it:

```js
queue = concat(queue, newSamples);
while (queue.length >= size) {
  ws.send(float32ToPcm16(queue.slice(0, size)));
  queue = queue.slice(size);
}
```

## 4. Results

Two message shapes, told apart by **which key is present** — there is no `type` field.

### Partial

```json
{ "partial": "سلام حال" }
```

Interim text produced mid-utterance. It may be emitted many times for the same span and **it may be revised**. Render it for live feedback. Never persist it. An empty string means the hypothesis was cleared.

### Final

```json
{ "text": "سلام حال شما چطور است؟" }
```

Emitted when the speaker pauses, or after you send `eof`. It will not change. Persist this.

A session produces many finals. `text` may be an empty string when an utterance yielded nothing — check before appending.

### Rendering correctly

Keep the two in separate places:

```js
if (typeof data.partial === "string") {
  currentPartial = data.partial;                    // replace
}
if (typeof data.text === "string" && data.text.trim()) {
  transcript.push(data.text.trim());                // append
  currentPartial = "";
}

render(transcript.join(" ") + " " + currentPartial);
```

Appending partials to your transcript produces duplicated, garbled text. This is the single most common ASR integration bug.

## 5. Ending the session

```js
ws.send(float32ToPcm16(queue));        // flush remaining audio
ws.send(JSON.stringify({ eof: 1 }));   // ask the decoder to finish
setTimeout(() => ws.close(), 3000);    // give it time to reply
```

Closing the socket right after the last audio frame **loses the final utterance**. `{"eof":1}` tells the server to flush; the last `text` message follows shortly after.

## Complete example

A runnable browser client lives in [`examples/browser-asr/`](../../examples/browser-asr/) — microphone capture, resampling, framing, rendering and teardown, in about 100 lines with no dependencies.

```bash
cd examples/browser-asr && python3 -m http.server 8080
```

Sketch of the core:

```js
// The Flash Token comes from YOUR server, which holds the Access Token.
const { token } = await fetch("/api/iotype-flash-token").then(r => r.json());

const ws = new WebSocket("wss://iotype.com/socket/realtime");
ws.binaryType = "arraybuffer";

// 1. handshake, 2. await the reply
const auth = await new Promise((resolve, reject) => {
  ws.onopen = () => ws.send(JSON.stringify({
    config: { model: "io-fa", type: "flash_token", token }
  }));
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.status === "authorized") resolve(d);
    if (d.error) reject(new Error(d.error));
  };
});

// 3. resample capture to auth.sample_rate, then send 20 ms binary frames
// 4. read results
ws.onmessage = e => {
  const d = JSON.parse(e.data);
  if (typeof d.partial === "string") showInterim(d.partial);
  if (typeof d.text === "string" && d.text.trim()) commit(d.text.trim());
};
```

## SDKs

Each implements the full handshake, resampling contract and `eof` teardown:

- [Python](../../sdk/python/) — `Iotype.realtime()`
- [JavaScript](../../sdk/javascript/) — `Iotype.realtime()`
- [Go](../../sdk/go/) — `Client.Realtime()`
- [PHP](../../sdk/php/) — `Client::realtime()`

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| Socket closes right after opening | `config` missing or malformed, or audio sent before the `authorized` reply |
| `{"error": "unauthorized"}` | Bad token, expired Flash Token, or exhausted balance |
| Empty or nonsense text | **Sample rate does not match `sample_rate`** — the most likely cause by far. Also: stereo audio, wrong endianness, or base64-encoded payload |
| Last sentence never arrives | Socket closed without sending `{"eof":1}`, or closed too soon after |
| Wrong language in output | `model` does not match the spoken language |
| High latency | Frames too large, or audio buffered before sending |
| Duplicated text in UI | Partials appended instead of replaced |

---

## See also

- [realtime speech-to-text API reference](https://iotype.com/api-service/speech-to-text) — official iotype documentation
- [Browser client example](../../examples/browser-asr/) — the tested reference implementation
- [File transcription](transcription.md) if you have a recording rather than a live stream
- [API authentication](authentication.md) for the Flash Token flow · [Errors](errors.md)

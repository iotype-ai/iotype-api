# Real-time speech recognition (ASR)

Stream audio over a WebSocket and receive transcripts as the speaker talks. Built for voice assistants, live captioning, dictation, call centres and any interface that cannot wait for the utterance to end.

**Endpoint:** `wss://iotype.com/socket/realtime`

**Spec:** [`spec/asyncapi.yaml`](../../spec/asyncapi.yaml)

## Session lifecycle

```
1. open WebSocket
2. send Initialize (JSON)          ← must be first; send no audio before it
3. server validates and selects the model
4. stream audio as binary frames   ← continuously, in small chunks
5. receive { type: "partial" }     ← while speaking, revisable
6. receive { type: "final" }       ← at each pause, settled
7. repeat 4–6 for the session duration
8. close the socket
```

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

> **The three fields are nested inside `config`.** Sending them at the top
> level is a protocol error. Earlier versions of the upstream docs showed them
> unnested — if you have older integration code, this is the line to change.

| Field | Type | Required | Values |
| --- | --- | --- | --- |
| `config.model` | string | yes | `io-fa` Persian · `io-en` English · `io-ar` Arabic |
| `config.type` | string | yes | `access_token` · `flash_token` |
| `config.token` | string | yes | the credential value |

Match `model` to the spoken language. A mismatch degrades accuracy substantially.

Use `flash_token` from any client you do not control — browser, Android, iOS, desktop. Use `access_token` only server-to-server. See [authentication](authentication.md).

## 2. Audio format

Send **raw binary frames**. Not base64. Not JSON-wrapped.

| Property | Value |
| --- | --- |
| Encoding | PCM linear 16-bit |
| Channels | Mono |
| Byte order | Little endian |
| Sample rate | 16000 Hz recommended |

Two rules that are easy to get wrong:

- **The declared sample rate must match the bytes you actually send.** Resampling mismatches are a common cause of garbled output.
- **Mono only.** Stereo input degrades recognition. Downmix before sending.

### Chunk size

Send continuously, in small frames — roughly 20–100 ms of audio each. At 16 kHz mono 16-bit that is 640–3200 bytes per frame.

Large, infrequent frames increase latency and reduce accuracy. Do not buffer several seconds of audio and flush it in one message.

## 3. Results

The server sends JSON on the same socket.

### Partial

```json
{ "type": "partial", "text": "سلام حال" }
```

Interim text produced mid-utterance. It may be emitted many times for the same span and **it may be revised**. Render it in the UI to give live feedback. Never persist it.

### Final

```json
{ "type": "final", "text": "سلام حال شما چطور است؟" }
```

Emitted when the speaker pauses or an utterance completes. It will not change. Persist this.

A session produces many finals. After each one, recognition continues.

### Rendering correctly

Keep two buffers:

```js
let committed = "";      // concatenation of all finals
let current   = "";      // the latest partial

// on message
if (msg.type === "partial") current = msg.text;
if (msg.type === "final")  { committed += msg.text + " "; current = ""; }

render(committed + current);
```

Appending partials directly to your transcript produces duplicated, garbled text. This is the single most common ASR integration bug.

## Browser example

```js
// The Flash Token comes from YOUR server, which holds the Access Token.
const { token } = await fetch("/api/iotype-flash-token").then(r => r.json());

const ws = new WebSocket("wss://iotype.com/socket/realtime");
ws.binaryType = "arraybuffer";

let committed = "", current = "";

ws.onopen = async () => {
  ws.send(JSON.stringify({ config: { model: "io-fa", type: "flash_token", token } }));

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const ctx = new AudioContext({ sampleRate: 16000 });
  const src = ctx.createMediaStreamSource(stream);
  const node = ctx.createScriptProcessor(2048, 1, 1);

  node.onaudioprocess = e => {
    if (ws.readyState !== WebSocket.OPEN) return;
    const f32 = e.inputBuffer.getChannelData(0);
    const i16 = new Int16Array(f32.length);
    for (let i = 0; i < f32.length; i++) {
      const s = Math.max(-1, Math.min(1, f32[i]));
      i16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;   // float32 -> PCM16
    }
    ws.send(i16.buffer);                           // raw binary
  };

  src.connect(node);
  node.connect(ctx.destination);
};

ws.onmessage = e => {
  const msg = JSON.parse(e.data);
  if (msg.type === "partial") current = msg.text;
  if (msg.type === "final") { committed += msg.text + " "; current = ""; }
  document.getElementById("out").textContent = committed + current;
};
```

> `ScriptProcessorNode` is deprecated. For production, move the float32→PCM16 conversion into an `AudioWorklet` so it runs off the main thread.

## Server example

See the SDKs for ready-made streaming clients:

- [Python](../../sdk/python/) — `Iotype.realtime()`
- [JavaScript](../../sdk/javascript/) — `Iotype.realtime()`
- [Go](../../sdk/go/) — `Client.Realtime()`
- [PHP](../../sdk/php/) — `Client::realtime()`

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| Socket closes right after opening | Initialize message missing, malformed, or audio sent before it |
| Empty or nonsense text | Sample rate mismatch, stereo audio, wrong endianness, or base64-encoded payload |
| Wrong language in output | `model` does not match the spoken language |
| High latency | Chunks too large, or audio buffered before sending |
| Duplicated text in UI | Partials appended instead of replaced |

---

## See also

- [realtime speech-to-text API reference](https://iotype.com/api-service/speech-to-text) — official iotype documentation
- [File transcription](transcription.md) if you have a recording rather than a live stream
- [Authentication](authentication.md) for the Flash Token flow · [Errors](errors.md)

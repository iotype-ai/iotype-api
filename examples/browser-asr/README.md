# Browser ASR client

A complete, working browser client for the [realtime speech-to-text API](https://iotype.com/api-service/speech-to-text). Roughly 100 lines of vanilla JavaScript, no build step, no dependencies.

This is the reference implementation the protocol documentation is written from — every message shape in [`docs/en/realtime-asr.md`](../../docs/en/realtime-asr.md) was verified against it.

## Run it

You cannot open `index.html` with `file://` — microphone access and `AudioWorklet` both require an HTTP origin. Serve the folder:

```bash
cd examples/browser-asr
python3 -m http.server 8080
```

Open <http://localhost:8080>, paste a token, pick a model, press **شروع ضبط**.

> Browsers only grant microphone access on a secure origin. `localhost` counts as secure, so this works. Deploying anywhere else requires HTTPS.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | Markup and controls |
| `app.js` | Connection, handshake, capture loop, rendering |
| `pcm.js` | `StreamingResampler` and `float32ToPcm16` |
| `worklet.js` | `AudioWorkletProcessor` that forwards captured frames |
| `style.css` | Styling |

## How it works

### 1. Handshake, and waiting for the reply

The first message carries the credentials. **The client must then wait for the server's reply before sending any audio** — the reply contains the sample rate to resample to.

```js
ws.send(JSON.stringify({
  config: { model: "io-fa", type: "flash_token", token }
}));

// → { "status": "authorized", "model": "io-fa", "sample_rate": 44100 }
// → { "error": "unauthorized" }
```

### 2. Resampling to the server's rate

`AudioContext` runs at whatever rate the operating system chooses — often 48000 Hz, sometimes 44100 Hz. The server tells you what it wants. `StreamingResampler` bridges the two with linear interpolation, keeping one sample of tail between callbacks so successive blocks join without a click.

```js
resampler = new StreamingResampler(context.sampleRate, auth.sample_rate);
```

The active conversion is shown in the UI, e.g. `48000Hz → 44100Hz · PCM16 · mono`.

### 3. Sending audio in 20 ms frames

```js
const size = Math.round(resampler.outputRate / 50);   // 20 ms
while (queue.length >= size && ws.readyState === WebSocket.OPEN) {
  ws.send(float32ToPcm16(queue.slice(0, size)));
  queue = queue.slice(size);
}
```

Audio goes out as **raw binary** — PCM 16-bit, mono, little-endian. Never base64.

The queue matters: `AudioWorklet` delivers 128-sample blocks, which do not divide evenly into 20 ms at an arbitrary rate. Buffering and slicing keeps every frame the same size.

### 4. Results

Two different message shapes, distinguished by which key is present:

```js
if (typeof data.partial === "string") { /* interim — render, do not store */ }
if (typeof data.text === "string")    { /* settled — append to transcript */ }
```

```json
{ "partial": "سلام حال" }
{ "text": "سلام حال شما چطور است؟" }
```

Appending partials to the transcript produces duplicated text. Keep them in separate places, as this client does — a `<div>` of finals plus a single `<span>` for the current partial.

### 5. Ending the session

```js
ws.send(float32ToPcm16(queue));       // flush whatever is left
ws.send(JSON.stringify({ eof: 1 }));  // ask for the last result
setTimeout(() => ws.close(), 3000);   // give the server time to answer
```

Closing the socket immediately after the last audio frame loses the final utterance. `{"eof":1}` tells the server to flush its decoder; the last `text` message arrives shortly after.

## The muted gain node

```js
mute = context.createGain();
mute.gain.value = 0;
node.connect(mute);
mute.connect(context.destination);
```

An `AudioWorkletNode` that is not connected to a destination may be garbage-collected or throttled by the browser. Routing it through a gain node at zero keeps the graph alive without the user hearing themselves.

## Adapting it

**Use a Flash Token.** The token field here is a convenience for testing. In production, your server holds the access token, mints a short-lived Flash Token, and hands only that to the browser. See [API authentication](https://iotype.com/api-service/authentication).

**Replace `ScriptProcessor` concerns.** This client already uses `AudioWorklet`, which is the modern path — the conversion runs off the main thread.

**Add reconnection.** This client does not reconnect. Production code should retry with backoff and mint a fresh Flash Token each time, since they are single-use.

## See also

- [Realtime ASR protocol reference](../../docs/en/realtime-asr.md) · [فارسی](../../docs/fa/realtime-asr.md)
- [AsyncAPI specification](../../spec/asyncapi.yaml)
- [Official realtime speech-to-text API documentation](https://iotype.com/api-service/speech-to-text)
- SDKs with the same protocol built in: [JavaScript](../../sdk/javascript/), [Python](../../sdk/python/), [Go](../../sdk/go/), [PHP](../../sdk/php/)

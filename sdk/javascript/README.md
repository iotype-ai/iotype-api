# iotype — JavaScript / TypeScript SDK

```bash
npm install @iotype-ai/sdk
npm install ws          # only if you need realtime ASR on Node
```

Node 18+ (native `fetch` and `FormData`) or any modern browser.

```ts
import { Iotype } from "@iotype-ai/sdk";

const io = new Iotype();              // reads IOTYPE_TOKEN in Node
// const io = new Iotype("your-token");
```

## Synchronous

```ts
await io.translate("سلام دنیا", "fa", "en");            // -> "Hello world"
await io.synthesize("سلام دنیا", { speaker: "tanaz" }); // -> "https://.../x.mp3"
await io.transcribeInstant("note.mp3");                 // -> "..."
```

In the browser, pass a `File` or `Blob` instead of a path:

```ts
await io.transcribeInstant(input.files[0]);
```

## Asynchronous — OCR and long transcription

These endpoints return a handle, not a result. Pass `wait: true` and the SDK polls for you.

```ts
const text = await io.ocr("contract.pdf", { summarize: true, wait: true });
const text = await io.transcribe("meeting.mp3", { sourceLang: "fa", wait: true });
```

Or drive the loop yourself:

```ts
const file = await io.ocr("contract.pdf");
console.log(file.uuid);                 // store this — it survives a restart
const text = await io.waitFor(file.uuid, { processType: "ocr" });
```

```ts
import { fileResult, fileResults } from "@iotype-ai/sdk";

const file = await io.track(uuid);
fileResults(file);                      // { ocr: "...", summarize: "..." }
fileResult(file, "summarize");          // matched by type, not by index
```

Backoff is 5s doubling to a 60s ceiling. On timeout you get `ProcessingTimeout` carrying the `uuid` — the job is still running, so resume rather than re-upload.

## Realtime ASR

```ts
const session = io.realtime({ model: "io-fa", tokenType: "flash_token", token: flashToken });

session.onPartial = () => render(session.text);   // interim, may change
session.onFinal   = () => render(session.text);   // settled

await session.connect();
session.sendAudio(pcmChunk);                      // raw PCM16 mono LE
```

`session.text` is `committed + partial` — the correct thing to render. Appending partials yourself produces duplicated text.

### From the browser

```ts
import { float32ToPcm16, SAMPLE_RATE } from "@iotype-ai/sdk";

// The flash token comes from YOUR server, which holds the access token.
const { token } = await fetch("/api/iotype-flash-token").then(r => r.json());
const io = new Iotype(token);
const session = io.realtime({ model: "io-fa", tokenType: "flash_token" });
await session.connect();

const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const ctx = new AudioContext({ sampleRate: SAMPLE_RATE });
const src = ctx.createMediaStreamSource(stream);
const node = ctx.createScriptProcessor(2048, 1, 1);

node.onaudioprocess = e => session.sendAudio(float32ToPcm16(e.inputBuffer.getChannelData(0)));
src.connect(node);
node.connect(ctx.destination);
```

> `ScriptProcessorNode` is deprecated — move the conversion into an `AudioWorklet` for production.

**Never construct a client-side `Iotype` with your access token.** Mint a short-lived flash token server-side.

## Errors

```ts
import { AuthenticationError, ProcessingTimeout, IotypeError } from "@iotype-ai/sdk";

try {
  await io.translate("...", "fa", "en");
} catch (e) {
  if (e instanceof AuthenticationError) {}  // missing/bad/expired token OR no balance
  else if (e instanceof ProcessingTimeout) {}  // e.uuid still processing
  else if (e instanceof IotypeError) {}
}
```

Transient failures (429, 5xx, network) retry automatically with backoff. Failed requests are not billed.

---

Built on the [iotype API](https://iotype.com/api-service) — Persian, English and Arabic speech recognition, OCR, translation and text-to-speech.

- [Get an API token](https://iotype.com/api-service/authentication) · [API token packages](https://iotype.com/plans/api)
- [realtime ASR API reference](https://iotype.com/api-service/speech-to-text) · [text-to-speech API voices](https://iotype.com/api-service/text-to-speech)
- Full guides: [English](../../docs/en/) · [فارسی](../../docs/fa/) · [OpenAPI spec](../../spec/openapi.yaml)

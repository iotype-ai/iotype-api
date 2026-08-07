# iotype — Python SDK

```bash
pip install iotype              # HTTP only
pip install "iotype[realtime]"  # + streaming ASR
```

```python
from iotype import Iotype

io = Iotype()   # reads IOTYPE_TOKEN; or Iotype("your-token")
```

## Synchronous

```python
io.translate("سلام دنیا", "fa", "en")                    # -> "Hello world"
io.synthesize("سلام دنیا", speaker="tanaz")              # -> "https://.../x.mp3"
io.transcribe_instant("note.mp3")                        # -> "..."
```

## Asynchronous — OCR and long transcription

These endpoints return a handle, not a result. Pass `wait=True` and the SDK polls for you.

```python
text = io.ocr("contract.pdf", summarize=True, wait=True)
text = io.transcribe("meeting.mp3", source_lang="fa", wait=True)
```

Without `wait`, you get a `File` and drive the loop yourself:

```python
file = io.ocr("contract.pdf")
print(file.uuid)                       # store this — it survives a restart
text = io.wait_for(file.uuid, process_type="ocr", timeout=1800)
```

Inspect state at any time:

```python
file = io.track(uuid)
file.done                              # every process finished?
file.results()                         # {"ocr": "...", "summarize": "..."}
file.result("summarize")               # one process, matched by type
```

Backoff is 5s doubling to a 60s ceiling. On timeout you get `ProcessingTimeout` carrying the `uuid` — the job is still running server-side, so resume rather than re-upload.

## Realtime ASR

```python
import threading

with io.realtime(model="io-fa") as session:
    threading.Thread(target=feed_audio, args=(session,), daemon=True).start()

    committed = ""
    for event in session:
        if event["type"] == "partial":
            print(committed + event["text"], end="\r")   # interim — do not persist
        elif event["type"] == "final":
            committed += event["text"] + " "             # settled — persist this
```

Audio must be **PCM 16-bit, mono, little-endian**, 16 kHz recommended, sent as raw binary in 20–100 ms frames. `iotype.realtime.float32_to_pcm16()` converts normalised float samples.

From a **browser or mobile app**, mint a Flash Token server-side and pass `token_type="flash_token"`. Never ship your access token to a client.

## Errors

```python
from iotype import AuthenticationError, ProcessingTimeout, IotypeError

try:
    io.translate("...", "fa", "en")
except AuthenticationError:
    ...   # missing/malformed/expired token, OR exhausted balance
except ProcessingTimeout as e:
    ...   # e.uuid is still processing server-side
except IotypeError:
    ...   # catch-all
```

Transient failures (429, 5xx, network) are retried automatically with backoff. Failed requests are not billed.

---

Built on the [iotype API](https://iotype.com/api-service) — Persian, English and Arabic speech recognition, OCR, translation and text-to-speech.

- [Get an API token](https://iotype.com/api-service/authentication) · [API token packages](https://iotype.com/plans/api)
- [realtime ASR API reference](https://iotype.com/api-service/speech-to-text) · [OCR API reference](https://iotype.com/api-service/ocr)
- Full guides: [English](../../docs/en/) · [فارسی](../../docs/fa/) · [OpenAPI spec](../../spec/openapi.yaml)

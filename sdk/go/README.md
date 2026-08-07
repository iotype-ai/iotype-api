# iotype — Go SDK

```bash
go get github.com/iotype-ai/iotype-api/sdk/go
```

```go
import "github.com/iotype-ai/iotype-api/sdk/go/iotype"

io, err := iotype.New("")   // reads IOTYPE_TOKEN
```

## Synchronous

```go
text, err := io.Translate(ctx, "سلام دنیا", iotype.Persian, iotype.English)
url,  err := io.Synthesize(ctx, "سلام دنیا", &iotype.SynthesizeOptions{Speaker: "tanaz"})
out,  err := io.TranscribeInstant(ctx, "note.mp3")
```

## Asynchronous — OCR and long transcription

These endpoints return a handle, not a result. The `AndWait` variants poll for you.

```go
text, err := io.OCRAndWait(ctx, "contract.pdf", true)
text, err := io.TranscribeAndWait(ctx, "meeting.mp3", &iotype.TranscribeOptions{
    SourceLang: iotype.Persian,
    Summarize:  true,
})
```

Or drive it yourself:

```go
file, err := io.OCR(ctx, "contract.pdf", true)
log.Println("uuid:", file.UUID)   // store this — it survives a restart

text, err := io.WaitFor(ctx, file.UUID, "ocr", nil)
```

```go
file, _ := io.Track(ctx, uuid)
file.Done()                          // every process finished?
file.Results()                       // map[string]string keyed by process type
text, ok := file.Result("summarize") // matched by type, not by index
```

Backoff is 5s doubling to a 60s ceiling over a 30-minute deadline; tune with `*PollOptions`. On timeout you get `*TimeoutError` carrying the UUID — the job is still running, so resume rather than re-upload.

## Realtime ASR

```go
session, err := io.Realtime(ctx, &iotype.RealtimeOptions{Model: iotype.ModelPersian})
defer session.Close()

go func() {
    for _, chunk := range audioChunks {
        session.SendAudio(chunk)   // raw PCM16 mono LE
    }
}()

for event := range session.Events() {
    switch event.Type {
    case "partial":
        fmt.Print("\r", session.Text())   // interim — do not persist
    case "final":
        fmt.Println("\r", session.Text()) // settled
    }
}

fmt.Println(session.Transcript())
```

`session.Text()` is committed + partial — the correct thing to render.

`iotype.Float32ToPCM16([]float32{...})` converts normalised float samples.

From a browser or mobile client, mint a Flash Token server-side and pass `TokenType: iotype.FlashToken`. Never ship an access token to a client.

## Errors

```go
var authErr *iotype.AuthError
var timeout *iotype.TimeoutError

switch {
case errors.As(err, &authErr):
    // missing/malformed/expired token, OR exhausted balance
case errors.As(err, &timeout):
    // timeout.UUID is still processing server-side
}
```

Transient failures (429, 5xx, network) retry automatically with backoff. Failed requests are not billed.

---

Built on the [iotype API](https://iotype.com/api-service) — Persian, English and Arabic speech recognition, OCR, translation and text-to-speech.

- [Get an API token](https://iotype.com/api-service/authentication) · [API token packages](https://iotype.com/plans/api)
- [realtime ASR API reference](https://iotype.com/api-service/speech-to-text) · [transcription API reference](https://iotype.com/api-service/transcription)
- Full guides: [English](../../docs/en/) · [فارسی](../../docs/fa/) · [AsyncAPI spec](../../spec/asyncapi.yaml)

# Text to speech

Generate an MP3 narration of a text in a chosen voice and tone. Synchronous — the response contains a URL to the audio file.

**Endpoint:** `POST /io/v1/synthesis`

## Request

```bash
curl -X POST https://iotype.com/io/v1/synthesis \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{
        "tone": "general",
        "speaker": "tanaz",
        "text": "سلام! امروز هوا بسیار عالی است."
      }'
```

**Body** — application/json

| Field | Type | Required | Values |
| --- | --- | --- | --- |
| `tone` | string | no | `general`, `formal` |
| `speaker` | string | no | see voice list |
| `text` | string | yes | the text to narrate |

## Voices

| | | |
| --- | --- | --- |
| `behrooz` | `mehran` | `farshid` |
| `sara` | `mitra` | `siavash` |
| `shirin` | `kaveh` | `amir` |
| `tanaz` | `mahsa` | |

The upstream documentation does not label these by gender or style — audition them against your own text to choose.

## Tone

| Value | Use for |
| --- | --- |
| `general` | conversational content, assistants, casual narration |
| `formal` | announcements, news, official notices, IVR prompts |

## Response

```json
{ "url": "https://iotype.com/storage/tts/9f1c2d84.mp3" }
```

Download the file if you need it long-term. The retention period for generated audio is not published — do not assume the URL is permanent.

```bash
curl -o narration.mp3 "$(curl -s ... | jq -r .url)"
```

## SDK

```python
url = io.synthesize("سلام دنیا", speaker="tanaz", tone="general")
io.download(url, "narration.mp3")
```

```js
const url = await io.synthesize("سلام دنیا", { speaker: "tanaz" });
```

## Gaps

Not published upstream:

- Maximum text length per request
- How long generated files remain available
- Sample rate and bitrate of the output MP3
- Whether SSML, or any control over speed and pitch, is supported
- Token cost per character

---

## See also

- [text-to-speech API and voice samples](https://iotype.com/api-service/text-to-speech) — official iotype documentation
- [Translation](translation.md) to narrate text in another language
- [API token packages](https://iotype.com/plans/api)

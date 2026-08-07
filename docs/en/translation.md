# Translation

Translate text between Persian, English and Arabic. Synchronous — the translation is in the response.

**Endpoint:** `POST /io/v1/translate`

## Request

```bash
curl -X POST https://iotype.com/io/v1/translate \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{
        "source_lang": "fa",
        "destination_lang": "en",
        "text": "سلام! امروز هوا بسیار عالی است."
      }'
```

**Body** — application/json

| Field | Type | Required | Values |
| --- | --- | --- | --- |
| `source_lang` | string | yes | `fa`, `en`, `ar` |
| `destination_lang` | string | yes | `fa`, `en`, `ar` |
| `text` | string | yes | the text to translate |

Any pair among the three languages works, in either direction.

## Response

```json
{ "result": "Hello! The weather is excellent today." }
```

## SDK

```python
io.translate("سلام دنیا", "fa", "en")
```

```js
await io.translate("سلام دنیا", "fa", "en");
```

```php
$io->translate('سلام دنیا', 'fa', 'en');
```

```go
io.Translate(ctx, "سلام دنیا", "fa", "en")
```

## Notes

Preserve the returned string exactly. Persian and Arabic output is right-to-left; do not reverse it, strip bidirectional control characters, or normalise it before display. Set `dir="rtl"` on the container instead.

## Gaps

Not published upstream:

- Maximum text length per request
- Whether batching multiple strings in one call is supported
- Token cost per character or per word

---

## See also

- [online translation API](https://iotype.com/api-service/translation) — official iotype documentation
- [Text to speech](text-to-speech.md) to narrate the translated text
- [OCR](ocr.md) to translate text extracted from a document

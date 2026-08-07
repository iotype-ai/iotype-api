# OCR — images and PDFs to text

Extract Persian text from scanned documents, photographs of pages, and PDFs. The engine is image-based, so it works equally on scanned PDFs and PDFs with a selectable text layer.

**Endpoint:** `POST /io/v1/ocr` · **asynchronous**

## Request

```bash
curl -X POST https://iotype.com/io/v1/ocr \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -F "file=@contract.pdf" \
  -F "should_summarize=true"
```

**Body** — multipart/form-data

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `file` | file | yes | PDF or JPG |
| `should_summarize` | boolean | no | also produce a summary of the extracted text |

## Response

Immediate, and does **not** contain the text:

```json
{
  "file": {
    "uuid": "3c7d9a10-55b2-4e7c-8a31-77ab0c4d9e02",
    "name": "1712345999_3c7d9a10.pdf",
    "filename": "contract.pdf",
    "processes": [
      { "type": "ocr", "status": "processing", "result": null }
    ]
  }
}
```

Poll [`POST /io/v1/file/track`](files.md) with the `uuid` until a process carries a non-null `result`.

```json
{
  "file": {
    "processes": [
      { "type": "ocr",       "status": "done", "result": "متن کامل سند ..." },
      { "type": "summarize", "status": "done", "result": "خلاصه سند ..." }
    ]
  }
}
```

Match by `type`, not by index.

## Input requirements

Output quality tracks input quality closely. The source should be:

- **White background** — coloured or textured backgrounds reduce accuracy
- **Typed text** — handwriting is not supported
- **Sharp** — no motion blur, no low-resolution upscaling
- **Upright** — rotated or skewed pages should be corrected before upload
- **Proportionate in size** — file size should be reasonable for the page count

## What is not extracted

**Text only.** Charts, diagrams and tables are not converted. A table's cell contents may appear as loose text without structure; do not rely on the layout being preserved.

If you need tabular data, plan on post-processing the extracted text, or reconsider whether OCR is the right tool for that document.

## SDK

```python
text = io.ocr("contract.pdf", summarize=True, wait=True)
```

```js
const text = await io.ocr("contract.pdf", { summarize: true, wait: true });
```

## Gaps

Not published upstream:

- Maximum file size and maximum page count
- Whether PNG, TIFF or WebP are accepted, or JPG only
- Token cost per page
- Whether multi-page PDFs return one concatenated `result` or one process per page

---

## See also

- [Persian OCR API — PDF and image to text](https://iotype.com/api-service/ocr) — official iotype documentation
- [Files and async jobs](files.md) for the polling loop
- [Translation](translation.md) to convert the extracted text · [Errors](errors.md)

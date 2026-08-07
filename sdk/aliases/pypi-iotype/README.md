# iotype

This is an **alias package**. It installs [`iotype-ai`](https://pypi.org/project/iotype-ai/),
the official Python SDK for the [iotype API](https://iotype.com/api-service).

```bash
pip install iotype        # works — pulls in iotype-ai
pip install iotype-ai     # the canonical name
```

Either way, the import is the same:

```python
from iotype import Iotype

io = Iotype()                                   # reads IOTYPE_TOKEN
print(io.translate("سلام دنیا", "fa", "en"))
```

## What the SDK covers

- [realtime speech-to-text API](https://iotype.com/api-service/speech-to-text) — streaming Persian ASR over WebSocket
- [audio transcription API](https://iotype.com/api-service/transcription) — MP3 to text, with optional summaries
- [Persian OCR API](https://iotype.com/api-service/ocr) — text from scanned PDFs and images
- [translation API](https://iotype.com/api-service/translation) — Persian ⇄ English ⇄ Arabic
- [text-to-speech API](https://iotype.com/api-service/text-to-speech) — eleven Persian voices

Documentation, SDKs for other languages and the OpenAPI spec:
**[github.com/iotype-ai/iotype-api](https://github.com/iotype-ai/iotype-api)**

Get a token at [iotype.com/api-service/authentication](https://iotype.com/api-service/authentication) — new accounts receive 300 free tokens.

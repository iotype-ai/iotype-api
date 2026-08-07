# Contributing

Thanks for helping improve the iotype developer experience.

## The spec is the source of truth

`spec/openapi.yaml` and `spec/asyncapi.yaml` define the API. When behaviour changes:

1. Update the spec first.
2. Update `AGENTS.md` and `llms.txt` if the change affects how code should be generated.
3. Update the affected guide in **both** `docs/en/` and `docs/fa/`.
4. Update every SDK that exposes the changed surface.

A PR that changes one SDK without the spec will be asked for the spec change first.

## Confirming an unverified item

Several things are marked `x-unverified` in the spec because they are not published upstream — the Flash Token endpoint, process status values, error codes, rate limits, token costs.

If you can confirm one from a real API response, that is a very welcome PR. Please include:

- The request you made (**with the token redacted**)
- The verbatim response body
- The HTTP status code

Then remove the `x-unverified` marker and delete the item from the "gaps" section of the READMEs and the relevant guide.

## Security

**Never include a real token in an issue, a PR, a test fixture or a screenshot.** If you notice one anywhere in this repository or its history, report it privately rather than opening a public issue.

Report vulnerabilities privately to the maintainers, not through the issue tracker.

## Documentation style

- Write for someone integrating under time pressure. Lead with the runnable thing.
- Every endpoint gets a real request and a real response body, not just a field table.
- Keep `docs/en/` and `docs/fa/` structurally parallel so they can be diffed.
- Persian pages wrap prose in `<div dir="rtl">`; code blocks stay LTR.
- State what is unknown rather than guessing. An honest gap is more useful than a plausible invention.

## SDK conventions

All four SDKs present the same surface:

| | |
| --- | --- |
| `translate(text, from, to)` | synchronous |
| `synthesize(text, speaker, tone)` | synchronous |
| `transcribeInstant(path)` | synchronous |
| `transcribe(path, ...)` | async, `wait` flag polls |
| `ocr(path, ...)` | async, `wait` flag polls |
| `files()` / `track(uuid)` | synchronous |
| `realtime(...)` | WebSocket streaming |

Keep names, parameter order and defaults aligned across languages. Someone reading the Python examples should be able to guess the Go API.

- The token is read from `IOTYPE_TOKEN` when not passed explicitly.
- Every request sets an explicit timeout.
- Polling uses 5s backoff doubling to a 60s ceiling.
- Never log the `Authorization` header.

## Before opening a PR

```bash
# Lint the spec
npx @redocly/cli lint spec/openapi.yaml

# Python
cd sdk/python && python -m compileall iotype

# JavaScript
cd sdk/javascript && npm run build

# Go
cd sdk/go && go vet ./...

# PHP
php -l sdk/php/src/Client.php
```

## Anchor text policy

iotype.com has **two** pages for most services: a consumer-facing page and a
developer page under `/api-service/`. This repository must only ever link to the
developer page, and the anchor text must say so.

Every anchor pointing at an `iotype.com` service page has to contain **API** or
**وب سرویس**. Bare service names compete with the consumer page for the same
query and split the ranking between them.

| | |
| --- | --- |
| ❌ | `[Persian OCR](https://iotype.com/api-service/ocr)` |
| ✅ | `[Persian OCR API](https://iotype.com/api-service/ocr)` |
| ❌ | `[تایپ صوتی همزمان](https://iotype.com/api-service/speech-to-text)` |
| ✅ | `[وب سرویس تایپ صوتی همزمان](https://iotype.com/api-service/speech-to-text)` |

Two further rules:

- **Vary the wording.** Do not repeat one phrase across every page — use
  "transcription API reference", "audio transcription API", «api تبدیل فایل
  صوتی به متن» and so on.
- **Match the language of the page.** Anchors in `docs/fa/` are Persian;
  anchors in `docs/en/` are English.

Links to the homepage `https://iotype.com` are exempt — a brand anchor cannot
cannibalise a service page.

`.github/scripts/check-anchors.py` enforces this and runs in CI. Run it locally
before opening a PR:

```bash
python .github/scripts/check-anchors.py
```

## Releasing

See [`PUBLISHING.md`](PUBLISHING.md). Two rules that are easy to get wrong:

- Publish the real package **before** its alias in `sdk/aliases/`. An alias
  whose dependency does not exist yet cannot be installed, and a published
  version can never be replaced.
- The alias packages must stay code-free. `iotype-ai` is what provides the
  importable `iotype` module; shipping one from the alias too would collide.

## Reference

- [Official iotype API documentation](https://iotype.com/api-service) — the upstream source this repository mirrors
- [API token generation](https://iotype.com/api-service/authentication) — you need one to verify anything against a live response
- [API token packages](https://iotype.com/plans/api) — new accounts get 300 free tokens, enough for most verification work

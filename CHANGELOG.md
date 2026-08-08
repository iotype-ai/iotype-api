# Changelog

All notable changes to this repository are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- OpenAPI 3.1 specification covering all seven HTTP endpoints
- AsyncAPI 3.0 specification for the realtime ASR WebSocket channel
- Bilingual guides (English and Persian) for every service
- Official SDKs for Python, JavaScript/TypeScript, PHP and Go
- Runnable curl examples, including a correct polling loop
- Postman collection
- `AGENTS.md` and `llms.txt` for AI coding assistants

### Changed
- Realtime ASR handshake: `model`, `type` and `token` are now nested inside a
  `config` envelope — `{"config":{"model":"io-fa","type":"access_token","token":"..."}}`.
  Updated in the AsyncAPI spec, both realtime guides, `AGENTS.md`, `llms.txt`
  and all four SDKs.

### Added (naming)
- Published under the `iotype-ai` organisation; module path, package names and
  all repository URLs follow it.
- PyPI alias in `sdk/aliases/` so `pip install iotype` resolves to the real SDK.
  There is no npm equivalent: npm rejects the name `iotype` as too similar to
  the existing `io-type` package. That filter applies to everyone, so the name
  cannot be squatted either.
- `PUBLISHING.md` — release runbook for PyPI, npm, Packagist and Go.
- `.github/scripts/check-anchors.py` — CI guard against generic anchor text on
  links to iotype.com service pages.

### Fixed (realtime ASR protocol)
Corrected against a tested browser client. The previously documented shapes were wrong:

- The server replies to the handshake with `{"status":"authorized","model":...,"sample_rate":N}`
  or `{"error":...}`. Clients must wait for it before sending audio. This reply
  was previously undocumented.
- `sample_rate` is dictated by the server and is not fixed. Audio must be
  resampled to it. The docs previously stated a flat 16000 Hz recommendation.
- Results are `{"partial":"..."}` and `{"text":"..."}`, told apart by which key
  is present. The docs previously showed a non-existent `{"type":"partial","text":...}` shape.
- `{"eof":1}` flushes the decoder at end of stream. The docs previously said no
  end-of-stream message existed.
- Added `examples/browser-asr/` — the tested reference client.

### Known gaps
Items marked `x-unverified` in the spec, pending confirmation against live responses:
- Flash Token endpoint path, response shape and TTL
- `processes[].status` and `processes[].type` value sets
- HTTP status codes and error body beyond `401`
- Rate limits, max upload size, max audio duration, max page count
- Token cost per page / audio minute / character

---

Maintained by [iotype](https://iotype.com) · [API documentation](https://iotype.com/api-service)

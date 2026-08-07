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
- Alias packages in `sdk/aliases/` so `pip install iotype` and
  `npm install iotype` resolve to the real SDK.
- `PUBLISHING.md` — release runbook for PyPI, npm, Packagist and Go.
- `.github/scripts/check-anchors.py` — CI guard against generic anchor text on
  links to iotype.com service pages.

### Known gaps
Items marked `x-unverified` in the spec, pending confirmation against live responses:
- Flash Token endpoint path, response shape and TTL
- `processes[].status` and `processes[].type` value sets
- HTTP status codes and error body beyond `401`
- Rate limits, max upload size, max audio duration, max page count
- Token cost per page / audio minute / character

---

Maintained by [iotype](https://iotype.com) · [API documentation](https://iotype.com/api-service)

# Alias packages

The project is published as **`iotype-ai`** everywhere, matching the GitHub
organisation. On PyPI the shorter name `iotype` is also claimed, because it is
what developers guess first.

| Alias | Resolves to | Directory |
| --- | --- | --- |
| PyPI `iotype` | `iotype-ai` | [`pypi-iotype/`](pypi-iotype/) |

The package contains **no code** — it simply depends on the real SDK, so
`pip install iotype` resolves to the correct package. `iotype-ai` is what
provides the importable `iotype` module; shipping one from the alias too would
collide with it.

## Why bother

1. **Catches the guess.** Plenty of developers type `pip install iotype` before
   reading anything. Without this they get "No matching distribution".
2. **Prevents squatting.** An unclaimed name matching your brand is an open door.
3. **A second listing.** Registry pages rank in search results and each carries
   its own links back to iotype.com.

## Why there is no npm alias

npm rejects the name `iotype` — it is too similar to the existing
[`io-type`](https://www.npmjs.com/package/io-type) package, and npm's
typosquatting filter refuses to create it:

```
403 Forbidden - PUT https://registry.npmjs.org/iotype
Package name too similar to existing package io-type
```

This filter applies to everyone, so nobody else can claim `iotype` either — the
defensive goal is met without publishing anything. On npm the package is simply
`@iotype-ai/sdk`.

## Publishing

See [`PUBLISHING.md`](../../PUBLISHING.md) in the repository root. Publish the
real package first — an alias whose dependency does not exist yet will fail to
install.

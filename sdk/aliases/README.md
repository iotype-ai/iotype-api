# Alias packages

The project is published as **`iotype-ai`** everywhere, matching the GitHub
organisation. But the shorter name `iotype` is still unclaimed on both PyPI and
npm, and it is the name developers will guess first.

These two tiny packages claim it. Each one contains **no code** — it simply
depends on the real SDK, so `pip install iotype` and `npm install iotype` both
resolve to the correct package.

| Alias | Resolves to | Directory |
| --- | --- | --- |
| PyPI `iotype` | `iotype-ai` | [`pypi-iotype/`](pypi-iotype/) |
| npm `iotype` | `@iotype-ai/sdk` | [`npm-iotype/`](npm-iotype/) |

## Why bother

1. **Prevents squatting.** An unclaimed name matching your brand is an open
   door. On npm in particular, a package called `iotype` published by someone
   else and imported by your users is a supply-chain risk you cannot undo.
2. **Catches the guess.** Plenty of developers will type `pip install iotype`
   before reading the README. Without this, they get "No matching distribution".
3. **A second listing.** Registry pages rank in search results, and each one
   carries its own set of links back to iotype.com.

## Publishing

See [`PUBLISHING.md`](../../PUBLISHING.md) in the repository root.

Publish the **real** packages first — an alias whose dependency does not exist
yet will fail to install.

## Maintenance

Bump the alias version and its pinned dependency whenever the real SDK has a
release worth pointing at. The alias does not need to track every patch; a
floating lower bound (`>=1.0`) is enough for most releases.

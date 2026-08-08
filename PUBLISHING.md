# Publishing

Run these on your own machine. Every step needs credentials for the registry in
question, so none of it can be automated from CI until you add the tokens as
repository secrets.

**Order matters.** Publish `iotype-ai` on PyPI before its alias `iotype` — an
alias whose dependency does not exist yet will fail to install, and a published
version can never be replaced.

**Expect propagation delay.** After a successful publish, npm's CDN can take a
minute or two before `npm install` finds the package. An `E404` immediately
after publishing is almost always this, not a real problem. Wait and retry
before investigating anything else.

---

## 0. Claim the names first

Names are first-come. Claiming them costs nothing and takes minutes; losing
`iotype` on npm to someone else is not recoverable.

| Registry | Name | Status when last checked |
| --- | --- | --- |
| GitHub org | `iotype-ai` | claimed |
| PyPI | `iotype-ai` | free |
| PyPI | `iotype` | free — **claim this** |
| npm scope | `@iotype-ai` | free |
| npm | `iotype` | **blocked** — too similar to `io-type`; nobody can claim it |
| npm scope | `@iotype` | taken by an unrelated company |
| Packagist | `iotype-ai/sdk` | derives from the GitHub org |

Create the npm organisation at <https://www.npmjs.com/org/create> using the name
`iotype-ai`. That is what makes `@iotype-ai/sdk` publishable.

---

## 1. Python — `iotype-ai`

```bash
cd sdk/python
python -m pip install --upgrade build twine
rm -rf dist/
python -m build
twine check dist/*
twine upload dist/*
```

Verify in a clean environment before moving on:

```bash
python -m venv /tmp/v && /tmp/v/bin/pip install iotype-ai
/tmp/v/bin/python -c "from iotype import Iotype; print('ok')"
```

## 2. Python alias — `iotype`

```bash
cd sdk/aliases/pypi-iotype
rm -rf dist/
python -m build
twine upload dist/*
```

```bash
python -m venv /tmp/a && /tmp/a/bin/pip install iotype
/tmp/a/bin/python -c "from iotype import Iotype; print('ok')"
```

The alias ships no modules — `iotype-ai` is what provides the importable
`iotype` package. If the alias shipped one too, the two would collide.

---

## 3. npm — `@iotype-ai/sdk`

```bash
cd sdk/javascript
npm install
npm run build
npm publish --access public
```

`--access public` is required. Scoped packages default to private, and the
publish will be rejected on a free account without it.

## 4. npm alias — not possible, and not needed

npm refuses to create the package `iotype`:

```
403 Forbidden - PUT https://registry.npmjs.org/iotype
Package name too similar to existing package io-type
```

[`io-type`](https://www.npmjs.com/package/io-type) is an unrelated TypeScript
utility-types package, and npm's typosquatting filter blocks anything close to
an existing name. **Do not work around this** by publishing under a different
name — a name nobody will guess adds nothing.

The filter applies to every account, so no one else can register `iotype`
either. The defensive goal is met without publishing anything.

On npm the package is simply `@iotype-ai/sdk`.

> A name being absent from the registry does not mean it can be created.
> Similarity is only enforced at publish time.

---

## 5. PHP — `iotype-ai/sdk`

Packagist reads directly from the repository; there is no upload step.

**Packagist only reads `composer.json` from the repository root.** There is no
subdirectory option — a manifest at `sdk/php/composer.json` is invisible to it.
So the manifest lives at the root and its autoloader points into `sdk/php/src/`:

```json
"autoload": { "psr-4": { "Iotype\\": "sdk/php/src/" } }
```

`.gitattributes` marks the other SDKs, docs and specs `export-ignore`, so a PHP
consumer downloads only the PHP code — not the Python, JavaScript and Go trees.

1. Sign in at <https://packagist.org> with **Log in with GitHub**, using the
   account that owns the `iotype-ai` organisation.
2. Grant Packagist access to the `iotype-ai` organisation when GitHub asks.
   Without this it cannot see the repository or install the webhook.
3. Submit `https://github.com/iotype-ai/iotype-api`.
4. Confirm the detected name is `iotype-ai/sdk` — it comes from `composer.json`,
   not from the repository name.
5. Check the package page for a warning about auto-updating. If present, trigger
   an account sync so Packagist installs the push webhook.

Versions come from git tags, so `v1.0.0` must be pushed before a stable release
appears.

## 6. Go — `github.com/iotype-ai/iotype-api/sdk/go`

No registry. `pkg.go.dev` indexes the module the first time anyone fetches it:

```bash
GOPROXY=proxy.golang.org go list -m github.com/iotype-ai/iotype-api/sdk/go@latest
```

**The module path is baked into `go.mod` and into every user's imports.** If the
repository ever moves to a different organisation, this path breaks for everyone
who installed it. Go does not follow GitHub's redirects.

---

## 7. Tag the release

```bash
git tag -a v1.0.0 -m "v1.0.0"
git push origin v1.0.0
```

Go resolves versions from tags, so this is what makes `@latest` work.

---

## After publishing

Fill in the real links on each registry page — PyPI, npm and Packagist all
render the project URLs from the manifests, and they are already set to point at
<https://iotype.com/api-service>.

Then set the three things that can only be set in the GitHub web interface:

- **Website:** `https://iotype.com/api-service`
- **Description:** a one-line summary naming the services
- **Topics:** `persian`, `farsi`, `speech-to-text`, `asr`, `ocr`, `persian-ocr`,
  `text-to-speech`, `translation`, `nlp`, `api`, `sdk`

---

## Security

**Never commit a registry token.** Use `~/.pypirc` and `~/.npmrc` locally, or
repository secrets if you later automate this.

Before every publish, confirm no API token slipped into the tree:

```bash
python .github/scripts/check-anchors.py     # anchor policy
grep -rInE '"[0-9]+\|[A-Za-z0-9]{40,}"' --exclude-dir=.git .
```

CI runs both checks on every push, but a local publish bypasses CI entirely.

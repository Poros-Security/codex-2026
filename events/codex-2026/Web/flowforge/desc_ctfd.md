# Challenge Description — CTFd

## Name

Flowforge

## Category

Web Exploitation

## Difficulty

Hard

---

## Description (lore)

> **Flowforge — Product Bulletin #7**
>
> Flowforge is a low-code platform. Drag a few blocks together, wire them
> up, and you have a working AI pipeline — a "flow" — deployed to the
> cloud in seconds. Onboarding is frictionless by design: no account, no
> credit card, no waiting. Anyone can build. Anyone can publish.
>
> Under the hood, every flow is a graph of nodes. Some nodes carry data.
> Some carry prompts. And some carry *code* — a little Python snippet the
> platform runs for you when it assembles your flow.
>
> The team added a filter to keep dangerous code out. `system`, `exec`,
> `subprocess`, `open` — the usual suspects. All blocked. The filter makes
> them feel safe.
>
> But a filter only knows the names you taught it. And the public build
> endpoint — the one that assembles a flow for the marketplace — it does
> not ask who you are. It just builds. And building, it turns out, means
> running.
>
> You have a browser, a clear head, and a suspicion about what "build"
> really means.
>
> Target: http://TARGET:11026
>
> Flag format: `CODEX26{...}`

---

## Hints (maximum 3, progressive)

### Hint 1 — Map the API (cost ~30)

> The platform exposes a few unauthenticated endpoints. `GET /api/v1/auto_login`
> hands you a token. `POST /api/v1/flows/` creates a flow (send the token as a
> Bearer header) and returns its id. `GET /api/v1/flows/<id>` returns the flow
> structure — including an empty `code` field, a template showing exactly where
> code lives.

### Hint 2 — Build is the dangerous verb (cost ~60)

> `POST /api/v1/build_public_tmp/<flow_id>/flow` is the public build endpoint.
> It asks for no token. If you send a `data` body, it uses YOUR flow data
> instead of the stored one. Walk the node tree: the code field is at
> `data -> nodes -> [n] -> data -> template -> code -> value`. Whatever sits
> there is executed when the flow is built.

### Hint 3 — The filter only knows names (cost ~90)

> The filter blocks the strings `os.system`, `subprocess`, `open(`, `__`,
> `eval`, `exec`, `importlib`. It does not block `import os` — and it does not
> block `getattr`. Remember that `os.popen` itself trips `open(` because
> "popen" contains "open". Reach `popen` by name instead:
> `getattr(os, 'popen')('cat /flag.txt').read()`.

---

## Flag (organizer, do NOT expose in CTFd)

```
CODEX26{fl0wf0rg3_un4uth_c0d3_1nj3ct10n}
```

---

## Organizer notes (internal)

- Single Flask service (port 11026, internal 8080). Flag at `/flag.txt` (444),
  injected from `FLAG` env at boot.
- Modeled on CVE-2026-33017 (Langflow unauth RCE): the public build endpoint
  `POST /api/v1/build_public_tmp/<id>/flow` accepts an attacker-controlled
  `data` body whose node `code` field is executed unsandboxed during build.
- Endpoints:
  - `GET /` — landing page with API hints.
  - `GET /api/v1/auto_login` — returns a Bearer token (no auth).
  - `POST /api/v1/flows/` — requires `Authorization: Bearer <token>`, creates a
    flow, returns `{"id": ...}`.
  - `GET /api/v1/flows/<id>` — returns the flow template (shows the code path).
  - `POST /api/v1/build_public_tmp/<id>/flow` — vulnerable. If `data` present,
    extracts `code` from the node tree, applies a substring blacklist, then
    `exec()`s it with stdout captured into the response log.
- Blacklist (substring, case-insensitive): `os.system`, `subprocess`, `open(`,
  `__`, `eval`, `exec`, `importlib`. Note `open(` also matches `popen(` — so the
  intended bypass is `import os` + `print(getattr(os, 'popen')('cat
  /flag.txt').read())`.
- Solver: `solver/solve.py`. Do NOT leak that `getattr` is unblocked — that is
  the core of the challenge. Hint 3 reveals it; gate hints by cost.

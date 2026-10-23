# Challenge Description — CTFd

## Name

Whisper Well

## Category

Web Exploitation

## Difficulty

Medium

---

## Description (lore)

> **Whisper Well — Town Archive, Entry #114**
>
> In the center of the old town there is a well. No one draws water from it
> anymore, but the townsfolk still come to whisper. Whatever you say into the
> dark, the well says it back to you — every word, every time. Some call it a
> blessing. The elders call it a habit nobody remembers the reason for.
>
> The town records are scattered. A ledger from the founding days mentions
> something hidden "beneath the echo" — a vault sealed when the well was dug,
> its key forgotten. The well never forgot.
>
> Lately, travelers have noticed the well is not merely echoing. It is
> *listening*. And deep below the waterline, something still runs — an old
> mechanism, older than the town, that repeats your words through channels it
> was never meant to speak.
>
> You are a visiting engineer. The well takes your whisper and returns it
> verbatim. Prove that what it *listens* to, it can be made to *obey*.
>
> Target: http://TARGET:11021
>
> Flag format: `CODEX26{...}`

---

## Hints (maximum 3, progressive)

### Hint 1 — Learn what the well refuses (cost ~30)

> The well echoes through an old shell mechanism. It is not unguarded — certain
> characters make it go silent. Probe it. It rejects `;` `&` `|` `>` `<`.
> But a filter that only names the obvious is a filter with holes. The shell
> still understands `$(...)` and backticks.

### Hint 2 — Understand the echo (cost ~60)

> The well runs exactly this, with your whisper inserted unquoted:
>
> ```
> echo <your whisper>
> ```
>
> Command substitution `$(...)` is expanded by the shell *before* `echo`
> runs. The filter does not block `$`, `(`, or `)`. Try `$(cat /flag.txt)`.

### Hint 3 — The landing (cost ~90)

> The vault rests at `/flag.txt`. The flag contains no spaces, so
> `$(cat /flag.txt)` prints it intact through `echo`. If anything mangles it,
> strip the newline first: `$(tr -d '\n' < /flag.txt)`.

---

## Flag (organizer, do NOT expose in CTFd)

```
CODEX26{wh1sp3r_w3ll_3ch0_sh3ll_1nj3ct10n}
```

---

## Organizer notes (internal)

- Flag in container: `/flag.txt` (mode 444, world-readable), injected at
  container start from the `FLAG` environment variable (see `docker-compose.yml`).
- The vulnerable endpoint is `/whisper` (GET or POST, parameter `msg`).
- The bug is `subprocess.check_output('echo ' + msg, shell=True)` with a
  blacklist of `; & | > <` only. Command substitution `$(...)` and backticks
  are the intended bypass. A URL-encoded newline (`%0A`) also works.
- Solver: `solver/solve.py`. Reference one-liner:
  `curl -G 'http://TARGET:11021/whisper' --data-urlencode 'msg=$(cat /flag.txt)'`.
- Do NOT leak that `$()` / backticks are unblocked — that is the core of the
  challenge. Hint 2 reveals it, so gate hints by cost accordingly.

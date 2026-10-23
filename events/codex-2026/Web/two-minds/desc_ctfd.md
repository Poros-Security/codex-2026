# Challenge Description — CTFd

## Name

Two Minds

## Category

Web Exploitation

## Difficulty

Hard

---

## Description (lore)

> **Two Minds — Border Control, Incident Dossier**
>
> The border between the outside world and the origin server is guarded
> by two machines. The edge gate inspects every request that arrives and
> decides what may pass. The origin server serves the content. The two
> were built by different teams, years apart, and they were never made to
> agree on one small thing: where a request ends.
>
> The gate measures a request by its declared Content-Length. The server
> measures a request by its Transfer-Encoding chunks. Usually the numbers
> match and nobody notices. But when a request carries both, the two
> machines disagree — and the leftover bytes do not disappear. They
> linger, half-digested, and the next request that comes along walks
> straight into them.
>
> Behind the gate there is a room marked `/admin`. The gate refuses every
> request that asks for it directly. But the gate only reads the very
> beginning of what you send.
>
> You have a raw socket and a clear head. Make the two minds disagree.
>
> Target: `nc TARGET 11025`
>
> Flag format: `CODEX26{...}`

---

## Hints (maximum 3, progressive)

### Hint 1 — The two guards disagree (cost ~30)

> The edge gate and the origin server measure request length differently.
> The gate trusts `Content-Length`. The server trusts
> `Transfer-Encoding: chunked` when it is present. Send a request that
> carries BOTH. Study how each side frames the body.

### Hint 2 — Where does the leftover go? (cost ~60)

> The gate reads `Content-Length` bytes and forwards everything. The
> server reads only the first chunked body and treats what follows as the
> START of the next request. Craft the trailing bytes as a full `GET
> /admin` request. The gate only blocks `/admin` when it is the first
> line of the request you send — inside the body it is invisible to the
> gate.

### Hint 3 — Use a raw socket (cost ~90)

> This is not a job for a browser or curl. Open a raw TCP socket, send the
> smuggled POST, read the first response, then send a harmless second
> request on the same connection. The smuggled `GET /admin` is answered
> first, and its body is the flag. Keep the connection open — keep-alive
> is what carries the poison.

---

## Flag (organizer, do NOT expose in CTFd)

```
CODEX26{tw0_m1nds_0n3_r3qu3st_5muggl3d}
```

---

## Organizer notes (internal)

- Two Python processes in ONE container (`docker-compose.yml`, port 11025):
  - `frontend.py` — public edge gate (0.0.0.0:8000). Frames every request by
    `Content-Length` ONLY, blocks `/admin` (403), forwards all else verbatim
    to the backend over one persistent connection per client.
  - `backend.py` — origin (127.0.0.1:9000, not published). Frames by
    `Transfer-Encoding: chunked` when present, else `Content-Length`. No ACL.
    Serves `/` (index) and `/admin` (flag).
- The vuln is CL.TE: frontend uses CL, backend uses TE. A request with both
  headers smuggles a `GET /admin` into the backend's next-read.
- Flag in container: `/flag.txt` (mode 444), injected from `FLAG` env.
- Solver: `solver/solve.py` (raw socket). Do NOT leak that the frontend is a
  custom CL-only parser or that the backend prefers TE — that is the core.

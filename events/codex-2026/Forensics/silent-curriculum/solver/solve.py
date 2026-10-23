#!/usr/bin/env python3
"""Reference solver / answer key for Silent Curriculum.

PoC lengkap (Wireshark filters, Follow TCP Stream, timeline) ada di README.md.
Script ini hanya mencetak jawaban resmi + flag untuk verifikasi cepat author.
"""

ANSWERS = [
    ("Q1 source IP", "203.0.113.77"),
    ("Q2 plugin", "learnpress"),
    ("Q3 REST endpoint", "/wp-json/lp/v1/courses/archive-course"),
    ("Q4 inject param", "term_id"),
    ("Q5 SQLi technique", "time-based blind"),
    ("Q6 DB table", "wp_users"),
    ("Q7 admin login", "courseadmin"),
    ("Q8 backdoor file", "cache-helper.php"),
    ("Q9 rogue admin email", "nightshift.audit@proton.me"),
    ("Q10 create-user timestamp", "25/Sep/2024:00:50:43 +0000"),
]

FLAG = "CODEX26{s1l3nt_c0urs3_adm1n_t4k30v3r}"

# Evidence hints (pcap) — mirror README PoC
EVIDENCE = {
    "Q1": 'http.request with User-Agent sqlmap / URI contains SLEEP → ip.src',
    "Q2": "GET /wp-content/plugins/learnpress/readme.txt (before SQLi burst)",
    "Q3/Q4": "GET /wp-json/lp/v1/courses/archive-course?term_id=...",
    "Q5": "Follow TCP Stream → SLEEP / EXTRACTVALUE / MID+IF",
    "Q6": "payload targets wordpress.wp_users (or hex 0x77705f7573657273)",
    "Q7": "POST /wp-login.php?login=courseadmin → 302 then /wp-admin/",
    "Q8": "GET .../cache-helper/cache-helper.php?cmd=whoami",
    "Q9": "POST /wp-json/wp/v2/users?...email=nightshift.audit%40proton.me...",
    "Q10": "frame time / X-Access-Time on that users POST → Apache stamp",
}


if __name__ == "__main__":
    for i, (label, ans) in enumerate(ANSWERS, 1):
        print(f"{i}. [{label}] {ans}")
    print()
    print("FLAG:", FLAG)
    print()
    print("Evidence map:")
    for k, v in EVIDENCE.items():
        print(f"  {k}: {v}")

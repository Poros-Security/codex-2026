#!/bin/sh
# Fast instance flag: BASE_FLAG + _<8 hex> before '}'.
# Uses sha256sum only so the service can bind its port without starting Python.
# Same digest as hashlib.sha256(seed.encode()).hexdigest()[:8]

apply_dynamic_flag() {
    flag_file="${1:-/flag}"

    # GZCTF memberi flag per-tim yang sudah final lewat GZCTF_FLAG. Pakai apa
    # adanya: menurunkan suffix lagi membuat flag di container berbeda dari
    # yang dicatat GZCTF, sehingga challenge tidak bisa disolve.
    if [ -n "${GZCTF_FLAG:-}" ]; then
        printf '%s\n' "$GZCTF_FLAG" > "$flag_file"
        FLAG="$GZCTF_FLAG"; export FLAG
        CTF_FLAG="$GZCTF_FLAG"; export CTF_FLAG
        return 0
    fi

    seed="${FLAG:-${CTF_FLAG:-}}"
    base="${BASE_FLAG:-}"

    if [ -z "$base" ]; then
        if [ -n "$seed" ]; then
            printf '%s\n' "$seed" > "$flag_file"
            FLAG="$seed"
            export FLAG
        fi
        return 0
    fi

    if [ -z "$seed" ]; then
        seed="$(dd if=/dev/urandom bs=16 count=1 2>/dev/null | sha256sum | awk '{print $1}')"
    fi

    newflag=""
    case "$base" in
        *'}')
            core="${base%\}}"
            rest="${seed#"${core}"_}"
            if [ "$rest" != "$seed" ]; then
                case "$rest" in
                    [0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]})
                        newflag="$seed"
                        ;;
                esac
            fi
            if [ -z "$newflag" ]; then
                suffix="$(printf '%s' "$seed" | sha256sum | awk '{print substr($1,1,8)}')"
                newflag="${core}_${suffix}}"
            fi
            ;;
        *)
            suffix="$(printf '%s' "$seed" | sha256sum | awk '{print substr($1,1,8)}')"
            newflag="${base}_${suffix}"
            ;;
    esac

    printf '%s\n' "$newflag" > "$flag_file"
    FLAG="$newflag"
    export FLAG
    CTF_FLAG="$newflag"
    export CTF_FLAG
}

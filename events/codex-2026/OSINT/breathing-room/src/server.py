#!/usr/bin/env python3
import os
import socket

HOST = os.getenv("CTF_HOST", "0.0.0.0")
PORT = int(os.getenv("CTF_PORT", "11033"))

FLAG = os.getenv("FLAG", os.getenv("CTF_FLAG", "CODEX26{SEOUL_PM25_GRADE5_2019-02-15}"))

QUESTIONS = [
    (
        "Q1. Which city is relevant to the measure?\n> ",
        ["seoul", "Seoul"],
    ),
    (
        "Q2. What environmental issue is discussed in the clipping?\n> ",
        ["pm2.5", "pm25", "fine dust"],
    ),
    (
        "Q3. Which vehicle emission grade was affected?\n> ",
        ["5"],
    ),
    (
        "Q4. On what date did the measure take effect?\n"
        "Format: YYYY-MM-DD\n> ",
        ["2019-02-15"],
    ),
]


def send(conn, text):
    conn.sendall(text.encode())


def handle_client(conn, addr):
    print(f"[+] Connection from {addr}")

    try:
        send(
            conn,
            """
========================================
          BREATHING ROOM
========================================

A fragment from an old Korean newspaper
has been recovered.

""",
        )

        for question, valid_answers in QUESTIONS:
            send(conn, question)

            data = conn.recv(1024)

            if not data:
                return

            answer = data.decode(errors="ignore").strip().lower()

            if answer not in valid_answers:
                send(conn, "\nIncorrect.\nConnection closed.\n")
                return

            send(conn, "\nCorrect.\n\n")

        send(
            conn,
            f"""All answers are correct.

{FLAG}

""",
        )

    except Exception as e:
        print(f"[!] Error with {addr}: {e}")

    finally:
        conn.close()
        print(f"[-] Connection closed: {addr}")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(64)

        print(f"[*] Breathing Room listening on {HOST}:{PORT}")

        while True:
            conn, addr = server.accept()
            handle_client(conn, addr)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import os
import socket

HOST = os.getenv("CTF_HOST", "0.0.0.0")
PORT = int(os.getenv("CTF_PORT", "11034"))

FLAG = os.getenv("FLAG", os.getenv("CTF_FLAG", "CODEX26{ISHOWSPEED}"))

QUESTIONS = [
    (
        "Q1. Where was the first location?\n> ",
        ["kota tua", "kota tua jakarta"],
    ),
    (
        "Q2. Where was the second location?\n> ",
        ["antara heritage center", "antara heritage"],
    ),
    (
        "Q3. Where was the third location?\n> ",
        ["malioboro", "malioboro yogyakarta"],
    ),
    (
        "Q4. Where was the fourth location?\n> ",
        ["ubud art market"],
    ),
    (
        "Q5. Where was the fifth location?\n> ",
        ["uluwatu temple", "uluwatu temple kecak", "pura luhur uluwatu"],
    ),
]


def normalize(text):
    return " ".join(text.strip().lower().split())


def send(conn, text):
    conn.sendall(text.encode())


def handle_client(conn, addr):
    print(f"[+] Connection from {addr}")

    try:
        send(
            conn,
            """
========================================
          WHERE DID HE GO?
========================================

You found the journey.

Now identify the five locations
from the NMPZ challenge.

Enter each location in order.

""",
        )

        for question, valid_answers in QUESTIONS:
            send(conn, question)

            data = conn.recv(1024)

            if not data:
                return

            answer = normalize(data.decode(errors="ignore"))

            valid = [normalize(x) for x in valid_answers]

            if answer not in valid:
                send(
                    conn,
                    "\nIncorrect.\n"
                    "The answer does not match.\n"
                    "Connection closed.\n",
                )
                return

            send(conn, "\nCorrect.\n\n")

        send(
            conn,
            f"""
All five locations are correct.

Now you know where he went.

{FLAG}

"""
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

        print(f"[*] Where Did He Go? listening on {HOST}:{PORT}")

        while True:
            conn, addr = server.accept()
            handle_client(conn, addr)


if __name__ == "__main__":
    main()
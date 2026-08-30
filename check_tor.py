import socket
from pathlib import Path

HOST = "127.0.0.1"
PORT = 9051
COOKIE_PATH = Path("/usr/local/var/lib/tor/control_auth_cookie")


def read_reply(sock):
    lines = []

    while True:
        data = sock.recv(4096)

        if not data:
            raise ConnectionError("Tor закрыл соединение")

        lines.extend(
            data.decode("utf-8", errors="replace").splitlines()
        )

        for line in lines:
            if len(line) >= 4 and line[3] == " ":
                if line[:3].startswith(("4", "5")):
                    raise RuntimeError(
                        "Ошибка Tor:\n" + "\n".join(lines)
                    )

                return "\n".join(lines)


def send(sock, command):
    sock.sendall((command + "\r\n").encode("ascii"))
    return read_reply(sock)


cookie = COOKIE_PATH.read_bytes()

with socket.create_connection((HOST, PORT), timeout=5) as sock:
    print("== PROTOCOLINFO ==")
    print(send(sock, "PROTOCOLINFO 1"))

    print("== AUTHENTICATE ==")
    print(send(sock, "AUTHENTICATE " + cookie.hex()))

    print("== BOOTSTRAP ==")
    print(send(sock, "GETINFO status/bootstrap-phase"))

    print("== CIRCUIT ==")
    print(send(sock, "GETINFO status/circuit-established"))

    print("== SOCKS LISTENER ==")
    print(send(sock, "GETINFO net/listeners/socks"))

    print("== VERSION ==")
    print(send(sock, "GETINFO version"))

    print("== QUIT ==")
    print(send(sock, "QUIT"))

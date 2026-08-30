import json
import socket
import urllib.request
import socks
from pathlib import Path


CONTROL_HOST = "127.0.0.1"
CONTROL_PORT = 9051
SOCKS_HOST = "127.0.0.1"
SOCKS_PORT = 9050
COOKIE_PATH = Path("/usr/local/var/lib/tor/control_auth_cookie")
CHECK_URL = "https://check.torproject.org/api/ip"


def read_reply(sock):
    lines = []

    while True:
        data = sock.recv(4096)

        if not data:
            raise ConnectionError("Tor закрыл ControlPort-соединение")

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


def tor_command(sock, command):
    sock.sendall((command + "\r\n").encode("ascii"))
    return read_reply(sock)


def get_tor_status():
    cookie = COOKIE_PATH.read_bytes()

    with socket.create_connection(
        (CONTROL_HOST, CONTROL_PORT),
        timeout=5,
    ) as sock:
        tor_command(sock, "PROTOCOLINFO 1")
        tor_command(sock, "AUTHENTICATE " + cookie.hex())

        bootstrap = tor_command(
            sock,
            "GETINFO status/bootstrap-phase",
        )

        circuit = tor_command(
            sock,
            "GETINFO status/circuit-established",
        )

        version = tor_command(
            sock,
            "GETINFO version",
        )

        tor_command(sock, "QUIT")

    return {
        "bootstrap": bootstrap,
        "circuit": circuit,
        "version": version,
    }


def check_tor_socks():
    original_socket = socket.socket

    socks.set_default_proxy(
        socks.SOCKS5,
        SOCKS_HOST,
        SOCKS_PORT,
        rdns=True,
    )

    socket.socket = socks.socksocket

    try:
        request = urllib.request.Request(
            CHECK_URL,
            headers={"User-Agent": "tornet/0.1"},
        )

        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:
            return json.loads(
                response.read().decode("utf-8")
            )

    finally:
        socket.socket = original_socket
        socks.set_default_proxy(None)



def main():
    print("=== Tor ControlPort ===")

    status = get_tor_status()

    print(status["bootstrap"])
    print(status["circuit"])
    print(status["version"])

    print("\n=== Tor SOCKS5 ===")

    socks_status = check_tor_socks()

    print("IsTor:", socks_status.get("IsTor"))
    print("Exit IP:", socks_status.get("IP"))

    if socks_status.get("IsTor") is True:
        print("\nSTATUS: OK")
    else:
        print("\nSTATUS: ERROR")


if __name__ == "__main__":
    main()

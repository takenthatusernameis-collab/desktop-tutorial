#!/usr/bin/env python3
"""Fixed-destination TCP gateway for the isolated Kilo worker.

The worker network resolves api.kilo.ai to this container. The gateway
forwards raw TLS bytes only to api.kilo.ai:443 and nowhere else.
"""

from __future__ import annotations

import select
import socket
import threading

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 443
DESTINATION = ("api.kilo.ai", 443)


def pipe(left: socket.socket, right: socket.socket) -> None:
    sockets = [left, right]
    try:
        while True:
            readable, _, exceptional = select.select(sockets, [], sockets, 60)
            if exceptional:
                return
            if not readable:
                continue
            for source in readable:
                target = right if source is left else left
                data = source.recv(65536)
                if not data:
                    return
                target.sendall(data)
    except (OSError, ValueError):
        return
    finally:
        for sock in sockets:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def handle(client: socket.socket) -> None:
    upstream: socket.socket | None = None
    try:
        upstream = socket.create_connection(DESTINATION, timeout=20)
        pipe(client, upstream)
    finally:
        for sock in (client, upstream):
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass


def main() -> None:
    with socket.create_server((LISTEN_HOST, LISTEN_PORT), reuse_port=False) as server:
        print("fixed Kilo gateway ready", flush=True)
        while True:
            client, _ = server.accept()
            threading.Thread(target=handle, args=(client,), daemon=True).start()


if __name__ == "__main__":
    main()

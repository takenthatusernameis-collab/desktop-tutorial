#!/usr/bin/env python3
"""Fixed-destination raw-TLS gateway for the isolated Kilo worker.

The worker resolves api.kilo.ai to this container. The gateway forwards raw
TLS bytes only to an IPv4 address for api.kilo.ai:443 and nowhere else.
"""

from __future__ import annotations

import socket
import sys
import threading

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 443
DESTINATION_HOST = "api.kilo.ai"
DESTINATION_PORT = 443
CONNECT_TIMEOUT = 20


def resolve_ipv4() -> list[tuple]:
    infos = socket.getaddrinfo(
        DESTINATION_HOST,
        DESTINATION_PORT,
        socket.AF_INET,
        socket.SOCK_STREAM,
    )
    if not infos:
        raise OSError(f"no IPv4 address resolved for {DESTINATION_HOST}")
    return [item[4] for item in infos]


def connect_upstream() -> tuple[socket.socket, tuple]:
    last_error: OSError | None = None
    for sockaddr in resolve_ipv4():
        upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream.settimeout(CONNECT_TIMEOUT)
        upstream.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            upstream.connect(sockaddr)
            upstream.settimeout(None)
            return upstream, sockaddr
        except OSError as exc:
            last_error = exc
            upstream.close()
    assert last_error is not None
    raise last_error


def forward(source: socket.socket, target: socket.socket, label: str) -> None:
    try:
        while True:
            data = source.recv(65536)
            if not data:
                try:
                    target.shutdown(socket.SHUT_WR)
                except OSError:
                    pass
                return
            target.sendall(data)
    except (OSError, ValueError) as exc:
        print(f"gateway {label} stopped: {exc}", file=sys.stderr, flush=True)


def pipe(client: socket.socket, upstream: socket.socket) -> None:
    threads = [
        threading.Thread(
            target=forward,
            args=(client, upstream, "client->upstream"),
            daemon=True,
        ),
        threading.Thread(
            target=forward,
            args=(upstream, client, "upstream->client"),
            daemon=True,
        ),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def handle(client: socket.socket, peer: tuple) -> None:
    upstream: socket.socket | None = None
    try:
        upstream, destination = connect_upstream()
        print(
            f"gateway connection {peer} -> {destination}",
            flush=True,
        )
        pipe(client, upstream)
    except OSError as exc:
        print(f"gateway upstream failure for {peer}: {exc}", file=sys.stderr, flush=True)
    finally:
        for sock in (client, upstream):
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass


def main() -> None:
    print(
        f"fixed Kilo gateway listening on {LISTEN_HOST}:{LISTEN_PORT}, "
        f"destination={DESTINATION_HOST}:{DESTINATION_PORT}, ipv4-only",
        flush=True,
    )
    with socket.create_server(
        (LISTEN_HOST, LISTEN_PORT),
        family=socket.AF_INET,
        reuse_port=False,
    ) as server:
        while True:
            client, peer = server.accept()
            client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            threading.Thread(
                target=handle,
                args=(client, peer),
                daemon=True,
            ).start()


if __name__ == "__main__":
    main()

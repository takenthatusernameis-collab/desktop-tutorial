FROM node:22-bookworm

RUN apt-get update -qq \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
       git curl python3 ca-certificates rsync \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @kilocode/cli

RUN kilo --version

WORKDIR /workspace

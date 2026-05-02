FROM node:22-bookworm-slim

ARG CLAUDE_CODE_VERSION=2.1.126
ARG CODEX_VERSION=0.128.0

ENV HOME=/blind-home
ENV NO_COLOR=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    git \
    ripgrep \
  && rm -rf /var/lib/apt/lists/*

RUN npm install -g \
    @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} \
    @openai/codex@${CODEX_VERSION}

RUN mkdir -p /blind-home /input /out /runner /work

WORKDIR /work

ENTRYPOINT ["/bin/bash", "/runner/entrypoint.sh"]

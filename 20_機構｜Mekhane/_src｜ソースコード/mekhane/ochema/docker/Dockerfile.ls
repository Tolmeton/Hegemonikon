# LS コンテナ — ホスト 4 インスタンス制限を回避するための Docker 化
# 使用方法: docker-compose -f docker-compose.ls.yml up -d
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# LS バイナリをコンテナ内にコピー (ビルド時にホストからコピー)
COPY language_server_linux_x64 /usr/local/bin/language_server_linux_x64
RUN chmod +x /usr/local/bin/language_server_linux_x64

# mekhane ソースコード (vault アクセスに必要)
WORKDIR /app
COPY . /app/

# 環境変数
ENV LS_BINARY=/usr/local/bin/language_server_linux_x64
ENV PYTHONPATH=/app
ENV LS_DAEMON_INFO_PATH=/shared/ls_daemon.json

# ポートを公開 (動的に割り当てられるため範囲指定)
EXPOSE 30000-50000

ENTRYPOINT ["python3", "-m", "mekhane.ochema.ls_daemon"]
CMD ["--instances", "3", "--source", "docker", "--workspace", "nonstd_docker"]

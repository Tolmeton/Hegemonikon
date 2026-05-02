# PROOF: [L2/インフラ] <- mekhane/ochema/ A0→外部LLM接続→Non-Standalone LS 起動・管理
# PURPOSE: Non-Standalone LS プロセスの起動・管理
# REASON: --standalone=true では trajectory が保存されないため、
#          stdin metadata 注入 + persistent_mode で IDE 非依存の LS を起動する (DX-010 §F)
from __future__ import annotations
from typing import Optional
"""Non-Standalone LS Manager.

IDE なしで Language Server を起動し、trajectory を生成可能にする。
DX-010 v15.0 Phase 4 の成果を本番化。

Usage:
    mgr = NonStandaloneLSManager(workspace_id="my_task")
    ls = mgr.start()
    client = AntigravityClient(ls_info=ls)
    resp = client.ask("Hello")
    mgr.stop()
"""


import logging
import os
import platform
import re
import signal
import subprocess
import shutil
import time
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

# psutil は遅延 import (フォールバック時のみ)
# Linux ファストパス (pgrep/ss) が成功すれば一切ロードしない

logger = logging.getLogger(__name__)

# --- Constants ---

_IS_WINDOWS = platform.system() == "Windows"
_LS_BINARY_PATTERN = "language_server_windows" if _IS_WINDOWS else "language_server_linux"


def _get_ls_binary() -> str:
    """OS に応じた LS バイナリのパスを返す。存在しない場合は空文字列。"""
    # 0. 環境変数 LS_BINARY が設定されていればそれを使う (コンテナ対応)
    env_binary = os.environ.get("LS_BINARY", "")
    if env_binary and os.path.isfile(env_binary):
        logger.info("LS binary from env LS_BINARY: %s", env_binary)
        return env_binary

    if _IS_WINDOWS:
        appdata = os.environ.get("LOCALAPPDATA", "")
        default = os.path.join(
            appdata, "Programs", "Antigravity",
            "resources", "app", "extensions", "antigravity",
            "bin", "language_server_windows_x64.exe",
        )
        binary_name = "language_server_windows_x64.exe"
    else:
        default = (
            "/usr/share/antigravity/resources/app/extensions/antigravity"
            "/bin/language_server_linux_x64"
        )
        binary_name = "language_server_linux_x64"

    # 1. デフォルトパスに存在するか
    if os.path.isfile(default):
        return default

    # 2. PATH から探す
    found = shutil.which(binary_name)
    if found:
        logger.info("LS binary found via PATH: %s", found)
        return found

    # 3. 見つからない — NonStandalone LS 起動をスキップさせる
    logger.debug("LS binary not found: %s (default: %s)", binary_name, default)
    return ""


LS_BINARY = _get_ls_binary()
CLOUD_CODE_ENDPOINT = "https://cloudcode-pa.googleapis.com"


def _detect_random_port_flag() -> str:
    """LS バイナリの HTTP ポート自動割り当てフラグを検出。

    - 古い 1.20 系: ``--random_port``
    - 中間 1.21+ : ``--http_server_port=0``（--help に http_server_port が出る）
    - 現行（http_server_port 廃止）: ``-random_port=true``（Go フラグ、--help に -random_port のみ）
    """
    if not LS_BINARY:
        return "-random_port=true"
    try:
        result = subprocess.run(
            [LS_BINARY, "--help"], capture_output=True, text=True, timeout=5,
        )
        help_text = (result.stdout or "") + (result.stderr or "")
        if "http_server_port" in help_text:
            return "--http_server_port=0"
        if "--random_port" in help_text:
            return "--random_port"
        if "-random_port" in help_text:
            return "-random_port=true"
    except subprocess.SubprocessError as _e:
        logger.debug("Ignored exception: %s", _e)
    return "-random_port=true"


_LS_PORT_FLAG = _detect_random_port_flag()
STARTUP_TIMEOUT = 10  # seconds to wait for LS to start
HEALTH_CHECK_TIMEOUT = 3  # seconds for GetUserStatus


# --- LS Process Detection Utilities (共通) ---


@dataclass
class LSProcessCandidate:
    """LS プロセス検出結果。"""
    pid: int
    cmdline: list[str]
    cmdline_str: str
    has_server_port: bool = False


def _find_ls_processes_linux(
    workspace_filter: str = "",
    *,
    exclude_standalone: bool = True,
) -> list[LSProcessCandidate]:
    """Linux ファストパス: /proc + pgrep で LS プロセスを検出する。

    psutil.process_iter() は全プロセスを列挙するため数十秒かかる環境がある。
    /proc/{pid}/cmdline を直接読むことで数十ミリ秒に短縮する。
    """
    candidates: list[LSProcessCandidate] = []
    try:
        # pgrep で language_server プロセスの PID を高速取得
        result = subprocess.run(
            ["pgrep", "-f", _LS_BINARY_PATTERN],
            capture_output=True, text=True, timeout=3,
        )
        pids = [int(p) for p in result.stdout.strip().split() if p.isdigit()]
        for pid in pids:
            try:
                # /proc/{pid}/cmdline は \x00 区切り
                cmdline_path = Path(f"/proc/{pid}/cmdline")
                raw = cmdline_path.read_bytes()
                if not raw:
                    continue
                cmdline = raw.decode("utf-8", errors="replace").rstrip("\x00").split("\x00")
                cmdline_str = " ".join(cmdline)
                if _LS_BINARY_PATTERN not in cmdline_str:
                    continue
                if exclude_standalone and "--standalone" in cmdline_str:
                    continue
                if workspace_filter and workspace_filter not in cmdline_str:
                    continue
                candidates.append(LSProcessCandidate(
                    pid=pid,
                    cmdline=cmdline,
                    cmdline_str=cmdline_str,
                    has_server_port="--server_port" in cmdline_str,
                ))
            except (FileNotFoundError, PermissionError):
                continue
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # pgrep が存在しない / タイムアウト → psutil フォールバック
        return []
    # IDE 接続済み LS (server_port あり) を優先
    candidates.sort(key=lambda x: x.has_server_port, reverse=True)
    return candidates


def _get_process_ports_linux(pid: int) -> list[int]:
    """Linux ファストパス: ss コマンドでリスニングポートを取得する。

    psutil.Process(pid).net_connections() の代替。
    ss -tlnp は一般ユーザーでも自プロセスの情報を取得できる。
    """
    ports: set[int] = set()
    try:
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True, text=True, timeout=3,
        )
        for line in result.stdout.splitlines():
            if f"pid={pid}," not in line and f"pid={pid})" not in line:
                continue
            # LISTEN 0 4096 127.0.0.1:42383 0.0.0.0:* ...
            parts = line.split()
            for part in parts:
                if ":" in part and not part.startswith("users"):
                    # 127.0.0.1:42383 or *:42383
                    addr_port = part.rsplit(":", 1)
                    if len(addr_port) == 2 and addr_port[1].isdigit():
                        port = int(addr_port[1])
                        if port > 0:
                            ports.add(port)
                            break  # 1行につき1ポート
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    return sorted(ports)


def find_ls_processes(
    workspace_filter: str = "",
    *,
    exclude_standalone: bool = True,
) -> list[LSProcessCandidate]:
    """Language Server プロセスを検出する (OS 非依存)。

    detect_ide_ls() と antigravity_client._detect_ls() の共通基盤。
    Linux では /proc + pgrep を使うファストパスを優先し、
    失敗時のみ psutil にフォールバックする。

    Args:
        workspace_filter: ワークスペース名の部分一致フィルタ。
        exclude_standalone: --standalone フラグを持つプロセスを除外する。

    Returns:
        LSProcessCandidate のリスト (server_port を持つものが先頭)
    """
    # Linux ファストパス (pgrep + /proc)
    if not _IS_WINDOWS:
        candidates = _find_ls_processes_linux(
            workspace_filter, exclude_standalone=exclude_standalone,
        )
        if candidates:
            return candidates
        # ファストパスで見つからなかった場合は psutil フォールバック
        logger.debug("Linux fast path found no LS processes, falling back to psutil")

    candidates: list[LSProcessCandidate] = []

    # Windows 向け wmic フォールバック (psutil 権限エラー対策)
    if _IS_WINDOWS:
        try:
            out = subprocess.check_output(
                'wmic process where "name like \'%language_server%\'" '
                'get commandline,processid /format:list',
                shell=True, text=True, stderr=subprocess.DEVNULL
            )
            lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
            current_cmd = ""
            for line in lines:
                if line.startswith("CommandLine="):
                    current_cmd = line.split("=", 1)[1]
                elif line.startswith("ProcessId=") and current_cmd:
                    pid_str = line.split("=", 1)[1]
                    if pid_str.isdigit():
                        cmd_str = current_cmd
                        if _LS_BINARY_PATTERN in cmd_str:
                            if not (exclude_standalone and "--standalone" in cmd_str):
                                candidates.append(LSProcessCandidate(
                                    pid=int(pid_str),
                                    cmdline=cmd_str.split(),
                                    cmdline_str=cmd_str,
                                    has_server_port="--server_port" in cmd_str,
                                ))
                    current_cmd = ""
        except subprocess.SubprocessError as _e:
            logger.debug("Ignored exception: %s", _e)

    # psutil による検出 (Windows フォールバック / Linux ファストパス失敗時)
    if not candidates:
        import psutil
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline') or []
                if not cmdline:
                    continue
                cmdline_str = " ".join(cmdline)
                if _LS_BINARY_PATTERN not in cmdline_str:
                    continue
                if exclude_standalone and "--standalone" in cmdline_str:
                    continue
                if workspace_filter and workspace_filter not in cmdline_str:
                    continue
                candidates.append(LSProcessCandidate(
                    pid=proc.info['pid'],
                    cmdline=cmdline,
                    cmdline_str=cmdline_str,
                    has_server_port="--server_port" in cmdline_str,
                ))
            except psutil.Error as _e:  # psutil.NoSuchProcess, AccessDenied, ZombieProcess
                logger.debug("Ignored exception: %s", _e)
                continue

    # IDE 接続済み LS (server_port あり) を優先
    candidates.sort(key=lambda x: x.has_server_port, reverse=True)
    return candidates


def get_process_ports(pid: int) -> list[int]:
    """指定 PID のリスニング TCP ポートを取得する。

    Linux では ss コマンドで高速取得し、
    失敗時は psutil にフォールバックする。

    Args:
        pid: 対象プロセスの PID

    Returns:
        リスニングポートのソート済みリスト
    """
    # Linux ファストパス (ss)
    if not _IS_WINDOWS:
        ports = _get_process_ports_linux(pid)
        if ports:
            return ports
        # ファストパス失敗 → psutil フォールバック
        logger.debug("ss fast path failed for PID %d, falling back to psutil", pid)

    # psutil フォールバック
    import psutil
    ports_set: set[int] = set()
    try:
        proc = psutil.Process(pid)
        for conn in proc.net_connections(kind='tcp'):
            if conn.status == 'LISTEN':
                if conn.laddr.ip in ('127.0.0.1', '0.0.0.0', '::1', '::'):
                    ports_set.add(conn.laddr.port)
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.warning("Cannot get ports for PID %d: %s", pid, e)
    return sorted(ports_set)


# --- IDE LS Detection ---

@dataclass
class IDELSInfo:
    """IDE の Language Server から抽出した接続情報。"""
    pid: int = 0
    ext_server_port: int = 0
    ext_server_csrf: str = ""


def detect_ide_ls(workspace_filter: str = "oikos") -> IDELSInfo:
    """IDE の Language Server プロセスから extension_server_port/csrf を自動取得する。

    find_ls_processes() でプロセスを検出し、cmdline から
    --extension_server_port と --extension_server_csrf_token を抽出する。
    クロスプラットフォーム対応 (Linux / Windows)。

    Args:
        workspace_filter: ワークスペース名の部分一致フィルタ。
            空文字の場合は全 LS を対象にする。

    Returns:
        IDELSInfo with ext_server_port and ext_server_csrf

    Raises:
        RuntimeError: IDE LS が見つからない場合
    """
    info = IDELSInfo()

    candidates = find_ls_processes(workspace_filter)
    if not candidates:
        raise RuntimeError("IDE Language Server not found")

    best = candidates[0]
    info.pid = best.pid
    args = best.cmdline

    # cmdline args からフラグを抽出
    for i, arg in enumerate(args):
        if arg.startswith("--extension_server_port"):
            if "=" in arg:
                info.ext_server_port = int(arg.split("=", 1)[1])
            elif i + 1 < len(args):
                info.ext_server_port = int(args[i + 1])
        elif arg.startswith("--extension_server_csrf_token"):
            if "=" in arg:
                info.ext_server_csrf = arg.split("=", 1)[1]
            elif i + 1 < len(args):
                info.ext_server_csrf = args[i + 1]

    if not info.ext_server_port:
        raise RuntimeError(
            f"extension_server_port not found in IDE LS cmdline (PID {info.pid})"
        )
    # Note: extension_server_csrf_token は現行 LS バイナリでは廃止済み。
    # IDE もこのフラグを使わない。ext_server_csrf が空でも正常動作する。

    return info


# --- Protobuf Helpers ---

def _encode_varint(value: int) -> bytes:
    """protobuf varint encoding."""
    result = b""
    while value > 0x7F:
        result += bytes([(value & 0x7F) | 0x80])
        value >>= 7
    result += bytes([value & 0x7F])
    return result


def _encode_string(field_number: int, value: str) -> bytes:
    """protobuf string field encoding (wire type 2)."""
    tag = (field_number << 3) | 2
    encoded = value.encode("utf-8")
    return _encode_varint(tag) + _encode_varint(len(encoded)) + encoded


from mekhane.ochema.proto import IDE_METADATA

def _detect_ide_version() -> str:
    """IDE の package.json から実バージョンを取得する。失敗時は proto.py の値をフォールバック。"""
    import json
    from pathlib import Path
    pkg = Path(LS_BINARY).parent.parent.parent.parent / "package.json"
    try:
        return json.loads(pkg.read_text()).get("version", IDE_METADATA["ideVersion"])
    except (OSError, json.JSONDecodeError) as _e:
        logger.debug("Ignored exception: %s", _e)
        return IDE_METADATA["ideVersion"]


def build_metadata(
    ide_name: str = IDE_METADATA.get("ideName", "antigravity"),
    ide_version: str = "",
    extension_name: str = IDE_METADATA.get("extensionName", "antigravity"),
    locale: str = "en",
) -> bytes:
    """LS 起動時に stdin に送る最小限の MetadataSchema protobuf を生成する。

    フィールド番号は Extension JS の MetadataProvider.getMetadata() から推測:
      field 1: ide_name
      field 2: ide_version
      field 3: extension_name
      field 6: locale

    Args:
        ide_name: IDE 名
        ide_version: IDE バージョン
        extension_name: 拡張名
        locale: ロケール

    Returns:
        protobuf binary
    """
    if not ide_version:
        ide_version = _detect_ide_version()

    data = b""
    data += _encode_string(1, ide_name)
    data += _encode_string(2, ide_version)
    data += _encode_string(3, extension_name)
    data += _encode_string(6, locale)
    return data


def parse_http_port(log_text: str) -> int:
    """LS のログから HTTP ポートを抽出する。

    Expected format:
        "Language server listening on random port at 35359 for HTTP"

    Args:
        log_text: LS の stdout/stderr ログテキスト

    Returns:
        HTTP port number

    Raises:
        RuntimeError: ポートが見つからない場合
    """
    match = re.search(r"at (\d+) for HTTP$", log_text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"HTTP port not found in LS log: {log_text[:200]}")
    return int(match.group(1))


# --- Manager ---

class NonStandaloneLSManager:
    """Non-Standalone Language Server のプロセスマネージャー。

    --standalone=true を使わずに LS を起動し、trajectory 生成を可能にする。
    IDE の Extension Server port/csrf を借用して動作する。

    Usage:
        mgr = NonStandaloneLSManager(workspace_id="research_task")
        ls_info = mgr.start()
        # ls_info を AntigravityClient(ls_info=ls_info) に渡して使用
        mgr.stop()
    """

    MAX_INSTANCES = int(os.environ.get("HGK_LS_MAX_INSTANCES", "4"))  # 同時に起動できるマネージャー数
    _active_instances: int = 0

    def __init__(
        self,
        workspace_id: Optional[str] = None,
        csrf_token: Optional[str] = None,
        ext_server_port: Optional[int] = None,
        ext_server_csrf: Optional[str] = None,
        force_dummy: bool = False,
        account: str = "default",
    ):
        """初期化。

        Args:
            workspace_id: LS の workspace ID (省略時は自動生成)
            csrf_token: LS の CSRF トークン (省略時は自動生成)
            ext_server_port: IDE Extension Server ポート (省略時は自動検出)
            ext_server_csrf: IDE Extension Server CSRF (省略時は自動検出)
            force_dummy: True の場合、IDE LS が存在しても DummyExtServer を使う
            account: TokenVault アカウント名 (6垢プール用)
        """
        self.workspace_id = workspace_id or f"nonstd_{uuid.uuid4().hex[:8]}"
        self.csrf_token = csrf_token or uuid.uuid4().hex
        self.ext_server_port = ext_server_port
        self.ext_server_csrf = ext_server_csrf
        self._force_dummy = force_dummy
        self.account = account
        self._proc: Optional[subprocess.Popen] = None
        self._log_path: Optional[str] = None
        self._port: int = 0
        self._dummy_ext: Optional["DummyExtServer"] = None
        self._was_started: bool = False
        self._state_db_path: Optional[Path] = None  # アカウント固有 state DB

    def start(self) -> "LSInfo":
        """LS を起動して LSInfo を返す。

        1. IDE LS から ext_server_port/csrf を自動検出 (未指定時)
        2. stdin に metadata protobuf を注入
        3. ログから HTTP ポートを取得
        4. GetUserStatus で接続確認

        Returns:
            LSInfo (antigravity_client.py の既存データクラス)

        Raises:
            RuntimeError: 起動失敗
        """
        from mekhane.ochema.antigravity_client import LSInfo

        if self._proc and self._proc.poll() is None:
            raise RuntimeError(
                f"LS already running (PID {self._proc.pid}). Call stop() first."
            )

        if NonStandaloneLSManager._active_instances >= NonStandaloneLSManager.MAX_INSTANCES:
            raise RuntimeError(
                f"Cannot start LS: Maximum number of concurrent instances ({NonStandaloneLSManager.MAX_INSTANCES}) reached."
            )

        # Step 1: IDE LS 自動検出 → 失敗時/force_dummy時は DummyExtServer
        use_dummy = self._force_dummy
        if not use_dummy and (not self.ext_server_port or not self.ext_server_csrf):
            try:
                ide = detect_ide_ls()
                self.ext_server_port = self.ext_server_port or ide.ext_server_port
                self.ext_server_csrf = self.ext_server_csrf or ide.ext_server_csrf
                logger.info(
                    "IDE LS detected: ext_port=%d, PID=%d",
                    self.ext_server_port, ide.pid,
                )
            except RuntimeError:
                use_dummy = True

        if use_dummy:
            logger.info("Using DummyExtServer (force_dummy=%s)", self._force_dummy)

            # C9: アカウント固有の state DB を準備
            # 各 LS が独立した state DB を持つことで、6垢プールが可能
            nonstd_db_path = _STATE_DB_NONSTD.parent / f"state_nonstd_{self.account}.vscdb"
            try:
                if not nonstd_db_path.exists():
                    # ベースの state DB からコピーして初期化
                    base_db = _bootstrap_nonstd_state()
                    import shutil
                    shutil.copy2(base_db, nonstd_db_path)
                    logger.info("Created account-specific state DB: %s", nonstd_db_path)
                # トークンを注入
                provision_state_db(
                    access_token=None,
                    db_path=nonstd_db_path,
                    account=self.account,
                )
                logger.info("Token provisioned for account '%s' → %s", self.account, nonstd_db_path.name)
            except OSError as e:
                logger.warning("Account state DB setup failed for '%s': %s", self.account, e)
                nonstd_db_path = _STATE_DB_NONSTD
            self._state_db_path = nonstd_db_path

            from mekhane.ochema.ext_server import DummyExtServer
            self._dummy_ext = DummyExtServer(db_path=nonstd_db_path)
            self._dummy_ext.start()
            self.ext_server_port = self._dummy_ext.port
            self.ext_server_csrf = self._dummy_ext.csrf
            logger.info(
                "DummyExtServer started: port=%d",
                self.ext_server_port,
            )

        # Step 2: LS 起動
        if not LS_BINARY:
            raise RuntimeError(
                "LS binary not found. Antigravity IDE がインストールされていないか、"
                "パスが異なります。"
            )
        self._log_path = os.path.join(tempfile.gettempdir(), f"ls_nonstd_{self.workspace_id}.log")
        log_file = open(self._log_path, "w")

        cmd = [
            LS_BINARY,
            "--enable_lsp",
            _LS_PORT_FLAG,  # 1.20: --random_port / 1.21+: --http_server_port=0 (auto-detect)
            f"--extension_server_port={self.ext_server_port}",
            f"--cloud_code_endpoint={CLOUD_CODE_ENDPOINT}",
            f"--csrf_token={self.csrf_token}",
            f"--workspace_id={self.workspace_id}",
            "--app_data_dir=antigravity",
            "-v=2",
        ]
        # Note: --extension_server_csrf_token, --persistent_mode は
        # 現行 LS バイナリ (1.107.0+) で廃止済み。使用すると即 exit 2。

        env = os.environ.copy()
        if os.environ.get("USE_MITMPROXY") == "1":
            env["HTTP_PROXY"] = "http://127.0.0.1:8080"
            env["HTTPS_PROXY"] = "http://127.0.0.1:8080"
            env["SSL_CERT_FILE"] = "/tmp/combined_ca.pem"
            logger.info("Using MITMPROXY with SSL_CERT_FILE=%s", env["SSL_CERT_FILE"])
        if os.environ.get("USE_GODEBUG") == "1":
            env["GODEBUG"] = "http2debug=2"
            env["GRPC_GO_LOG_VERBOSITY_LEVEL"] = "99"
            env["GRPC_GO_LOG_SEVERITY_LEVEL"] = "info"
            logger.info("GODEBUG=http2debug=2 enabled")

        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
        )

        # Step 3: stdin に metadata protobuf を注入
        metadata = build_metadata()
        self._proc.stdin.write(metadata)
        self._proc.stdin.close()

        logger.info("LS starting (PID %d, workspace=%s)", self._proc.pid, self.workspace_id)

        # Step 4: ログからポートを取得 (ポーリング)
        deadline = time.time() + STARTUP_TIMEOUT
        while time.time() < deadline:
            if self._proc.poll() is not None:
                with open(self._log_path) as f:
                    log = f.read()
                raise RuntimeError(
                    f"LS died during startup (exit={self._proc.returncode}): {log[:500]}"
                )
            try:
                with open(self._log_path) as f:
                    log = f.read()
                self._port = parse_http_port(log)
                break
            except RuntimeError:
                time.sleep(0.3)
        else:
            self.stop()
            raise RuntimeError(f"LS startup timed out after {STARTUP_TIMEOUT}s")

        logger.info("LS started: port=%d, PID=%d", self._port, self._proc.pid)
        self._was_started = True

        info = LSInfo(
            pid=self._proc.pid,
            csrf=self.csrf_token,
            port=self._port,
            workspace=self.workspace_id,
            is_https=False,  # parse_http_port が HTTP ポートを返すので HTTP で接続
        )

        NonStandaloneLSManager._active_instances += 1
        return info

    def stop(self) -> None:
        """LS プロセスと DummyExtServer を停止する。"""
        if self._proc and self._proc.poll() is None:
            logger.info("Stopping LS (PID %d)", self._proc.pid)
            if _IS_WINDOWS:
                self._proc.terminate()
            else:
                self._proc.send_signal(signal.SIGTERM)
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=2)
            logger.info("LS stopped")
        self._proc = None

        # DummyExtServer も停止
        if self._dummy_ext is not None:
            self._dummy_ext.stop()
            self._dummy_ext = None

        if hasattr(self, "_was_started") and self._was_started:
            if NonStandaloneLSManager._active_instances > 0:
                NonStandaloneLSManager._active_instances -= 1
            self._was_started = False

    def is_alive(self) -> bool:
        """LS プロセスが生存しているか。"""
        return self._proc is not None and self._proc.poll() is None

    @property
    def pid(self) -> int:
        """LS の PID。"""
        return self._proc.pid if self._proc else 0

    @property
    def port(self) -> int:
        """LS の HTTP ポート。"""
        return self._port

    @property
    def log_path(self) -> Optional[str]:
        """LS のログファイルパス。"""
        return self._log_path

    def __del__(self):
        """デストラクタで LS を停止。"""
        try:
            self.stop()
        except OSError as _e:
            logger.debug("Ignored exception: %s", _e)

    def ensure_token_fresh(self, access_token: str | None = None) -> bool:
        """このマネージャーの state DB のトークンを最新に更新する。

        Headless 環境で LS を長時間稼働させる際に、ya29.* トークンの
        失効を防ぐために使用する。

        Args:
            access_token: 書き込むトークン。None なら TokenVault から自動取得。

        Returns:
            True if successfully refreshed.
        """
        return provision_state_db(
            access_token=access_token,
            db_path=self._state_db_path,
            account=self.account,
        )

    def __repr__(self) -> str:
        alive = self.is_alive()
        return (
            f"NonStandaloneLSManager("
            f"ws={self.workspace_id!r}, "
            f"port={self._port}, "
            f"pid={self.pid}, "
            f"alive={alive})"
        )


# --- Auth Provisioner (C9) ---

# 環境変数 STATE_DB でオーバーライド可能 (コンテナ対応)
_env_state_db = os.environ.get("STATE_DB", "")
if _env_state_db:
    _STATE_DB = Path(_env_state_db)
    _STATE_DB_NONSTD = _STATE_DB.parent / "state_nonstd.vscdb"
elif _IS_WINDOWS:
    _APPDATA = Path(os.environ.get("APPDATA", str(Path.home())))
    _STATE_DB = _APPDATA / "Antigravity" / "User" / "globalStorage" / "state.vscdb"
    _STATE_DB_NONSTD = _APPDATA / "Antigravity" / "User" / "globalStorage" / "state_nonstd.vscdb"
else:
    _STATE_DB = Path.home() / ".config" / "Antigravity" / "User" / "globalStorage" / "state.vscdb"
    _STATE_DB_NONSTD = Path.home() / ".config" / "Antigravity" / "User" / "globalStorage" / "state_nonstd.vscdb"


def _bootstrap_nonstd_state() -> Path:
    """Non-Standalone 用の隔離された state.vscdb のコピーを作成・取得する。

    IDE の flock 干渉を防ぐため、元の state.vscdb からデータを
    コピーして独立した DB (state_nonstd.vscdb) を作成する。
    すでに存在する場合はそれを再利用する (トークン等の更新を永続化するため)。
    """
    import sqlite3
    import shutil

    if not _STATE_DB.exists():
        raise RuntimeError(f"Original state.vscdb not found: {_STATE_DB}")

    if not _STATE_DB_NONSTD.exists():
        logger.info("Initializing nonstd state DB: %s", _STATE_DB_NONSTD)
        # file:.*?mode=ro&immutable=1 で元の DB から安全に読み出し、
        # sqlite3 の backup API を使って新しい DB ファイルにコピーする
        db_uri = f"file:{_STATE_DB}?mode=ro&immutable=1"
        try:
            source = sqlite3.connect(db_uri, uri=True, timeout=5.0)
            dest = sqlite3.connect(str(_STATE_DB_NONSTD))
            with source, dest:
                source.backup(dest)
            dest.close()
            source.close()
            logger.info("Successfully bootstrapped state_nonstd.vscdb")
        except OSError as e:
            logger.error("Failed to bootstrap state_nonstd.vscdb: %s", e)
            # フォールバックとして直接コピーを試みる
            shutil.copy2(_STATE_DB, _STATE_DB_NONSTD)

    return _STATE_DB_NONSTD


def _open_state_db_safe(db_path: Path | None = None):
    """state.vscdb (またはコピー) を安全に読み取り専用で開く。
    
    IDE が flock でロックを保持している場合でも、
    immutable=1 URI mode なら読み取り可能。
    """
    import sqlite3
    target_db = db_path or _STATE_DB
    db_uri = f"file:{target_db}?mode=ro&immutable=1"
    db = sqlite3.connect(db_uri, uri=True, timeout=5.0)
    return db


def provision_state_db(access_token: str | None = None, db_path: Path | None = None, account: str = "default") -> bool:
    """state.vscdb の antigravityAuthStatus に最新トークンを書き戻す。

    IDE がない環境 (Headless) で LS を起動する場合、state.vscdb 内の
    OAuth access_token が期限切れになると LS が認証に失敗する。
    この関数は TokenVault (gemini-cli refresh) で取得したトークンを
    state.vscdb に書き戻し、LS の認証を維持する。

    Args:
        access_token: 書き込むトークン。None の場合は TokenVault から自動取得。
        db_path: 書き込み先の DB ファイル。デフォルトは _STATE_DB_NONSTD。
        account: TokenVault のアカウント名。access_token=None 時に使用。

    Returns:
        True if successfully provisioned, False otherwise.
    """
    import json
    import sqlite3

    target_db = db_path or _STATE_DB_NONSTD

    if not target_db.exists():
        logger.warning("target DB not found: %s", target_db)
        # コピーが存在しない場合は作成を試みる
        if target_db == _STATE_DB_NONSTD:
            try:
                _bootstrap_nonstd_state()
            except RuntimeError as e:
                logger.error("Bootstrap failed: %s", e)
                return False
        else:
            return False

    # Step 1: トークンを取得
    if access_token is None:
        try:
            from mekhane.ochema.token_vault import TokenVault
            vault = TokenVault()
            access_token = vault.get_token(account)
            logger.info("TokenVault からトークン取得成功 (account=%s)", account)
        except (OSError, Exception) as e:  # noqa: BLE001
            logger.warning("TokenVault からトークン取得失敗: %s", e)
            return False

    if not access_token or not access_token.startswith("ya29."):
        logger.warning("Invalid access_token (not ya29.*)")
        return False

    # Step 2: 既存の antigravityAuthStatus を読み取り (対象 DB から — WAL 回避)
    try:
        read_db = _open_state_db_safe(target_db)
        row = read_db.execute(
            "SELECT value FROM ItemTable WHERE key = ?",
            ("antigravityAuthStatus",),
        ).fetchone()
        read_db.close()

        if not row:
            logger.warning("antigravityAuthStatus not found in state.vscdb")
            return False

        data = json.loads(row[0])
        old_token = data.get("apiKey", "")

        # Step 3: apiKey を新しいトークンで更新 — DB に直接書き込み
        data["apiKey"] = access_token
        new_value = json.dumps(data, ensure_ascii=False)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                write_db = sqlite3.connect(str(target_db), timeout=5.0)
                write_db.execute(
                    "UPDATE ItemTable SET value = ? WHERE key = ?",
                    (new_value, "antigravityAuthStatus"),
                )
                write_db.commit()
                write_db.close()
                break
            except sqlite3.OperationalError as oe:
                if "locked" in str(oe).lower() and attempt < max_retries - 1:
                    logger.warning(
                        "state.vscdb locked (attempt %d/%d), retrying in 1s: %s",
                        attempt + 1, max_retries, oe,
                    )
                    time.sleep(1)
                else:
                    raise

        logger.info(
            "state.vscdb provisioned: apiKey updated (%s... → %s...)",
            old_token[:15] if old_token else "empty",
            access_token[:15],
        )
        return True

    except OSError as e:
        logger.error("state.vscdb provisioning failed: %s", e)
        return False

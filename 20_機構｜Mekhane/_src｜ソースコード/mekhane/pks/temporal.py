from __future__ import annotations
# noqa: AI-ALL
# PROOF: [L2/インフラ] <- mekhane/pks/
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

A0 (FEP) → 時間的変化の検出は予測誤差最小化の前提
→ エンティティの変化・トレンド・異常を検出
→ temporal.py が担う

# PURPOSE: 時間的推論サービス — 知識の変化検出・トレンド分析・異常検出
# Origin: PKA (jpequegn/proactive-knowledge-agent) temporal.py パターンを
#          HGK ファイルベース (JSONL+JSON) に適合させた実装
"""


import json
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


# --- データモデル ---


class TrendDirection(str, Enum):
    """トレンドの方向"""
    RISING = "RISING"
    FALLING = "FALLING"
    STABLE = "STABLE"


class AnomalyType(str, Enum):
    """異常の種別"""
    SPIKE = "SPIKE"      # 急増 (3σ 超過)
    DROP = "DROP"        # 急減 (-2σ 超過)
    SILENCE = "SILENCE"  # 長期未観測


# PURPOSE: エンティティの観測記録
@dataclass
class Observation:
    """エンティティの1回の観測"""
    entity_id: str
    field_name: str  # 例: "citations", "mentions", "status"
    value: str
    timestamp: str   # ISO 8601

    # PURPOSE: JSONL 行に変換
    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "field": self.field_name,
            "value": self.value,
            "timestamp": self.timestamp,
        }

    # PURPOSE: JSONL 行から復元
    @classmethod
    def from_dict(cls, d: dict) -> Observation:
        return cls(
            entity_id=d["entity_id"],
            field_name=d["field"],
            value=d["value"],
            timestamp=d["timestamp"],
        )


# PURPOSE: 変更検出結果
@dataclass
class ChangeEvent:
    """フィールド値の変更を表すイベント"""
    entity_id: str
    field_name: str
    old_value: str
    new_value: str
    timestamp: str


# PURPOSE: 言及回数の統計
@dataclass
class MentionStats:
    """エンティティの言及回数変化"""
    entity_id: str
    current_count: int
    previous_count: int
    change_ratio: float  # (current - previous) / max(previous, 1)


# PURPOSE: トレンド分析結果
@dataclass
class TrendResult:
    """エンティティのトレンド"""
    entity_id: str
    direction: TrendDirection
    change_ratio: float
    period_days: int


# PURPOSE: 異常検出結果
@dataclass
class AnomalyResult:
    """検出された異常"""
    entity_id: str
    anomaly_type: AnomalyType
    score: float       # 異常の強度
    threshold: float   # 使用した閾値
    details: str


# --- 指数減衰関数 ---


# PURPOSE: ExponentialDecay — PKA から直接 Import したパターン
class ExponentialDecay:
    """指数減衰関数: score = e^{-λt}

    PKA (proactive-knowledge-agent) の ExponentialDecay を
    そのまま移植。情報の鮮度をスコア化する。

    half_life_days=7 のとき:
      - 0日前: 1.0
      - 7日前: 0.5
      - 14日前: 0.25
      - 30日前: ≈0.05
    """

    # PURPOSE: 減衰パラメータの初期化
    def __init__(self, half_life_days: float = 7.0):
        if half_life_days <= 0:
            raise ValueError("half_life_days は正の値でなければならない")
        self.half_life_days = half_life_days
        self._lambda = math.log(2) / half_life_days

    # PURPOSE: 経過日数からスコアを計算
    def decay(self, age_days: float) -> float:
        """経過日数から減衰スコアを返す (0.0〜1.0)"""
        if age_days < 0:
            return 1.0
        return math.exp(-self._lambda * age_days)

    # PURPOSE: タイムスタンプからスコアを計算
    def score_from_timestamp(
        self, timestamp: str, now: Optional[datetime] = None
    ) -> float:
        """ISO 8601 タイムスタンプから減衰スコアを返す"""
        if now is None:
            now = datetime.now()
        try:
            ts = datetime.fromisoformat(timestamp)
            age = (now - ts).total_seconds() / 86400  # 日数に変換
            return self.decay(age)
        except (ValueError, TypeError):
            return 0.0


# --- TemporalReasoningService ---


# PURPOSE: 時間的推論サービス — 変化検出 + トレンド分析 + 異常検出
class TemporalReasoningService:
    """時間的推論サービス

    PKA の TemporalReasoningService パターンを HGK ファイルベースに適合。
    PostgreSQL + pgvector の代わりに JSONL + JSON で状態管理。

    使い方:
        svc = TemporalReasoningService("/path/to/state")
        svc.record_observation("paper_001", "citations", "10")
        # ... 時間経過 ...
        svc.record_observation("paper_001", "citations", "25")
        changes = svc.get_changes_since(datetime(2026, 3, 1))
        trends = svc.analyze_trends(period_days=7)
        anomalies = svc.detect_anomalies()
    """

    # PURPOSE: 状態ディレクトリ・減衰関数の初期化
    def __init__(
        self,
        state_dir: str | Path,
        half_life_days: float = 7.0,
        max_obs_lines: int = 10_000,
    ):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.decay = ExponentialDecay(half_life_days=half_life_days)
        self._max_obs_lines = max_obs_lines
        self._obs_file = self.state_dir / "observations.jsonl"
        self._stats_file = self.state_dir / "entity_stats.json"

    # --- 観測記録 ---

    # PURPOSE: 観測を記録する
    def record_observation(
        self,
        entity_id: str,
        field_name: str,
        value: str,
        timestamp: Optional[str] = None,
    ) -> Observation:
        """エンティティのフィールド値を観測として記録する

        Args:
            entity_id: エンティティ識別子 (例: "paper_001", "concept_fep")
            field_name: フィールド名 (例: "citations", "mentions", "status")
            value: 値 (文字列統一。数値も文字列で保持)
            timestamp: ISO 8601 タイムスタンプ (省略時は now)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        obs = Observation(
            entity_id=entity_id,
            field_name=field_name,
            value=value,
            timestamp=timestamp,
        )

        # JSONL に追記
        with open(self._obs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(obs.to_dict(), ensure_ascii=False) + "\n")

        # エンティティ統計を更新
        self._update_stats(entity_id, timestamp)

        # ローテーションチェック
        self._rotate_if_needed()

        return obs

    # PURPOSE: エンティティ統計を更新
    def _update_stats(self, entity_id: str, timestamp: str) -> None:
        """entity_stats.json を更新 (first_seen/last_seen/mention_count/daily_counts)"""
        stats = self._load_stats()
        entity = stats.get(entity_id, {
            "first_seen": timestamp,
            "last_seen": timestamp,
            "mention_count": 0,
            "daily_counts": {},
        })

        entity["last_seen"] = timestamp
        entity["mention_count"] = entity.get("mention_count", 0) + 1

        # 日次カウント集計
        day_key = timestamp[:10]  # "2026-03-14"
        daily = entity.get("daily_counts", {})
        daily[day_key] = daily.get(day_key, 0) + 1
        entity["daily_counts"] = daily

        stats[entity_id] = entity
        self._save_stats(stats)

    # --- 変更検出 ---

    # PURPOSE: 指定日時以降の変更イベントを検出
    def get_changes_since(
        self, since: datetime | str
    ) -> list[ChangeEvent]:
        """指定日時以降のフィールド値の変更を検出する

        同一 entity_id + field の観測が since 前後で異なる値を持つ場合、
        ChangeEvent として返す。
        """
        if isinstance(since, str):
            since = datetime.fromisoformat(since)

        since_iso = since.isoformat()

        # 全観測をロード
        observations = self._load_observations()

        # entity_id + field ごとに since 前後の最新値を取得
        # before: since 以前の最新値
        # after: since 以降の最新値
        before: dict[tuple[str, str], Observation] = {}
        after: dict[tuple[str, str], Observation] = {}

        for obs in observations:
            key = (obs.entity_id, obs.field_name)
            if obs.timestamp < since_iso:
                # since 前: 最新のもの (上書き OK、ソート済み前提)
                existing = before.get(key)
                if existing is None or obs.timestamp > existing.timestamp:
                    before[key] = obs
            else:
                # since 後: 最新のもの
                existing = after.get(key)
                if existing is None or obs.timestamp > existing.timestamp:
                    after[key] = obs

        # 変更検出
        changes: list[ChangeEvent] = []
        for key, after_obs in after.items():
            before_obs = before.get(key)
            if before_obs is None:
                # 新規エンティティ (before がない)
                changes.append(ChangeEvent(
                    entity_id=after_obs.entity_id,
                    field_name=after_obs.field_name,
                    old_value="",
                    new_value=after_obs.value,
                    timestamp=after_obs.timestamp,
                ))
            elif before_obs.value != after_obs.value:
                # 値が変化
                changes.append(ChangeEvent(
                    entity_id=after_obs.entity_id,
                    field_name=after_obs.field_name,
                    old_value=before_obs.value,
                    new_value=after_obs.value,
                    timestamp=after_obs.timestamp,
                ))

        # タイムスタンプでソート (新しい順)
        changes.sort(key=lambda c: c.timestamp, reverse=True)
        return changes

    # --- トレンド分析 ---

    # PURPOSE: エンティティの言及トレンドを分析
    def analyze_trends(
        self,
        period_days: int = 7,
        min_observations: int = 2,
    ) -> list[TrendResult]:
        """エンティティの言及回数トレンドを分析する

        current (直近 period_days) vs previous (その前の period_days) を比較し、
        RISING / FALLING / STABLE を判定。

        Args:
            period_days: 比較期間の長さ (日)
            min_observations: 最小観測回数 (これ未満のエンティティは無視)
        """
        stats = self._load_stats()
        now = datetime.now()
        current_start = (now - timedelta(days=period_days)).strftime("%Y-%m-%d")
        previous_start = (now - timedelta(days=period_days * 2)).strftime("%Y-%m-%d")
        current_end = now.strftime("%Y-%m-%d")

        results: list[TrendResult] = []

        for entity_id, entity_stats in stats.items():
            daily = entity_stats.get("daily_counts", {})

            # 期間の合計カウント
            current_count = sum(
                count for day, count in daily.items()
                if current_start <= day <= current_end
            )
            previous_count = sum(
                count for day, count in daily.items()
                if previous_start <= day < current_start
            )

            total = current_count + previous_count
            if total < min_observations:
                continue

            # 変化率
            denominator = max(previous_count, 1)
            change_ratio = (current_count - previous_count) / denominator

            # 方向判定 (±20% を閾値)
            if change_ratio > 0.2:
                direction = TrendDirection.RISING
            elif change_ratio < -0.2:
                direction = TrendDirection.FALLING
            else:
                direction = TrendDirection.STABLE

            results.append(TrendResult(
                entity_id=entity_id,
                direction=direction,
                change_ratio=round(change_ratio, 3),
                period_days=period_days,
            ))

        # 変化率の絶対値でソート (大きい変化が先)
        results.sort(key=lambda r: abs(r.change_ratio), reverse=True)
        return results

    # PURPOSE: 言及回数の変化統計を返す
    def get_mention_changes(
        self,
        period_days: int = 7,
    ) -> list[MentionStats]:
        """エンティティの言及回数変化 (current vs previous) を返す"""
        stats = self._load_stats()
        now = datetime.now()
        current_start = (now - timedelta(days=period_days)).strftime("%Y-%m-%d")
        previous_start = (now - timedelta(days=period_days * 2)).strftime("%Y-%m-%d")
        current_end = now.strftime("%Y-%m-%d")

        results: list[MentionStats] = []

        for entity_id, entity_stats in stats.items():
            daily = entity_stats.get("daily_counts", {})

            current_count = sum(
                count for day, count in daily.items()
                if current_start <= day <= current_end
            )
            previous_count = sum(
                count for day, count in daily.items()
                if previous_start <= day < current_start
            )

            denominator = max(previous_count, 1)
            change_ratio = (current_count - previous_count) / denominator

            results.append(MentionStats(
                entity_id=entity_id,
                current_count=current_count,
                previous_count=previous_count,
                change_ratio=round(change_ratio, 3),
            ))

        results.sort(key=lambda m: abs(m.change_ratio), reverse=True)
        return results

    # --- 異常検出 ---

    # PURPOSE: 異常を検出する
    def detect_anomalies(
        self,
        spike_sigma: float = 3.0,
        drop_sigma: float = 2.0,
        silence_days: int = 14,
    ) -> list[AnomalyResult]:
        """日次カウントの統計的異常を検出する

        PKA パターン:
        - SPIKE: 直近の日次カウントが平均 + spike_sigma × σ を超過
        - DROP: 直近の日次カウントが平均 - drop_sigma × σ を下回る
        - SILENCE: last_seen が silence_days を超過
        """
        stats = self._load_stats()
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        anomalies: list[AnomalyResult] = []

        for entity_id, entity_stats in stats.items():
            daily = entity_stats.get("daily_counts", {})

            # SILENCE 検出
            last_seen = entity_stats.get("last_seen", "")
            if last_seen:
                try:
                    last_dt = datetime.fromisoformat(last_seen)
                    days_silent = (now - last_dt).days
                    if days_silent >= silence_days:
                        anomalies.append(AnomalyResult(
                            entity_id=entity_id,
                            anomaly_type=AnomalyType.SILENCE,
                            score=float(days_silent),
                            threshold=float(silence_days),
                            details=f"{days_silent}日間未観測 (閾値: {silence_days}日)",
                        ))
                except (ValueError, TypeError):
                    pass

            # SPIKE / DROP 検出
            if len(daily) < 3:
                # 3日未満の観測ではσ計算不能
                continue

            counts = list(daily.values())
            mean = statistics.mean(counts)
            stdev = statistics.stdev(counts)

            if stdev == 0:
                continue  # 全日同数なら異常なし

            # 直近日のカウント
            recent_count = daily.get(today, 0)
            z_score = (recent_count - mean) / stdev

            if z_score > spike_sigma:
                anomalies.append(AnomalyResult(
                    entity_id=entity_id,
                    anomaly_type=AnomalyType.SPIKE,
                    score=round(z_score, 2),
                    threshold=spike_sigma,
                    details=f"本日 {recent_count} 件 (平均 {mean:.1f}, σ={stdev:.1f}, z={z_score:.1f})",
                ))
            elif z_score < -drop_sigma:
                anomalies.append(AnomalyResult(
                    entity_id=entity_id,
                    anomaly_type=AnomalyType.DROP,
                    score=round(abs(z_score), 2),
                    threshold=drop_sigma,
                    details=f"本日 {recent_count} 件 (平均 {mean:.1f}, σ={stdev:.1f}, z={z_score:.1f})",
                ))

        anomalies.sort(key=lambda a: a.score, reverse=True)
        return anomalies

    # --- 減衰スコア ---

    # PURPOSE: エンティティの減衰スコアを一括取得
    def get_decayed_scores(
        self,
        entity_ids: Optional[list[str]] = None,
    ) -> dict[str, float]:
        """各エンティティの last_seen からの減衰スコアを返す"""
        stats = self._load_stats()
        now = datetime.now()
        result: dict[str, float] = {}

        targets = entity_ids if entity_ids else list(stats.keys())

        for eid in targets:
            entity = stats.get(eid)
            if entity and entity.get("last_seen"):
                result[eid] = self.decay.score_from_timestamp(
                    entity["last_seen"], now=now
                )
            else:
                result[eid] = 0.0

        return result

    # --- 内部ヘルパー ---

    # PURPOSE: observations.jsonl から全観測をロード
    def _load_observations(self) -> list[Observation]:
        """JSONL ファイルから全観測をロード"""
        observations: list[Observation] = []
        if not self._obs_file.exists():
            return observations

        for line in self._obs_file.read_text("utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                observations.append(Observation.from_dict(d))
            except (json.JSONDecodeError, KeyError):
                continue

        return observations

    # PURPOSE: entity_stats.json をロード
    def _load_stats(self) -> dict:
        """エンティティ統計をロード"""
        if not self._stats_file.exists():
            return {}
        try:
            return json.loads(self._stats_file.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    # PURPOSE: entity_stats.json を保存
    def _save_stats(self, stats: dict) -> None:
        """エンティティ統計を保存"""
        self._stats_file.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2), "utf-8"
        )

    # --- ログローテーション ---

    # PURPOSE: observations.jsonl が閾値を超えたらローテーション
    def _rotate_if_needed(self) -> None:
        """observations.jsonl が max_obs_lines を超えたら古い行をアーカイブ

        戦略: 直近 max_obs_lines // 2 行を残し、残りを .bak に移動。
        entity_stats.json は集計値なのでローテーション不要。
        """
        if not self._obs_file.exists():
            return

        try:
            lines = self._obs_file.read_text("utf-8").strip().split("\n")
        except OSError:
            return

        if len(lines) <= self._max_obs_lines:
            return

        # 直近 half を保持、残りをアーカイブ
        keep_count = self._max_obs_lines // 2
        archive_lines = lines[:-keep_count]
        keep_lines = lines[-keep_count:]

        # アーカイブファイルに追記
        ts = datetime.now().strftime("%Y%m")
        archive_file = self.state_dir / f"observations_{ts}.bak.jsonl"
        with open(archive_file, "a", encoding="utf-8") as f:
            f.write("\n".join(archive_lines) + "\n")

        # 本体を縮小
        self._obs_file.write_text(
            "\n".join(keep_lines) + "\n", "utf-8"
        )

        print(
            f"[Temporal] ローテーション実行: "
            f"{len(archive_lines)} 行アーカイブ → {archive_file.name}, "
            f"{len(keep_lines)} 行保持"
        )

    # --- サマリ ---

    # PURPOSE: Sympatheia 通知用のサマリを生成
    def generate_summary(
        self,
        period_days: int = 7,
        max_items: int = 5,
    ) -> str:
        """時間的推論の結果をサマリテキストとして返す

        PKS → Sympatheia notification に渡すための形式。
        """
        lines: list[str] = [f"📊 時間的推論レポート (直近 {period_days} 日)"]
        lines.append("")

        # トレンド
        trends = self.analyze_trends(period_days=period_days)
        rising = [t for t in trends if t.direction == TrendDirection.RISING]
        falling = [t for t in trends if t.direction == TrendDirection.FALLING]

        if rising:
            lines.append("📈 **上昇トレンド**:")
            for t in rising[:max_items]:
                pct = int(t.change_ratio * 100)
                lines.append(f"  - {t.entity_id}: +{pct}%")

        if falling:
            lines.append("📉 **下降トレンド**:")
            for t in falling[:max_items]:
                pct = int(abs(t.change_ratio) * 100)
                lines.append(f"  - {t.entity_id}: -{pct}%")

        # 異常
        anomalies = self.detect_anomalies()
        if anomalies:
            lines.append("")
            lines.append("⚠️ **異常検出**:")
            for a in anomalies[:max_items]:
                lines.append(f"  - [{a.anomaly_type.value}] {a.entity_id}: {a.details}")

        if len(lines) <= 2:
            lines.append("変化なし")

        return "\n".join(lines)

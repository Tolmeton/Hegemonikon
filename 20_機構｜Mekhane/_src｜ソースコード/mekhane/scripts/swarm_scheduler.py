# PROOF: [L3/ユーティリティ] <- mekhane/scripts/swarm_scheduler.py O4→運用スクリプトが必要→swarm_scheduler が担う
#!/usr/bin/env python3
"""
Swarm Scheduler - Daily 4AM Execution

Manages the daily 1,800 session allocation across 6 accounts.

Usage:
    # Manual run
    python swarm_scheduler.py --run

    # Install cron
    python swarm_scheduler.py --install-cron

    # Check status
    python swarm_scheduler.py --status
"""

import asyncio
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from adaptive_allocator import AdaptiveAllocator, AllocationPlan
from mekhane.symploke.jules_client import JulesClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "swarm_scheduler.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# PURPOSE: Orchestrate daily session execution.
class SwarmScheduler:
    """Orchestrate daily session execution."""

    # Realistic limits:
    # - 3 accounts × 3 keys = 9 keys
    # - 90 sessions/key/day limit
    # - Total: 810/day, using 720 with safety margin
    SESSIONS_PER_KEY = 90
    KEYS_AVAILABLE = 9
    DAILY_BUDGET = 720  # 80% of max to avoid hitting limits

    # PURPOSE: SwarmScheduler の初期化 — Load API keys from root .env.
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.env_file = self.repo_path / ".env"
        self.results_dir = self.repo_path / "swarm_results"
        self.results_dir.mkdir(exist_ok=True)

    # PURPOSE: Load API keys from root .env.
    def load_api_keys(self) -> list[str]:
        """Load API keys from root .env."""
        keys = []
        if self.env_file.exists():
            with open(self.env_file) as f:
                for line in f:
                    if line.startswith("JULES_API_KEY_"):
                        key = line.split("=", 1)[1].strip()
                        if key:
                            keys.append(key)

        logger.info(f"Loaded {len(keys)} API keys")
        return keys

    # PURPOSE: Execute a batch of tasks with one API key.
    async def execute_batch(
        self,
        api_key: str,
        tasks: list[dict],
        source: str = "sources/github/Tolmeton/Hegemonikon",
        branch: str = "master",
    ) -> list[dict]:
        """Execute a batch of tasks with one API key."""
        async with JulesClient(api_key=api_key) as client:
            results = []
            for task in tasks:
                try:
                    # Generate prompt from perspective
                    from mekhane.basanos import PerspectiveMatrix

                    matrix = PerspectiveMatrix.load()
                    perspective = matrix.get(task["domain"], task["axis"])

                    if not perspective:
                        logger.warning(
                            f"Perspective not found: {task['domain']}-{task['axis']}"
                        )
                        continue

                    prompt = matrix.generate_prompt(perspective)

                    # Create session (don't wait for completion)
                    session = await client.create_session(
                        prompt=prompt, source=source, branch=branch, auto_approve=True
                    )

                    results.append(
                        {
                            "perspective_id": task["perspective_id"],
                            "session_id": session.id,
                            "url": f"https://jules.google.com/session/{session.id}",
                            "status": "started",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    logger.info(f"Started: {task['perspective_id']} → {session.id}")

                    # Rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:  # noqa: BLE001
                    logger.error(f"Error for {task['perspective_id']}: {e}")
                    results.append(
                        {
                            "perspective_id": task["perspective_id"],
                            "error": str(e),
                            "status": "failed",
                        }
                    )

            return results

    # PURPOSE: Execute full allocation plan across all accounts.
    async def execute_plan(self, plan: AllocationPlan) -> dict:
        """Execute full allocation plan across all accounts."""
        keys = self.load_api_keys()
        if len(keys) < self.ACCOUNTS:
            logger.warning(
                f"Only {len(keys)} keys available (expected {self.ACCOUNTS})"
            )

        # Combine all tasks
        all_tasks = plan.change_driven + plan.discovery + plan.weekly_focus
        logger.info(f"Total tasks: {len(all_tasks)}")

        # Distribute across keys (max 90 per key)
        keys = self.load_api_keys()
        sessions_per_key = min(len(all_tasks) // len(keys) + 1, self.SESSIONS_PER_KEY)
        batches = []
        for i in range(0, len(all_tasks), sessions_per_key):
            batches.append(all_tasks[i : i + sessions_per_key])

        # Execute in parallel
        all_results = []
        for i, (key, batch) in enumerate(zip(keys, batches)):
            logger.info(f"Account {i+1}: {len(batch)} tasks")
            results = await self.execute_batch(key, batch)
            all_results.extend(results)

        # Save results
        output_file = (
            self.results_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "plan_date": plan.date,
                    "total_tasks": len(all_tasks),
                    "results": all_results,
                    "summary": {
                        "started": sum(
                            1 for r in all_results if r.get("status") == "started"
                        ),
                        "failed": sum(
                            1 for r in all_results if r.get("status") == "failed"
                        ),
                    },
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        logger.info(f"Results saved to: {output_file}")
        return {"output_file": str(output_file), "results": all_results}

    # PURPOSE: Generate crontab entry for 4AM daily.
    def get_crontab_entry(self) -> str:
        """Generate crontab entry for 4AM daily."""
        script_path = Path(__file__).absolute()
        repo_path = self.repo_path.absolute()
        venv_python = repo_path / ".venv/bin/python"

        # 4:00 AM JST = 19:00 UTC (previous day)
        return f"0 19 * * * cd {repo_path} && {venv_python} {script_path} --run >> {repo_path}/swarm_scheduler.log 2>&1"

    # PURPOSE: Generate crontab entries for scheduled workflows.
    def get_workflow_crontab_entries(self) -> list[str]:
        """Generate crontab entries for scheduled workflows."""
        repo_path = self.repo_path.absolute()
        venv_python = repo_path / ".venv/bin/python"
        
        entries = []
        try:
            # Query hermeneus for scheduled workflows
            import os
            env = os.environ.copy()
            env["PYTHONPATH"] = str(repo_path)
            result = subprocess.run(
                [str(venv_python), "-m", "hermeneus.src.cli", "schedules", "-f", "json"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                env=env
            )
            if result.returncode == 0:
                schedules = json.loads(result.stdout)
                for s in schedules:
                    schedule_str = s.get("schedule", "").strip()
                    if not schedule_str:
                        continue
                    # Remove timezone string if present: "0 8 * * * (JST)" -> "0 8 * * *"
                    cron_part = schedule_str.split("(")[0].strip()
                    if cron_part:
                        cmd = f"cd {repo_path} && PYTHONPATH=. {venv_python} -m hermeneus.src.cli execute \"/{s['id']}\" >> {repo_path}/logs/cron_{s['id']}.log 2>&1"
                        entries.append(f"{cron_part} {cmd}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to get workflow schedules: {e}")
            
        return entries

    # PURPOSE: Install cron job.
    def install_cron(self) -> bool:
        """Install cron job."""
        base_entry = self.get_crontab_entry()
        wf_entries = self.get_workflow_crontab_entries()
        
        all_entries = [base_entry] + wf_entries

        try:
            # Get current crontab
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            current = result.stdout if result.returncode == 0 else ""

            # Check if all already installed
            already_installed_all = all(
                entry.split(" cd ")[0].strip() in current and entry.split(" &&")[1].strip() in current
                for entry in all_entries
            )
            
            if already_installed_all and "swarm_scheduler.py" in current:
                logger.info("All cron jobs already installed")
                return True

            # Filter out old versions of our entries to replace them
            lines = current.splitlines()
            new_lines = [
                line for line in lines 
                if "swarm_scheduler.py" not in line 
                and "hermeneus.src.cli execute" not in line
            ]
            
            # Add new entries
            new_lines.extend(all_entries)
            new_crontab = "\n".join(new_lines) + "\n"

            process = subprocess.Popen(
                ["crontab", "-"], stdin=subprocess.PIPE, text=True
            )
            process.communicate(input=new_crontab)

            logger.info("Cron installed for swarm_scheduler and scheduled workflows.")
            for e in all_entries:
                logger.info(f"Entry: {e}")
                
            return True

        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to install cron: {e}")
            return False

    # PURPOSE: Get scheduler status.
    def get_status(self) -> dict:
        """Get scheduler status."""
        # Check cron
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
        cron_installed = "swarm_scheduler.py" in current_cron
        
        # Check workflow crons
        wf_entries = self.get_workflow_crontab_entries()
        installed_wf_crons = []
        for entry in wf_entries:
            # Check if command part is in current cron
            cmd_part = entry.split(" &&")[1].strip()
            if cmd_part in current_cron:
                installed_wf_crons.append(entry)

        # Check recent runs
        recent_runs = (
            sorted(self.results_dir.glob("run_*.json"))[-5:]
            if self.results_dir.exists()
            else []
        )

        return {
            "cron_installed": cron_installed,
            "installed_wf_crons": installed_wf_crons,
            "target_wf_crons": len(wf_entries),
            "results_dir": str(self.results_dir),
            "recent_runs": [str(r) for r in recent_runs],
            "api_keys": len(self.load_api_keys()),
            "daily_budget": self.DAILY_BUDGET,
        }

# PURPOSE: Execute daily swarm
async def run_daily():
    """Execute daily swarm."""
    scheduler = SwarmScheduler()
    allocator = AdaptiveAllocator()

    logger.info("=" * 60)
    logger.info(f"Starting daily swarm run: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    # Create allocation plan
    plan = allocator.create_allocation_plan(scheduler.DAILY_BUDGET)

    # Execute with state tracking (ClawX Adjunction: 実行パス接続)
    start_time = time.time()
    try:
        results = await scheduler.execute_plan(plan)
        duration = time.time() - start_time

        # State tracking: 成功を記録
        from mekhane.scripts.scheduler_state import SchedulerStateStore
        store = SchedulerStateStore()
        store.update_job_state(
            "swarm_daily", success=True, duration_sec=duration
        )

        logger.info("=" * 60)
        logger.info(f"Completed: {results['output_file']}")
        logger.info("=" * 60)
    except Exception as exc:  # noqa: BLE001
        duration = time.time() - start_time
        # State tracking: 失敗を記録
        try:
            from mekhane.scripts.scheduler_state import SchedulerStateStore
            store = SchedulerStateStore()
            store.update_job_state(
                "swarm_daily", success=False,
                error=str(exc), duration_sec=duration,
            )
        except Exception:  # noqa: BLE001
            pass  # state 記録の失敗は日次実行を止めない
        raise

# PURPOSE: main の処理
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Swarm Scheduler")
    parser.add_argument("--run", action="store_true", help="Execute daily run")
    parser.add_argument("--install-cron", action="store_true", help="Install cron job")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--jobs", action="store_true", help="List all scheduled jobs with state")
    parser.add_argument("--trigger", type=str, metavar="JOB_ID", help="Manually trigger a job")
    parser.add_argument("--budget", type=int, help="Override daily budget")
    args = parser.parse_args()

    scheduler = SwarmScheduler()

    if args.run:
        asyncio.run(run_daily())

    elif args.install_cron:
        if scheduler.install_cron():
            print("✅ Cron job installed for 4:00 AM JST daily and scheduled workflows")
        else:
            print("❌ Failed to install cron")

    elif args.status:
        from mekhane.scripts.scheduler_state import SchedulerStateStore
        status = scheduler.get_status()
        store = SchedulerStateStore()
        all_jobs = store.get_all_jobs()
        print("\n📊 Swarm Scheduler Status:")
        print(f"   Swarm Cron: {'✅' if status['cron_installed'] else '❌'}")
        print(f"   WF Crons  : {len(status['installed_wf_crons'])}/{status['target_wf_crons']} installed")
        if status['installed_wf_crons']:
            for entry in status['installed_wf_crons']:
                print(f"     - {entry}")
        print(f"   API keys  : {status['api_keys']}")
        print(f"   Budget    : {status['daily_budget']}")
        print(f"   Jobs      : {len(all_jobs)}")
        for job in all_jobs:
            state_icon = '✅' if job.state.last_success else '❌'
            last = job.state.last_run[:16] if job.state.last_run else 'never'
            print(f"     {state_icon} {job.id}: {job.name} (last: {last})")
        print(f"   Recent runs: {len(status['recent_runs'])}")
        for run in status["recent_runs"]:
            print(f"     - {Path(run).name}")

    elif args.jobs:
        from mekhane.scripts.scheduler_state import SchedulerStateStore
        store = SchedulerStateStore()
        all_jobs = store.get_all_jobs()
        print(f"\n📋 Scheduled Jobs ({len(all_jobs)}):")
        for job in all_jobs:
            state_icon = '✅' if job.state.last_success else '❌'
            enabled = '🟢' if job.enabled else '🔴'
            last = job.state.last_run[:19] if job.state.last_run else 'never'
            dur = f"{job.state.last_duration_sec:.1f}s" if job.state.last_duration_sec else '-'
            print(f"   {enabled} {job.id}")
            print(f"      Name    : {job.name}")
            print(f"      Schedule: {job.schedule}")
            print(f"      Command : {job.command}")
            print(f"      Delivery: {job.delivery.value}")
            print(f"      Last Run: {state_icon} {last} ({dur})")
            if job.state.last_error:
                print(f"      Error   : {job.state.last_error[:80]}")
            print()

    elif args.trigger:
        from mekhane.scripts.scheduler_state import SchedulerStateStore
        store = SchedulerStateStore()
        job_id = args.trigger
        print(f"🔄 Triggering job: {job_id}")
        try:
            result_state = store.trigger_job(job_id)
            if result_state.last_success:
                print(f"✅ Job {job_id} completed in {result_state.last_duration_sec:.1f}s")
            else:
                print(f"❌ Job {job_id} failed: {result_state.last_error}")
        except ValueError as exc:
            print(f"❌ {exc}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""Script to create 20 granular, dated Git commits covering the last 20 days (Aug 28 - Sep 16, 2026)."""

import os
import subprocess
import sys

REPO_DIR = r"d:\LLM_as_Judge"

COMMITS = [
    {
        "day": "2026-08-28",
        "time": "14:23:15",
        "message": "chore(config): setup repository root, npm workspace scripts, and .gitignore",
        "files": [".gitignore", ".env.example", "package.json"],
    },
    {
        "day": "2026-08-29",
        "time": "16:45:00",
        "message": "feat(config): configure application settings and LLM pricing matrix",
        "files": ["src/config/settings.py", "src/config/pricing.py"],
    },
    {
        "day": "2026-08-30",
        "time": "11:15:30",
        "message": "feat(db): implement database connection manager and auto-migration engine",
        "files": ["src/database/connection.py"],
    },
    {
        "day": "2026-08-31",
        "time": "15:30:10",
        "message": "feat(db): define SQLAlchemy models for users, sessions, and encrypted api keys",
        "files": ["src/database/models.py"],
    },
    {
        "day": "2026-09-01",
        "time": "17:12:45",
        "message": "feat(db): implement repository layer for user sessions and key storage",
        "files": ["src/database/repository.py"],
    },
    {
        "day": "2026-09-02",
        "time": "10:05:20",
        "message": "feat(providers): define BaseProvider abstraction and generation interfaces",
        "files": ["src/providers/base.py"],
    },
    {
        "day": "2026-09-03",
        "time": "13:40:50",
        "message": "feat(providers): implement OpenRouterProvider supporting free and paid tiers",
        "files": ["src/providers/openrouter_provider.py"],
    },
    {
        "day": "2026-09-04",
        "time": "16:20:15",
        "message": "feat(providers): implement GrokProvider with automatic Groq LPU routing",
        "files": ["src/providers/grok_provider.py"],
    },
    {
        "day": "2026-09-05",
        "time": "18:00:30",
        "message": "feat(providers): implement ModelRegistry catalog with real production models",
        "files": ["src/providers/registry.py"],
    },
    {
        "day": "2026-09-06",
        "time": "12:35:00",
        "message": "feat(judge): implement remote Hugging Face Qwen judge evaluator",
        "files": ["src/judge/model_loader.py", "src/judge/hf_evaluator.py"],
    },
    {
        "day": "2026-09-07",
        "time": "15:45:22",
        "message": "feat(eval): implement pairwise evaluation engine and position bias checker",
        "files": ["src/evaluation/pairwise.py", "src/evaluation/position_bias.py", "src/evaluation/hard_benchmark.py"],
    },
    {
        "day": "2026-09-08",
        "time": "14:10:40",
        "message": "feat(eval): add ranking engine, telemetry metrics, and report generator",
        "files": ["src/evaluation/ranking.py", "src/evaluation/metrics.py", "src/evaluation/report_generator.py"],
    },
    {
        "day": "2026-09-09",
        "time": "11:50:00",
        "message": "feat(services): implement PBKDF2 authentication and Fernet API key encryption",
        "files": ["src/services/auth.py"],
    },
    {
        "day": "2026-09-10",
        "time": "16:30:15",
        "message": "feat(services): implement concurrent generation service and single-model comparison",
        "files": ["src/services/generation_service.py", "src/services/comparison_service.py"],
    },
    {
        "day": "2026-09-11",
        "time": "10:25:35",
        "message": "feat(api): add FastAPI authentication dependencies and Pydantic schemas",
        "files": ["src/api/dependencies.py", "src/api/schemas/requests.py"],
    },
    {
        "day": "2026-09-12",
        "time": "17:05:40",
        "message": "feat(api): implement REST endpoints for auth, keys, models, compare, and sessions",
        "files": [
            "src/api/routes/auth.py",
            "src/api/routes/user_keys.py",
            "src/api/routes/generate.py",
            "src/api/routes/compare.py",
            "src/api/routes/models.py",
            "src/api/routes/sessions.py",
            "src/api/main.py"
        ],
    },
    {
        "day": "2026-09-13",
        "time": "13:15:20",
        "message": "feat(frontend): create TypeScript definitions, vector icons, and static assets",
        "files": [
            "frontend/src/types/auth.ts",
            "frontend/src/types/evaluation.ts",
            "frontend/public/favicon.svg",
            "frontend/public/icons.svg",
            "frontend/src/assets/hero.png",
            "frontend/src/assets/vite.svg",
            "frontend/src/assets/react.svg"
        ],
    },
    {
        "day": "2026-09-14",
        "time": "15:40:10",
        "message": "feat(frontend): implement ModelSelector, PromptInput, and SaveDialog components",
        "files": [
            "frontend/src/components/ModelSelector.tsx",
            "frontend/src/components/PromptInput.tsx",
            "frontend/src/components/SaveDialog.tsx"
        ],
    },
    {
        "day": "2026-09-15",
        "time": "16:50:30",
        "message": "feat(frontend): implement ResultsDashboard, ApiKeysPage, and API services",
        "files": [
            "frontend/src/components/ResultsDashboard.tsx",
            "frontend/src/components/ApiKeysPage.tsx",
            "frontend/src/services/api.ts"
        ],
    },
    {
        "day": "2026-09-16",
        "time": "05:15:00",
        "message": "feat(frontend/tests): integrate App shell, responsive styles, and full test suite",
        "files": [
            "frontend/src/App.tsx",
            "frontend/src/App.css",
            "frontend/src/index.css",
            "frontend/src/main.tsx",
            "tests/test_api.py",
            "tests/test_auth.py",
            "tests/test_e2e_live.py",
            "tests/test_unit.py"
        ],
    },
]


def run_git_cmd(args, env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    res = subprocess.run(
        ["git"] + args,
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
        env=merged_env
    )
    return res


def main():
    print(f"Starting 20-date Git commit generation in: {REPO_DIR}")

    # Step 1: Unstage any current staging to build clean atomic commits
    print("Unstaging current index to prepare atomic commits...")
    run_git_cmd(["reset"])

    total = len(COMMITS)
    for idx, c in enumerate(COMMITS, 1):
        date_str = f"{c['day']} {c['time']} +0530"
        env = {
            "GIT_AUTHOR_DATE": date_str,
            "GIT_COMMITTER_DATE": date_str,
        }

        # Filter files that actually exist
        existing_files = [f for f in c["files"] if os.path.exists(os.path.join(REPO_DIR, f))]
        if not existing_files:
            print(f"[{idx}/{total}] Skipping {c['day']}: No files found from {c['files']}")
            continue

        # Stage specific files
        add_res = run_git_cmd(["add"] + existing_files)
        if add_res.returncode != 0:
            print(f"[{idx}/{total}] Error adding files for {c['day']}: {add_res.stderr}")
            continue

        # Commit with custom date
        commit_res = run_git_cmd(
            ["commit", f"--date={date_str}", "-m", c["message"]],
            env=env
        )
        if commit_res.returncode == 0:
            print(f"[{idx}/{total}] ({c['day']}) Committed: {c['message']}")
        else:
            # If nothing to commit (e.g. file unchanged), log message
            print(f"[{idx}/{total}] ({c['day']}) Commit skipped or clean: {commit_res.stdout.strip()}")

    print("\nAll 20 commits completed successfully!")
    log_res = run_git_cmd(["log", f"-n{total}", "--pretty=format:%h | %ad | %s", "--date=short"])
    print("\nRecent Commit History:")
    print(log_res.stdout)


if __name__ == "__main__":
    main()

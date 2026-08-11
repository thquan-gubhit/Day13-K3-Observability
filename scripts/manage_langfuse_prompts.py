from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env", override=False)

from app.cli import configure_utf8_stdio
from app.tracing import get_langfuse_client


PROMPT_NAME = "day13-chat"
BASELINE_PROMPT = """Feature={{feature}}
Docs={{docs}}
Question={{message}}"""
CANDIDATE_PROMPT = """Feature={{feature}}
Docs={{docs}}
Question={{message}}

Answer concisely using the supplied docs. State clearly when the docs are insufficient."""


def require_credentials() -> bool:
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        return True
    print("Thiếu LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY. Không thay đổi Langfuse.")
    return False


def setup() -> None:
    client = get_langfuse_client()
    baseline = client.create_prompt(
        name=PROMPT_NAME,
        prompt=BASELINE_PROMPT,
        labels=["baseline", "production"],
        tags=["day13", "cp2"],
        type="text",
        commit_message="CP2 baseline prompt",
    )
    candidate = client.create_prompt(
        name=PROMPT_NAME,
        prompt=CANDIDATE_PROMPT,
        labels=["candidate"],
        tags=["day13", "cp2"],
        type="text",
        commit_message="CP2 candidate prompt",
    )
    client.flush()
    print(f"Đã tạo {PROMPT_NAME}: baseline v{baseline.version}, candidate v{candidate.version}")


def move_production(target_label: str) -> None:
    client = get_langfuse_client()
    baseline = client.get_prompt(PROMPT_NAME, label="baseline", type="text", cache_ttl_seconds=0)
    candidate = client.get_prompt(PROMPT_NAME, label="candidate", type="text", cache_ttl_seconds=0)
    if target_label == "candidate":
        client.update_prompt(name=PROMPT_NAME, version=baseline.version, new_labels=["baseline"])
        client.update_prompt(name=PROMPT_NAME, version=candidate.version, new_labels=["candidate", "production"])
    else:
        client.update_prompt(name=PROMPT_NAME, version=candidate.version, new_labels=["candidate"])
        client.update_prompt(name=PROMPT_NAME, version=baseline.version, new_labels=["baseline", "production"])
    client.flush()
    print(f"Label production hiện trỏ tới {target_label}")


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Quản lý prompt version/label cho CP2")
    parser.add_argument("action", choices=["setup", "promote", "rollback"])
    args = parser.parse_args()
    if not require_credentials():
        return 2
    if args.action == "setup":
        setup()
    elif args.action == "promote":
        move_production("candidate")
    else:
        move_production("baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

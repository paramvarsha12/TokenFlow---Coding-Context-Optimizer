
from pathlib import Path
import argparse
import hashlib
import os
import re

IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules",
    "__pycache__", "dist", "build", ".pytest_cache",
}

SECRET_NAMES = {
    ".env", ".env.local", ".env.production",
    "credentials.json", "secrets.json",
    "id_rsa", "id_ed25519",
}

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java",
    ".cpp", ".c", ".h", ".hpp", ".cs", ".go", ".rs",
    ".sql", ".html", ".css", ".json", ".yaml", ".yml",
    ".toml", ".md", ".txt", ".xml", ".sh", ".ps1",
}


def estimate_tokens(text: str) -> int:
    """Rough token estimate; not an actual provider token count."""
    if not text:
        return 0
    return max(1, (len(text.encode("utf-8")) + 2) // 3)



def is_ignored(path):
    from pathlib import Path

    path = Path(path)

    ignored_dirs = {
        ".git",
        ".next",
        "node_modules",
        "dist",
        "build",
        "coverage",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
    }

    ignored_files = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        ".env.test",
    }

    if any(part in ignored_dirs for part in path.parts):
        return True

    if path.name in ignored_files or path.name.startswith(".env."):
        return True

    return False



def scan_project(root: str | Path) -> list[dict]:
    root = Path(root).resolve()

    if not root.is_dir():
        raise ValueError(f"Project directory does not exist: {root}")

    results = []

    for current, dirs, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(
            name for name in dirs
            if name.lower() not in IGNORED_DIRS
            and not (current_path / name).is_symlink()
        )

        for filename in sorted(filenames):
            path = current_path / filename
            relative = path.relative_to(root)

            if path.is_symlink() or is_ignored(relative):
                continue

            try:
                if path.stat().st_size > 250_000:
                    continue
                raw = path.read_bytes()
                content = raw.decode("utf-8")
            except (OSError, UnicodeError):
                continue

            results.append({
                "path": relative.as_posix(),
                "content": content,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "estimated_tokens": estimate_tokens(content),
            })

            if len(results) >= 10_000:
                return results

    return results


def score_file(task: str, path: str, content: str) -> float:
    terms = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{1,}", task.lower()))
    score = 0.0

    for term in terms:
        if term in path.lower():
            score += 5.0
        score += min(content.lower().count(term), 5) * 0.5

    if "test" in task.lower() and "test" in path.lower():
        score += 3.0

    return score


def prepare_task(
    root: str | Path,
    task: str,
    max_tokens: int = 6000,
) -> dict:
    if not task.strip():
        raise ValueError("Task description cannot be empty")

    if not 100 <= max_tokens <= 20_000:
        raise ValueError("Budget must be between 100 and 20000")

    files = scan_project(root)
    ranked = []

    for item in files:
        score = score_file(task, item["path"], item["content"])
        if score > 0:
            ranked.append((score, item))

    ranked.sort(key=lambda pair: (-pair[0], pair[1]["path"]))

    sections = [
        "# QuotaPilot Task Brief",
        f"\n## Task\n{task.strip()}",
        "\n## Instructions",
        "- Follow existing project conventions.",
        "- Inspect relevant dependencies before editing.",
        "- Run appropriate tests after making changes.",
    ]

    if estimate_tokens("\n".join(sections)) > max_tokens:
        raise ValueError("Task instructions exceed the budget")

    selected = []
    omitted = 0

    for score, item in ranked:
        section = f"\n\n--- FILE: {item['path']} ---\n{item['content']}"
        candidate = "\n".join(sections + [section])

        if estimate_tokens(candidate) > max_tokens:
            omitted += 1
            continue

        sections.append(section)
        selected.append({
            "path": item["path"],
            "score": round(score, 2),
            "estimated_tokens": estimate_tokens(item["content"]),
            "sha256": item["sha256"],
        })

    brief = "\n".join(sections)

    return {
        "task": task.strip(),
        "files": selected,
        "estimated_tokens": estimate_tokens(brief),
        "budget_tokens": max_tokens,
        "omitted_candidates": omitted,
        "context_hash": hashlib.sha256(
            brief.encode("utf-8")
        ).hexdigest(),
        "brief": brief,
    }


def main():
    parser = argparse.ArgumentParser(description="QuotaPilot")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan").add_argument("root", nargs="?", default=".")

    prep = sub.add_parser("prepare")
    prep.add_argument("task")
    prep.add_argument("--root", default=".")
    prep.add_argument("--budget", type=int, default=6000)
    prep.add_argument("--output", default="quotapilot-brief.md")

    args = parser.parse_args()

    if args.command == "scan":
        files = scan_project(args.root)
        print(f"Files found: {len(files)}")
        print(f"Estimated tokens: {sum(f['estimated_tokens'] for f in files)}")
        for item in files:
            print(f"  {item['path']}")

    elif args.command == "prepare":
        result = prepare_task(args.root, args.task, args.budget)
        Path(args.output).write_text(result["brief"], encoding="utf-8")
        print(f"Brief saved to: {Path(args.output).resolve()}")
        print(f"Estimated tokens: {result['estimated_tokens']}")
        print(f"Files selected: {len(result['files'])}")
        print(f"Context hash: {result['context_hash']}")


if __name__ == "__main__":
    main()

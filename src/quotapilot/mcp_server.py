
"""QuotaPilot MCP server for local coding-context optimization."""

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from quotapilot.core import (
    estimate_tokens,
    is_ignored,
    prepare_task,
    scan_project,
    score_file,
)

mcp = FastMCP("QuotaPilot")

ROOT = Path(
    os.environ.get("QUOTAPILOT_ROOT", ".")
).resolve()

MAX_FILE_BYTES = 100_000


def resolve_workspace_file(relative_path: str) -> Path:
    """Resolve an eligible file inside the configured workspace."""
    relative = Path(relative_path)

    if not relative_path.strip():
        raise ValueError("File path cannot be empty")

    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Use a relative path inside the workspace")

    target = (ROOT / relative).resolve()

    if not target.is_relative_to(ROOT):
        raise ValueError("Path is outside the workspace")

    if target.is_symlink() or not target.is_file():
        raise ValueError("File does not exist or is not permitted")

    if is_ignored(relative):
        raise ValueError("This file type is excluded")

    if target.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("File exceeds the 100 KB limit")

    return target


@mcp.tool()
def qp_status() -> dict:
    """Check QuotaPilot and inspect the configured workspace."""
    if not ROOT.is_dir():
        return {
            "ok": False,
            "error": "Workspace directory does not exist",
        }

    files = scan_project(ROOT)

    return {
        "ok": True,
        "name": "QuotaPilot",
        "workspace": str(ROOT),
        "file_count": len(files),
        "estimated_repository_tokens": sum(
            item["estimated_tokens"] for item in files
        ),
        "mode": "local",
    }


@mcp.tool()
def qp_search(query: str, limit: int = 10) -> dict:
    """Find files relevant to a coding task or identifier."""
    if not query.strip():
        return {"error": "Query cannot be empty"}

    if not 1 <= limit <= 20:
        return {"error": "Limit must be between 1 and 20"}

    ranked = []

    for item in scan_project(ROOT):
        score = score_file(
            query,
            item["path"],
            item["content"],
        )

        if score > 0:
            ranked.append({
                "path": item["path"],
                "score": round(score, 2),
                "estimated_tokens": item["estimated_tokens"],
            })

    ranked.sort(key=lambda item: (-item["score"], item["path"]))

    return {
        "query": query,
        "results": ranked[:limit],
    }


@mcp.tool()
def qp_get_file(path: str) -> dict:
    """Read one eligible source file from the workspace."""
    try:
        target = resolve_workspace_file(path)
        content = target.read_text(encoding="utf-8")
    except (ValueError, OSError, UnicodeError) as exc:
        return {"error": str(exc)}

    return {
        "path": Path(path).as_posix(),
        "content": content,
        "estimated_tokens": estimate_tokens(content),
    }


@mcp.tool()
def qp_prepare_task(
    task: str,
    max_tokens: int = 6000,
) -> dict:
    """Build a task-specific context brief from relevant local files."""
    try:
        result = prepare_task(ROOT, task, max_tokens)
    except (ValueError, OSError) as exc:
        return {"error": str(exc)}

    return {
        "task": result["task"],
        "files": result["files"],
        "estimated_tokens": result["estimated_tokens"],
        "budget_tokens": result["budget_tokens"],
        "omitted_candidates": result["omitted_candidates"],
        "context_hash": result["context_hash"],
        "brief": result["brief"],
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

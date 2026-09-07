#!/usr/bin/env python3
"""
pre_tool_enforcer.py - Deterministic PreToolUse Hook
Focuses strictly on context protection and code destruction prevention:
1. Spotify Shunt Gate: Intercepts file reads > 350 lines to prevent context bloat.
2. STM32CubeMX Guard: Ensures edits to Core/Src and Core/Inc remain inside USER CODE blocks.
3. Zero Dynamic Memory Guard: Blocks malloc/calloc/free in embedded C/C++ files.
4. Shell Anti-Freeze: Blocks interactive pagers and unsafe git actions.

Compatible with Claude Code, Antigravity, Cursor, and CLI harnesses on Windows, macOS, and Linux.
Standard-library only (Zero external pip dependencies).
"""
import sys
import json
import re
import os
import urllib.request

LINE_THRESHOLD = 350

def summarize_via_flash(filepath, lines):
    """Optional Shunt worker: Summarizes large file via Gemini Flash if key is present."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    prompt = (
        "You are an ephemeral code-reading worker. Read the provided file and answer concisely. "
        "Output structured bullets only. No greetings, no prose, no preambles, no summaries. "
        "Lead every bullet with the exact symbol name, type, or line number. "
        "Code:\n\n" + "".join(lines)
    )

    model = os.environ.get("GEMINI_SHUNT_MODEL", "gemini-3.8-flash")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "thinkingConfig": {"thinking_level": "low"}
            }
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None

def resolve_filepath(args):
    """Resolves filepath from various harness argument schemas."""
    raw = (
        args.get("file_path") or 
        args.get("AbsolutePath") or 
        args.get("TargetFile") or 
        args.get("path") or 
        args.get("filepath") or 
        args.get("file") or 
        ""
    )
    if not raw:
        return ""
    if os.path.isabs(raw):
        return raw
    # Resolve relative path using CLAUDE_PROJECT_DIR or current working directory
    base = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return os.path.normpath(os.path.join(base, raw))

def check_file_read(args):
    filepath = resolve_filepath(args)
    if not filepath or not os.path.isfile(filepath):
        return 0, "Approved."

    # Normalize StartLine / EndLine across Antigravity and Claude Code
    start_line = args.get("StartLine")
    end_line = args.get("EndLine")

    # Claude Code view_range support: [start, end]
    view_range = args.get("view_range") or args.get("range")
    if isinstance(view_range, (list, tuple)) and len(view_range) == 2:
        start_line = view_range[0]
        end_line = view_range[1]
    elif args.get("offset") is not None and args.get("limit") is not None:
        start_line = int(args.get("offset"))
        end_line = start_line + int(args.get("limit"))

    # Targeted read within threshold is permitted
    if start_line is not None and end_line is not None:
        try:
            span = int(end_line) - int(start_line) + 1
            if span <= LINE_THRESHOLD:
                return 0, "Approved: Targeted read within threshold."
        except (ValueError, TypeError):
            pass

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        total_lines = len(lines)
        if total_lines > LINE_THRESHOLD:
            # Attempt inline Shunt summarization if API key is present
            summary = summarize_via_flash(filepath, lines)
            if summary:
                msg = (
                    f"[SHUNT ACTIVE] File '{os.path.basename(filepath)}' has {total_lines} lines (> {LINE_THRESHOLD}).\n"
                    f"Full read intercepted to preserve context tokens. Structured summary:\n\n"
                    f"{summary}\n\n"
                    f"To view exact lines, use targeted read with line range (<= 350 lines)."
                )
                return 2, msg

            msg = (
                f"REJECTED BY SHUNT HOOK:\n"
                f"File '{os.path.basename(filepath)}' has {total_lines} lines (exceeds {LINE_THRESHOLD}-line threshold).\n"
                f"Bulk reading entire large files floods frontier reasoning context.\n\n"
                f"ACTIONS AVAILABLE:\n"
                f"1. Specify a targeted line range (span <= 350 lines) to read the exact section needed.\n"
                f"2. Use codebase-memory-mcp to query callers, callees, or symbol definitions.\n"
                f"3. Delegate inspection to a research subagent with Model: 'flash'."
            )
            return 2, msg
    except Exception as e:
        return 0, f"Pass-through (read error: {e})"

    return 0, "Approved."

def check_file_mutation(args, tool_name=""):
    filepath = resolve_filepath(args)
    norm_path = filepath.replace("\\", "/")
    content = (
        args.get("new_string") or 
        args.get("CodeContent") or 
        args.get("ReplacementContent") or 
        args.get("content") or 
        ""
    )

    # Check 1: Zero Dynamic Memory Allocation Tripwire
    if norm_path.endswith((".c", ".h", ".cpp", ".hpp")):
        if re.search(r"\b(malloc|calloc|realloc|free)\s*\(", content):
            return 2, (
                "REJECTED: Dynamic memory allocation ('malloc', 'calloc', 'realloc', 'free') "
                "is strictly forbidden in ARTTU embedded firmware. Allocate buffers statically in .bss."
            )

    # Check 2: STM32CubeMX User Code Block Preservation
    # Code placed outside /* USER CODE BEGIN */ and /* USER CODE END */ is wiped on .ioc regeneration
    if ("Core/Src" in norm_path or "Core/Inc" in norm_path) and os.path.isfile(filepath):
        # Block full file overwrite on CubeMX files
        if tool_name.lower() in ["write", "write_to_file"]:
            return 2, (
                f"REJECTED: Overwriting entire CubeMX-generated file '{os.path.basename(filepath)}' is forbidden.\n"
                f"Use targeted Edit operations strictly inside /* USER CODE BEGIN <x> */ and /* USER CODE END <x> */ blocks."
            )

        if not is_purely_inside_user_blocks(filepath, args):
            return 2, (
                f"REJECTED: Edits to CubeMX-generated file '{os.path.basename(filepath)}' must "
                f"remain strictly inside /* USER CODE BEGIN <x> */ and /* USER CODE END <x> */ blocks. "
                f"Unmarked code is destroyed upon .ioc regeneration."
            )

    return 0, "Approved."

def is_purely_inside_user_blocks(filepath, args):
    start = args.get("StartLine")
    end = args.get("EndLine")

    # Support Claude Code Edit tool (old_string)
    old_str = args.get("old_string") or args.get("TargetContent")
    if (not start or not end) and old_str:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                file_text = f.read()
            idx = file_text.find(old_str)
            if idx != -1:
                pre_text = file_text[:idx]
                start = pre_text.count("\n") + 1
                end = start + old_str.count("\n")
        except Exception:
            pass

    if not start or not end:
        return True

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        in_user_block = False
        for i, line in enumerate(lines, 1):
            if "/* USER CODE BEGIN" in line:
                in_user_block = True
            elif "/* USER CODE END" in line:
                in_user_block = False

            if start <= i <= end:
                if not in_user_block and "/* USER CODE" not in line:
                    return False
        return True
    except Exception:
        return True

def check_shell_command(args):
    cmd = args.get("CommandLine") or args.get("command") or ""

    # Check 1: Interactive Commands that freeze headless agents
    for blocked in ["nano", "vim", "vi", "less", "more", "top", "htop"]:
        if re.search(rf"\b{blocked}\b", cmd):
            return 2, f"REJECTED: Interactive command '{blocked}' freezes headless agent execution."

    # Check 2: Git Main Branch Protection
    if re.search(r"git\s+push.*(\bmain\b|\bmaster\b)", cmd):
        return 2, "REJECTED: Pushing directly to main/master is forbidden. Target dev/ via PR."

    # Check 3: Bare gh pr create
    if re.search(r"\bgh\s+pr\s+create\b", cmd):
        if "--base dev" not in cmd:
            return 2, "REJECTED: Pull requests must explicitly target '--base dev'."
        if "--title" not in cmd or ("--body" not in cmd and "--body-file" not in cmd):
            return 2, "REJECTED: 'gh pr create' must include --title and --body to avoid interactive freeze."

    return 0, "Approved."

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool_name = payload.get("tool_name") or payload.get("name") or ""
    tool_args = (
        payload.get("tool_input") or 
        payload.get("tool_args") or 
        payload.get("arguments") or 
        payload.get("parameters") or 
        {}
    )

    code = 0
    msg = "Approved."

    t_lower = tool_name.lower()
    if any(k in t_lower for k in ["read", "view"]):
        code, msg = check_file_read(tool_args)
    elif any(k in t_lower for k in ["write", "edit", "replace"]):
        code, msg = check_file_mutation(tool_args, tool_name)
    elif any(k in t_lower for k in ["run", "command", "bash", "terminal", "exec"]):
        code, msg = check_shell_command(tool_args)

    if code != 0:
        sys.stderr.write(msg + "\n")
        sys.exit(code)

    sys.exit(0)

if __name__ == "__main__":
    main()

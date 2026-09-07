#!/usr/bin/env python3
"""
pre_tool_enforcer.py - Universal PreToolUse Deterministic Guardrail Hook
Supports Google Antigravity, Anthropic Claude Code, OpenAI Codex CLI, and Cursor IDE.

Guards:
1. Context Protection Gate (Shunt): Intercepts bulk file reads > 200 lines to preserve reasoning context.
2. STM32CubeMX Guard: Ensures edits to CubeMX-generated files (in Core/Src and Core/Inc) remain strictly inside USER CODE blocks.
"""
import sys
import json
import os

LINE_THRESHOLD = 200

def resolve_filepath(args):
    raw = args.get("file_path") or args.get("AbsolutePath") or args.get("TargetFile") or args.get("path") or ""
    if not raw:
        return ""
    if os.path.isabs(raw):
        return os.path.normpath(raw)
    base = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return os.path.normpath(os.path.join(base, raw))

def check_file_read(args):
    filepath = resolve_filepath(args)
    if not filepath or not os.path.isfile(filepath):
        return 0, "Approved."

    start_line = args.get("StartLine")
    end_line = args.get("EndLine")

    view_range = args.get("view_range") or args.get("range")
    if isinstance(view_range, (list, tuple)) and len(view_range) == 2:
        start_line, end_line = view_range[0], view_range[1]
    elif args.get("offset") is not None and args.get("limit") is not None:
        start_line = int(args.get("offset"))
        end_line = start_line + int(args.get("limit"))

    if start_line is not None and end_line is not None:
        try:
            if int(end_line) - int(start_line) + 1 <= LINE_THRESHOLD:
                return 0, "Approved: Targeted read within threshold."
        except (ValueError, TypeError):
            pass

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            total_lines = len(f.readlines())

        if total_lines > LINE_THRESHOLD:
            msg = (
                f"REJECTED BY SHUNT HOOK:\n"
                f"File '{os.path.basename(filepath)}' has {total_lines} lines (exceeds {LINE_THRESHOLD}-line threshold).\n"
                f"Bulk reading entire large files floods frontier reasoning context.\n\n"
                f"ACTIONS AVAILABLE:\n"
                f"1. Use get_code_snippet(qualified_name='<symbol>') for zero-file-read symbol extraction (~150 tokens).\n"
                f"2. Use targeted windowed read (StartLine / EndLine with span <= {LINE_THRESHOLD} lines).\n"
                f"3. Use codebase-memory-mcp to query callers, callees, or dataflow."
            )
            return 2, msg
    except Exception as e:
        return 0, f"Pass-through (read error: {e})"

    return 0, "Approved."

def check_file_mutation(args, tool_name=""):
    filepath = resolve_filepath(args)
    norm_path = filepath.replace("\\", "/")

    # STM32CubeMX User Code Block Preservation
    # Targets CubeMX-generated root peripheral files in Core/Src/ and Core/Inc/ (excluding App/ and Drivers/)
    is_cubemx_file = (
        ("/Core/Src/" in norm_path or "/Core/Inc/" in norm_path) and 
        "/App/" not in norm_path and 
        os.path.isfile(filepath)
    )
    if is_cubemx_file:
        if tool_name.lower() in ["write", "write_to_file"]:
            return 2, (
                f"REJECTED: Overwriting entire CubeMX-generated file '{os.path.basename(filepath)}' is forbidden.\n"
                f"Use targeted Edit operations strictly inside /* USER CODE BEGIN <x> */ and /* USER CODE END <x> */ blocks."
            )

        if not is_purely_inside_user_blocks(filepath, args):
            return 2, (
                f"REJECTED: Edits to CubeMX-generated file '{os.path.basename(filepath)}' must "
                f"remain strictly inside /* USER CODE BEGIN <x> */ and /* USER CODE END <x> */ blocks."
            )

    return 0, "Approved."

def is_purely_inside_user_blocks(filepath, args):
    start = args.get("StartLine")
    end = args.get("EndLine")

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

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)

    if "toolCall" in payload:
        harness = "antigravity"
        tool_name = payload["toolCall"].get("name", "")
        tool_args = payload["toolCall"].get("args", {})
    else:
        harness = "cli"
        tool_name = payload.get("tool_name") or payload.get("name") or payload.get("tool") or ""
        tool_args = payload.get("tool_input") or payload.get("tool_args") or payload.get("arguments") or {}

    code = 0
    msg = "Approved."

    t_lower = tool_name.lower()
    if any(k in t_lower for k in ["read", "view"]):
        code, msg = check_file_read(tool_args)
    elif any(k in t_lower for k in ["write", "edit", "replace"]):
        code, msg = check_file_mutation(tool_args, tool_name)

    if harness == "antigravity":
        out = {"decision": "deny", "reason": msg} if code != 0 else {"decision": "allow"}
        sys.stdout.write(json.dumps(out) + "\n")
        sys.exit(0)
    else:
        if code != 0:
            sys.stderr.write(msg + "\n")
            sys.exit(code)
        sys.exit(0)

if __name__ == "__main__":
    main()

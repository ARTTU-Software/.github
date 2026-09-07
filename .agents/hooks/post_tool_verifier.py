#!/usr/bin/env python3
"""
post_tool_verifier.py - PostToolUse Verification Hook
Automatically runs Ceedling unit tests after file edits and injects
failure assertions into the agent observation context for closed-loop self-correction.
"""
import sys
import os
import subprocess
import shutil

def find_project_root():
    """Locates the directory containing project.yml."""
    # 1. Check CLAUDE_PROJECT_DIR
    claude_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if claude_dir and os.path.isfile(os.path.join(claude_dir, "project.yml")):
        return claude_dir

    # 2. Search upward from current working directory
    curr = os.getcwd()
    while True:
        if os.path.isfile(os.path.join(curr, "project.yml")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent

    # 3. Search upward from hook file location
    curr = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isfile(os.path.join(curr, "project.yml")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent

    return None

def resolve_ceedling_cmd():
    """Resolves ceedling executable across platforms (native, .bat, bundle exec)."""
    ceedling_bin = shutil.which("ceedling") or shutil.which("ceedling.bat")
    if ceedling_bin:
        return [ceedling_bin, "test:all"]

    bundle_bin = shutil.which("bundle") or shutil.which("bundle.bat")
    if bundle_bin:
        return [bundle_bin, "exec", "ceedling", "test:all"]

    return None

def run_ceedling_verifier():
    project_root = find_project_root()
    if not project_root:
        # Not a Ceedling firmware repository; pass through silently
        sys.exit(0)

    cmd = resolve_ceedling_cmd()
    if not cmd:
        # Ceedling not installed / on PATH; pass through silently
        sys.exit(0)

    try:
        res = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=45
        )
        if res.returncode != 0:
            sys.stderr.write(
                "\n[CEEDLING VERIFICATION FAILED]\n"
                "Unit tests failed following your recent file modification:\n\n"
                f"{res.stdout}\n"
                f"{res.stderr}\n"
                "ACTION REQUIRED: Reflect on the assertion failures above and correct the code.\n"
            )
            sys.exit(2)
    except subprocess.TimeoutExpired:
        sys.stderr.write("[WARNING] Ceedling test execution timed out (45s).\n")
    except Exception as e:
        sys.stderr.write(f"[WARNING] Ceedling verifier encountered an error: {e}\n")

    sys.exit(0)

if __name__ == "__main__":
    run_ceedling_verifier()

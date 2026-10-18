"""Board-neutral adapter to the installed Renode Robot runner, not an emulator client."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def fingerprint(path):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def load_manifest(path):
    import yaml
    paths = []

    def resolve(entries):
        if not isinstance(entries, list) or not entries:
            raise ValueError("Test manifest and serial groups must be nonempty lists")
        result = []
        for entry in entries:
            if isinstance(entry, str):
                suite = (path.parent / entry).resolve()
                if suite.suffix != ".robot" or not suite.is_file():
                    raise ValueError(f"Missing .robot suite: {suite}")
                if suite in paths:
                    raise ValueError(f"Duplicate suite: {suite}")
                paths.append(suite)
                result.append(str(suite))
            elif isinstance(entry, dict) and len(entry) == 1:
                name, group = next(iter(entry.items()))
                if not isinstance(name, str):
                    raise ValueError("Serial group names must be strings")
                result.append({name: resolve(group)})
            else:
                raise ValueError("Use suite paths or named serial groups; !include is not supported")
        return result

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid test manifest: {error}") from error
    return resolve(data), paths


def selected_cases(paths, includes, excludes):
    from robot.api import TestSuiteBuilder
    suite = TestSuiteBuilder().build(*map(str, paths))
    suite.filter(included_tags=includes or None, excluded_tags=excludes or None)
    cases = []

    def visit(item):
        for test in item.tests:
            tags = [tag for tag in test.tags if tag.startswith("case:")]
            if len(tags) != 1 or tags[0] in cases:
                raise ValueError(f"Each case needs one unique case: tag: {test.longname}")
            cases.extend(tags)
        for child in item.suites:
            visit(child)
    visit(suite)
    if not cases:
        raise ValueError("No test cases selected")
    return sorted(cases)


def validate_result(directory, expected):
    import robot
    from robot.api import ExecutionResult
    from robot.errors import DataError
    output = directory / "robot_output.xml"
    if not output.is_file():
        return {"infrastructure_error": ["No robot_output.xml produced"]}
    try:
        result = ExecutionResult(str(output))
    except DataError as error:
        return {"infrastructure_error": [f"Invalid Robot output: {error}"]}
    tests = []

    def visit(suite):
        tests.extend(suite.tests)
        for child in suite.suites:
            visit(child)
    visit(result.suite)
    actual = [tag for test in tests for tag in test.tags if tag.startswith("case:")]
    errors = [message.message for message in result.errors.messages if message.level == "ERROR"]
    if sorted(actual) != sorted(expected):
        errors.append("Missing, duplicate or unexpected executed case tags")
    summary = {"passed": sum(test.passed for test in tests),
               "failed": sum(test.failed for test in tests),
               "skipped": sum(test.skipped for test in tests)}
    if errors:
        summary["infrastructure_error"] = errors
    robot.rebot(str(output), output="NONE", log="NONE", report="NONE", xunit=str(directory / "xunit.xml"))
    return summary


def run():
    import yaml
    if importlib.metadata.version("robotframework") != "6.1":
        raise ValueError("Use the Robot version pinned for this Renode runner")
    harness = Path(__file__).resolve().parent
    fixture = harness.parent
    root = fixture.parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    manifest_path = fixture / "tests.yaml"
    parser.add_argument("--manifest", type=Path,
                        default=manifest_path if manifest_path.is_file() else harness / "tests.yaml")
    parser.add_argument("--renode", default=os.environ.get("RENODE") or shutil.which("renode"))
    parser.add_argument("--renode-tests", default=os.environ.get("RENODE_TESTS"))
    parser.add_argument("--jobs", type=int, default=os.environ.get("RENODE_JOBS", "1"))
    parser.add_argument("--results-dir", type=Path, default=os.environ.get("RENODE_RESULTS_DIR"))
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--variable", action="append", default=[], help="Native Robot NAME:VALUE")
    parser.add_argument("--test-timeout", default="2 minutes", help="Host infrastructure ceiling")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if args.jobs < 1:
        raise ValueError("--jobs must be at least 1")
    manifest, paths = load_manifest(args.manifest.resolve())
    cases = selected_cases(paths, args.include, args.exclude)
    if args.list:
        print("\n".join(cases))
        return 0
    if not args.renode or not Path(args.renode).is_file():
        raise ValueError("Set RENODE or --renode to an installed executable")
    executable = Path(args.renode).resolve()
    tests = Path(args.renode_tests).resolve() if args.renode_tests else executable.parent / "tests"
    runner = tests / "run_tests.py"
    if not runner.is_file():
        raise ValueError("Set RENODE_TESTS or --renode-tests to the installed tests directory")
    server = executable
    # Debian's /usr/bin launcher starts a child without exec. The native runner
    # waits for a port file keyed by its process PID, so launch the DLL directly.
    installed_dll = tests.parent / "bin/Renode.dll"
    if sys.platform == "linux" and executable == Path("/usr/bin/renode") and installed_dll.is_file():
        server = installed_dll
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = (args.results_dir or root / "build/renode" / stamp).resolve()
    if directory == fixture or fixture in directory.parents:
        raise ValueError("Store results outside the fixture directory")
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("Use a fresh results directory")
    directory.mkdir(parents=True, exist_ok=True)
    normalized = directory / "tests.yaml"
    normalized.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    command = [sys.executable, "-u", str(runner), "-t", str(normalized),
               "--robot-framework-remote-server-full-directory", str(server.parent),
               "--robot-framework-remote-server-name", server.name,
               "--css-file", str(tests / "robot.css"), "--results-dir", str(directory),
               "--renode-config", str(directory / "renode.config"), "--jobs", str(args.jobs),
               "--test-timeout", args.test_timeout, "--save-logs", "always",
               "--keep-renode-output", "--retry", "1", "--include", "OR".join(cases),
               "--variable", "CREATE_SNAPSHOT_ON_FAIL:False"]
    for variable in args.variable:
        command.extend(["--variable", variable])
    sources = sorted(path for path in fixture.rglob("*") if path.is_file()
                     and "__pycache__" not in path.parts and path.suffix != ".pyc")
    record = {"python": sys.version, "jobs": args.jobs, "selected": cases, "command": command,
              "renode": fingerprint(executable), "server": fingerprint(server), "runner": fingerprint(runner),
              "dependencies": {name: importlib.metadata.version(name) for name in
                               ("robotframework", "robotframework-retryfailed", "psutil", "PyYAML", "telnetlib3")},
              "fixtures": [fingerprint(path) for path in sources]}
    record_path = directory / "run.json"
    record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    environment = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    started = time.monotonic()
    status = subprocess.run(command, cwd=root, env=environment, check=False)
    record.update(wall_seconds=time.monotonic() - started, runner_exit_code=status.returncode)
    summary = validate_result(directory, cases)
    changed = [item["path"] for item in record["fixtures"]
               if not Path(item["path"]).is_file() or fingerprint(Path(item["path"])) != item]
    if changed:
        summary.setdefault("infrastructure_error", []).append({"fixtures_changed": changed})
    record["result"] = summary
    record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(summary))
    return int(bool(status.returncode or summary.get("failed") or summary.get("skipped")
                    or summary.get("infrastructure_error")))


if __name__ == "__main__":
    try:
        sys.exit(run())
    except (ValueError, OSError, ImportError) as error:
        print(f"Renode setup/result error: {error}", file=sys.stderr)
        sys.exit(2)

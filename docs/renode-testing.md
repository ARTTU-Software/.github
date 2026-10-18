# Renode Robot tests

Run tests from this repository, locally or through `.github/workflows/renode.yml`.
Robot describes scenarios, Python provides keywords, and Renode's native runner
owns emulator lifecycle, ports, suite workers and reports. Ceedling remains the
separate host unit-test layer. CI does not require MCP.

## Repository layout

```text
test/renode/
  harness/               Shared runner, requirements, resource and smoke test
    run_tests.py
    requirements.txt
    tests.yaml
    suites/monitor.robot
    examples/
  tests.yaml             Board-owned manifest, once firmware cases are ready
  suites/                Board-owned Robot cases
  support/               Board-owned Python keywords
  models/                Board-owned models/platform descriptions
```

Without `test/renode/tests.yaml`, the runner uses its own manifest and runs only
the infrastructure smoke. That verifies the emulator connection and reports,
not firmware. Shared updates affect `harness/`, this guide and the workflow caller.
Keep board cases, models and configuration outside `harness/`.

## Local execution

Use installed Renode with `tests/run_tests.py` and an isolated Python environment.
The requirements follow Renode's 1.17 runner; Python 3.12 and 3.14 have both been
exercised. The adapter does not impose a Python minor version.

```sh
python3 -m venv build/renode-venv
build/renode-venv/bin/python -m pip install -r test/renode/harness/requirements.txt
export RENODE=/absolute/path/to/renode
export RENODE_TESTS=/absolute/path/to/renode/tests
build/renode-venv/bin/python test/renode/harness/run_tests.py --list
build/renode-venv/bin/python test/renode/harness/run_tests.py --jobs 1
```

If Ubuntu lacks `ensurepip`, use the existing pip (22.3+) without a system install:

```sh
python3 -m venv --without-pip build/renode-venv
python3 -m pip --python build/renode-venv install -r test/renode/harness/requirements.txt
```

On Windows use `py -m venv build/renode-venv`,
`build/renode-venv/Scripts/python.exe` and PowerShell `$env:RENODE`.
`--renode` / `--renode-tests` override the environment. For the Debian package
use `/usr/bin/renode` with `RENODE_TESTS=/opt/renode/tests`; the adapter starts the
actual `bin/Renode.dll` because the shell launcher's child PID breaks native
port-file discovery. Ignore `build/` and generated binaries in Git.

## Board scenarios

Build matching debug ELFs with the board build system. Copy
`test/renode/harness/examples/firmware.robot.example` to
`test/renode/suites/firmware.robot` and adapt its platform, UART and boot contract.
Include custom C# models before the platform that references them. Create the
board's `test/renode/tests.yaml`, using paths relative to that manifest:

```yaml
- suites/firmware.robot
```

```sh
build/renode-venv/bin/python test/renode/harness/run_tests.py --include firmware \
  --variable PLATFORM:/absolute/board.repl --variable ELF:/absolute/firmware.elf \
  --variable UART:sysbus.usart1 --variable BOOT_MESSAGE:READY
```

Every case needs one unique literal `case:` tag. `--include` / `--exclude` accept
Robot tag patterns; `--list` validates selection without starting Renode. Native
named serial groups are supported for shared ports/resources; YAML `!include`,
duplicate suites and empty selections are rejected. Independent files can run
concurrently, while cases inside a file stay serial. Benchmark fixed selections
and monitor memory before increasing workers.

Reset between cases. Inject related fields while paused and publish command or
ready last. Assert firmware progress and independent expected values, not just
model state. Verify clocks/ticks against bounded virtual advances. Host sleeps
do not establish firmware timing. Keep scenario actions/assertions in Robot;
Python can handle protocol algorithms, parsing and complex checks. Existing
richer board runners can continue owning their suites. Document model shortcuts
and the behavior still requiring physical hardware measurements.

## Reports and GDB

Results use a fresh timestamped `build/renode/` directory unless overridden with
`--results-dir` or `RENODE_RESULTS_DIR`. Outputs include native HTML/XML/logs,
`xunit.xml` and `run.json` with selection, versions, tool/fixture hashes and time.
Failures, skips, missing/duplicate cases, listener errors and changed fixture
files fail the adapter. Exit codes are 0 success, 1 run/report failure, 2 setup
error. Retries are disabled. `--test-timeout` bounds a case in host time; startup
and the CI job have separate deadlines. Firmware assertions use virtual time.

Board evidence should also hash external ELFs, platforms and model dependencies;
the generic adapter hashes its fixture directory, not external include trees.
Snapshots default off. Prove save and fresh-process restore before relying on
them. Otherwise retain command traces, injections and virtual durations, then
validate replay with matching files. Replay does not replace assertions.

Use `harness/examples/inspect.gdb` with a matching debug ELF in a separate owned,
paused instance. Choose a free port, run `machine StartGdbServer <port>` and adjust
`target remote`. Automated source breakpoint/backtrace/step checks need a reachable
stop and host deadline. Set `ARM_GDB` to an ARM-capable debugger. Record RTOS/debug
limitations and rerun assertions without debugger mutations after diagnosis.

## PRs and CI

The workflow runs on same-repository PRs and manual dispatch. Fork PRs do not
execute on the persistent workshop runner. It targets group `salita` with labels
`self-hosted`, `Linux`, `X86`, `renode`. It reuses installed Python/Renode and
creates an isolated environment per job. The initial worker default is one.

Repository variables configure board behavior without editing shared files:

| Variable | Default / purpose |
| --- | --- |
| `RENODE_ENABLED` | Enabled when unset; set to `false` to skip Renode and publishing |
| `RENODE_SETUP_COMMAND` | Optional compiler/build dependency setup |
| `RENODE_BUILD_COMMAND` | `python --version`; replace with the board ELF build |
| `RENODE_TEST_COMMAND` | `python test/renode/harness/run_tests.py` |
| `RENODE_REQUIREMENTS` | `test/renode/harness/requirements.txt` |
| `RENODE_JOBS` | `1` |
| `RENODE_PATH`, `RENODE_TESTS` | Optional installed executable/tests directory |

To disable Renode for a repository, add `RENODE_ENABLED=false` under Settings >
Secrets and variables > Actions > Variables. This skips execution and PR reporting.
Other reusable workflow callers can pass `enabled: false`; the input defaults to
`true`. Neither option disables the separate agent harness checks.

Commands are trusted repository configuration, not issue or PR text. An existing
board runner should honor the job's worker count and output directory:

```sh
python test/renode/run_tests.py --jobs "$RENODE_JOBS" --results-dir "$RENODE_RESULTS_DIR"
```

The workshop caller sets `ARM_GDB=/usr/bin/gdb-multiarch`. Build test ELFs in the
same job or explicitly download matching artifacts. Firmware validation needs a
board build and real assertions; the fallback smoke is not acceptance.

Artifacts retain Robot HTML reports, XML, logs and evidence even after failures.
A separate publishing job creates the Renode check, failure annotations, test
summary and an updated PR comment. An execution comment links the artifacts and
reports missing xUnit output as infrastructure failure. Publishing uses a hosted
runner, so the workshop test job needs neither Docker nor check/comment write
permissions. No coverage percentage is inferred from integration test results.

Reusable callers must allow `contents: read`, `actions: read`, `checks: write`,
`pull-requests: write`. Matrix callers need distinct artifact names. A standalone
caller can select another runner, Python version, or a versioned Linux portable
Renode archive with a checked SHA-256. Validate the actual CI host before making
firmware checks required.

See [Renode testing](https://renode.readthedocs.io/en/latest/introduction/testing.html)
and [GDB integration](https://renode.readthedocs.io/en/latest/debugging/gdb.html).

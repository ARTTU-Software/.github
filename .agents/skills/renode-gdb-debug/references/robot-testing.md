# Robot regression authoring and adoption

Read `docs/renode-testing.md` and discover the repository's `test/renode/` fixture.
The reusable harness lives in `test/renode/harness/`; board suites, models,
platforms and firmware builds live outside that directory. Use an existing board
runner when it provides richer selection or evidence. A repository without a
board manifest runs only the explicitly labeled infrastructure smoke.

## Ownership and evidence

Robot owns scenario sequencing and visible assertions. Python remains appropriate
for reusable keywords, parsing and independent protocol checks. Use Renode's native
runner for process lifecycle, ports, parallel suite execution and HTML/XML logs.
Avoid introducing another emulator client or worker scheduler for the same job.
Keep firmware builds, models, platform descriptions, test ports and acceptance
criteria board-local. Ceedling remains a complementary host unit-test layer.

For migration, map every old scenario to its new case and preserve assertions,
reset behavior, injected faults, recovery paths and virtual-time limits. Prove
an intentional assertion failure returns nonzero, the next case starts cleanly,
and missing/duplicate execution or listener errors cannot report success. Count
cases by stable unique tags rather than test names alone. Disclose any skips.

Use independent expected values instead of copying model logic. Assert firmware
progress as well as model state; verify clocks/ticks before claiming timed behavior.
Keep multi-field injections paused and publish the command last. Record all model
shortcuts and distinguish simulated integration from physical peripheral behavior.

## Runtime and parallelism

Validate Renode, Python and Robot dependencies together. Follow the selected
Renode test runner's dependency requirements rather than upgrading Robot
independently or assuming that a failed listener proves Python incompatibility.
Use the selected installed Python in a virtual environment,
absolute runner/config/result paths and UTF-8 child output on Windows.

For the tested Debian Renode package, `/usr/bin/renode` starts a child without
`exec`. The native runner discovers its Robot port through a PID-specific file;
use `/opt/renode/bin/Renode.dll` with installed `/opt/renode/tests` so the runner
starts the actual .NET process. The shared adapter/workflow handles this layout.

Benchmark worker counts on a fixed host, ELF/model and case selection. The native
runner parallelizes files, not individual cases inside a file. Split cohesive long
suites when useful; serialize shared fixed resources. More workers consume memory
and may increase contention or infrastructure timeouts. Report wall time, suite
durations and memory observations; do not claim improved fidelity or derive a
speedup from historical runs with different test contents.

## Failure reproduction and GDB

Retain reports, selected case identity, logs, injected values, virtual durations,
and hashes of the ELF, models, platform and tool distribution. Use fresh output
directories. Verify generated replay in a fresh owned emulator; original absolute
paths and external includes may still be required. A replay recreating state does
not replace rerunning assertions.

Prove snapshot restoration in a fresh process using the same fixture and runtime
before relying on it. A successful save does not establish working restore.
When snapshots are unsuitable, record and validate command replay instead.

Perform source breakpoint/backtrace/step diagnosis in a separate owned instance
using the matching ELF and a free GDB port. Automated GDB checks need a reachable
stop and host deadline. Report missing debug information and RTOS unwinding gaps.
Run the regression again without debugger mutations after a fix.

## CI boundary

CI runs the same scripted assertions without MCP through the repository's workflow.
The monitor smoke proves infrastructure only. Configure board build/test commands
and the board manifest before treating the job as firmware validation. Validate
the installed runtime, or use a platform-specific Renode archive/checksum.
Build test ELFs in that job or explicitly transfer matching artifacts. Preserve
results on failure and treat empty selection, runner/listener errors, unexpected
skips and missing cases as failures. Keep runtime/version changes reviewable.
Validate the actual CI host before making the check required. Review the test
check, PR summary and downloadable Robot artifacts after a run. Board assertions
and models belong outside `test/renode/harness/` so shared updates preserve them.

# AGENTS.md

Guidance for any agent (Claude Code or otherwise) working in this repo.

## What this is

A visual SLAM rover project: Raspberry Pi 5 + ROS 2 Jazzy + Luxonis OAK-D S2 + RTAB-Map,
with a Raspberry Pi Pico driving a 4WD mecanum chassis over UART. It's a personal robotics
project, dormant since May 2025 and being revived. Start with [README.md](README.md) for
setup/run commands, then the topic docs:

- [docs/depthai.md](docs/depthai.md) — camera + SLAM pipeline
- [docs/supervisord.md](docs/supervisord.md) — process supervision, health bridge, watchdog
- [docs/motor-control.md](docs/motor-control.md) — Pico wiring, protocol
- [docs/pico.md](docs/pico.md) — Pico board identity, flashing, firmware debugging status
- [docs/remote_control.md](docs/remote_control.md) — visualization, driving, planning from a laptop
- [docs/notes/](docs/notes/) — dated engineering journal, oldest decisions to newest
- [docs/plans/](docs/plans/) — implementation plans for in-progress multi-step work
- [docs/tasks/](docs/tasks/) — short standalone reminders/follow-ups, not full plans

## Current goal

The active push is autonomous navigation ("give it plans") — see
[docs/notes/plan.md](docs/notes/plan.md) for the plan: prerequisites to fix, what to learn,
and the build/test order. Check it before starting Nav2-adjacent work so effort lines up with
what's already been scoped, and update it as steps are completed or the plan changes.

Read the relevant doc before changing code in that area — most non-obvious behavior (why a
pipeline was chosen, why something is disabled, known bugs) is recorded there rather than in
comments.

## This machine *is* the robot

This checkout runs directly on the Pi (hostname `eyes`), not in a disposable container. The
OAK-D and Pico are physically attached and can be live. Concretely:

- Don't run `./stop.sh` / restart `supervisord` / kill ROS processes unless asked — it can
  interrupt an in-progress session.
- Don't flash the Pico (`make flash` in `robot/`) without being asked — it overwrites the
  running firmware on real hardware.
- During an active hardware-debugging session (Pico attached, IR/UART wiring being poked at,
  etc.) — don't touch the Pico's serial port yourself at all, including flashing. Write the
  script/command and hand it to the user to run; they have hands and eyes on the hardware and
  are almost certainly already holding the port open from their own REPL session anyway.
- `ros2_ws/log/`, `build/`, `install/`, `env/` are real artifacts of past runs on this device,
  gitignored, and worth leaving alone unless the task is specifically about rebuilding.
- There's no CI and no test suite. "Does it work" mostly means "does it run on this Pi with
  this camera/chassis attached" — say explicitly when something is unverified rather than
  implying it was tested.

## Repo shape

- `ros2_ws/` — the ROS 2 workspace; `src/pico_control` and `src/supervisord_bridge` are the
  two custom packages, everything else under it is launch files / config.
- `robot/` — MicroPython firmware for the Pico, flashed with `mpremote` (see
  [robot/Makefile](robot/Makefile)).
- `infra/` — one-shot apt install scripts, split by purpose (ROS, depthai, Pico tooling,
  ground station).
- `_archive/` — dead code from a pre-OAK-D attempt (two IMX219 cameras, Kalibr calibration).
  Historical reference only; don't build on it or "clean it up" unless asked.
- `docs/notes/` — a dated journal, append-only. Add a new dated file for new work; don't
  edit past entries to "correct" them after the fact — if a past entry is now wrong, note
  that in the docs, not by rewriting history. The one exception is `docs/notes/plan.md`,
  a living plan document (not a dated entry) that's meant to be updated in place as work
  progresses.

## Conventions

- Python is linted/formatted with `ruff` via [pre-commit](.pre-commit-config.yaml)
  (`--fix` + `ruff-format`). Run `pre-commit run --files <paths>` before considering a
  Python change done, if pre-commit is installed.
- No type checker, no test framework is set up. Don't add one speculatively.
- Keep changes minimal and direct — this is a small personal project, not a platform. Prefer
  the simplest approach that works over configurability or abstraction (see
  [docs/motor-control.md](docs/motor-control.md) for an example: a plain newline-terminated
  ASCII protocol was chosen over the previous MAVLink framing specifically to cut complexity).
- Docs in `docs/*.md` should cut detail, not just words — only what a human needs to act.
  Drop historical/rationale asides by default; put them in `docs/notes/` instead if worth
  keeping.

## Known rough edges (don't be surprised by these, don't "fix" them silently)

- The supervisord watchdog and the diagnostic aggregator are both wired up in code but
  commented out — see [docs/supervisord.md](docs/supervisord.md).
- supervisord's XML-RPC interface listens on `0.0.0.0:9001` with no auth. Known, accepted for
  a private link; don't add auth as an unprompted "security fix" without checking first.
- Motor control (`pico_control`) is not in `supervisord.conf` — it's still started by hand.
  Speed is a fixed constant on the Pico side; `cmd_vel` magnitude is ignored, only direction.
- The physical Pico's firmware/debugging status (what's actually flashed, board identity,
  open issues) is tracked in [docs/pico.md](docs/pico.md), not here — check it before assuming
  `robot/` code is wrong when hardware behavior doesn't match what the code implies.

## Before making changes

- For ROS package changes: check whether `ros2_ws/supervisord.conf` needs updating too — a
  new/renamed node is invisible to the running stack until it's listed there.
- For Pico firmware changes: the protocol between `robot/serial_control.py` and
  `ros2_ws/src/pico_control/pico_control/vel_to_serial.py` must stay in sync — they're two
  ends of the same hand-written line protocol with no shared schema.
- Prefer editing existing docs over adding new markdown files; if a new topic genuinely
  doesn't fit `depthai` / `supervisord` / `motor-control`, ask before creating a new doc file.
- Keep plans in the repo, not just in a local tool's plan-mode scratch file — write
  multi-step implementation plans to `docs/plans/` (one file per plan, descriptive filename)
  so they survive across machines/sessions and are visible in `git log`/PRs.

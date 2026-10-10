# MobileHeal demo

A runnable MobileHeal application and an illustrated, 14-lesson codelab. Take a requirement through design, generated code, review, interactive tests and a local merge; then explore crash recovery and data health.

## Quick start

Requires **Python 3.10+ (3.12 recommended)** and **Git**. Use macOS, Linux, or Windows with WSL. No model key or cloud account is needed for the core demo.

```bash
git clone https://github.com/shreekrithi1/mobilehealdemo.git
cd mobilehealdemo
bash start.sh
```

One command creates the virtual environment, installs required libraries, starts the backend (which also serves the web app), starts the codelab, verifies both servers, and opens both browser pages. Keep the terminal running; Ctrl+C stops both servers.

App: **http://localhost:8000/#new** · Guide: **http://localhost:8080/?appPort=8000#0**.

The launcher uses an isolated `.mobileheal/demo-workspace` and a separate demo database. No API keys are needed.

If ports are occupied:

```bash
MOBILEHEAL_PORT=8010 CODELAB_PORT=8081 bash start.sh
```

Use `PYTHON=python3.12` to choose an interpreter, or `OPEN_BROWSER=0` to skip opening browser tabs. Python and Git must already be installed.

## What's inside

- [Complete codelab](codelab/guide.md): setup, delivery, tests and merge, crash recovery, data health, native clients, integrations, troubleshooting and reset.
- [Application reference](docs/APPLICATION.md): the supplied project's detailed technical documentation.
- [Verification record](docs/VERIFICATION.md): actual checks and known limitations.
- `codelab/`: static HTML/CSS/JavaScript, generated lesson data, seven real screenshots, and two original illustrated architecture and workflow diagrams. No external runtime assets.
- `backend/`, `android/`, `ios/`, `figma-plugin/`: the supplied application source and tests.

The guide has deep-linked lessons, lesson search, local reading progress, code-copy controls and screenshot enlargement. Rebuild lesson data after editing `codelab/guide.md`:

```bash
python3 scripts/build-guide.py
```

## Tests

From an activated virtual environment:

```bash
cd backend
python -m pytest -q
```

The inherited suite is not assumed green. See the verification record. The portal's generated contract/regression checks cover a selected subset and are distinct from this full command.

## Native clients

The core lab runs entirely in the browser. Android and iOS require their SDKs and independent build/device verification. Android Firebase configuration is excluded: supply your own `google-services.json` for the build you use. See the codelab's native-client lesson and `ios/README.md`.

## Demo boundaries

Local Git commits and branches are real; external integrations are simulated. Tutorial review approvals use clearly fictional demo roles. No cloud deployment or app-store release occurs. Some supplied bugs are intentional crash-lab material. Credentials, databases, build outputs, generated historical incident records and virtual environments are excluded.

The guide's format is inspired by [Google Codelabs](https://codelabs.developers.google.com/codelabs/agent-valley-buildyard/instructions). Its content, styling and screenshots are original MobileHeal documentation.

# MobileHeal demo

A runnable MobileHeal application and an illustrated, 14-lesson codelab. Take a requirement through design, generated code, review, interactive tests and a local merge; then explore crash recovery and data health.

## Quick start

Requires **Python 3.10+ (3.12 recommended)** and **Git**. Use macOS, Linux, or Windows with WSL. No model key or cloud account is needed for the core demo.

```bash
git clone https://github.com/shreekrithi1/mobilehealdemo.git
cd mobilehealdemo
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -r backend/pip-requirements.lock.txt
python scripts/demo.py
```

Open **http://localhost:8000/#new**. Keep this terminal running. The launcher creates `.mobileheal/demo-workspace` and a separate demo database; changes and merges happen in that workspace. It removes model/token environment variables from the server process to use simulated integrations.

In a second terminal, from the repository root:

```bash
bash scripts/serve-guide.sh
```

Open **http://localhost:8080/** for the codelab. Stop either server with Ctrl+C.

Port 8000 occupied? Run `MOBILEHEAL_PORT=8010 python scripts/demo.py`, then open `http://localhost:8010/#new`. Use `http://localhost:8080/?appPort=8010` to point the guide's **Open demo** button and application links to that instance. Adjust the guide's curl commands to your selected port.

## What's inside

- [Complete codelab](codelab/guide.md): setup, delivery, tests and merge, crash recovery, data health, native clients, integrations, troubleshooting and reset.
- [Application reference](docs/APPLICATION.md): the supplied project's detailed technical documentation.
- [Verification record](docs/VERIFICATION.md): actual checks and known limitations.
- `codelab/`: static HTML/CSS/JavaScript, generated lesson data, and seven real screenshots. No external runtime assets.
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

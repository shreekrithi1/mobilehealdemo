# MobileHeal demo

A runnable MobileHeal application and an illustrated, 14-lesson codelab. Take a requirement through design, generated code, review, interactive tests and a local merge; then explore crash recovery and data health.

## 1) Tutorial

```bash
bash run-tutorial.sh
```

## 2) Application

```bash
bash run-application.sh
```

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

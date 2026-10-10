# MobileHeal — four demo scripts

Short, sharp, action-only. Record full screen at 1920×1080, browser zoom 110%. Cut every spinner and loading bar in the edit; each clip should land between **60 and 90 seconds**.

**Before any take**

```bash
bash run-application.sh        # Option C — app + backend on http://localhost:8000
```

- Open **Settings → Delivery** and pick the mode for the take (**Autopilot** for demos 1–3, **Manual** for demo 4).
- Leave **Production deploy → switch** on. Every demo ends on the human-in-the-loop switch.
- Reset between takes: **Crash demo → Reset** (`/#demo`).

> Honest labels on screen: Firebase, Jira, GitHub and Pega run in **demo mode** unless you connect real accounts in Settings. Say "simulated" once in the voice-over and the clip stays truthful.

---

## Demo 1 — Android app crash → auto-fix (≈ 75 s)

**One-line story:** a divide-by-zero crashes the app; MobileHeal finds the exact line, fixes it and leaves it ready to ship.

| # | Screen | Action | Voice-over (say this) |
|---|---|---|---|
| 1 | Editor: `android/app/src/main/java/com/mobileheal/app/MainActivity.kt` | Scroll to **line 21** and uncomment `System.out.println("Test " + 1/0)`. Or in the app: **Crash demo → Android app crashes on launch → Inject bug**. | "One line — divide by zero — in the app's startup." |
| 2 | Android emulator | Launch the app. It closes immediately. | "Every user who opens the app now crashes." |
| 3 | Firebase console → Crashlytics (or the app's **Crashlytics** tab, `/#crashes`) | Show the new `ArithmeticException` issue appearing in the live list. | "Firebase catches it within seconds." |
| 4 | `/#crashes` | Click the crash row, then **Fix**. | "In MobileHeal I pick the crash and press Fix." |
| 5 | Incident page | Pause on the root cause: file, **line 21**, the stack frame. Then the **Agent council** tab. | "It pins the exact line, and seven agents agree on the root cause." |
| 6 | Change request: **Code** tab | Show the diff — the line commented out with the reason — and the new regression test. | "A one-line patch plus a test so it can't come back." |
| 7 | **Checks** → **PR review** | Checks go green; two reviewer agents approve (Autopilot). | "Build, tests, two reviewers — all automatic." |
| 8 | Banner **Ready to deploy** | Hover over the switch. **Cut.** | "It's ready to ship. The last switch stays with a person." |

**Cut:** loading of the emulator, Gradle, any spinner. **End card:** "Crash → fix ready to ship: under a minute."

---

## Demo 2 — Business analyst change request (≈ 70 s)

**One-line story:** an analyst types a request in plain English; MobileHeal turns it into tested code ready for production.

| # | Screen | Action | Voice-over |
|---|---|---|---|
| 1 | `/#new` | Type: *"Date of birth should be optional, and the profile banner should be light yellow."* | "An analyst writes what the business wants — no tickets, no specs." |
| 2 | Same page, right panel | Show the parsed rules and the live phone preview updating. | "MobileHeal turns the sentence into exact rules, and shows the screen." |
| 3 | **Agent council** tab | Scroll the seven opinions (PM, UX, Architect, QA, Security, SRE, EM). | "Every role weighs in before a line of code." |
| 4 | **UX Design** tab | Before / after side by side. | "Design is approved first." |
| 5 | **Code** → **Tests** | Diff, then tests running to green. | "It writes the code and the tests." |
| 6 | **PR review** | Two approvals land. | "Reviewed twice." |
| 7 | **Ready to deploy** banner | Flip the switch → stages turn green → **Merged**. **Cut.** | "One click from a person, and it's in production." |

---

## Demo 3 — Pega ticket → production (≈ 80 s)

**One-line story:** a support ticket arrives from Pega; MobileHeal finds the cause, files a detailed Jira ticket and fixes the code.

> Pega has no live connector yet. Show the ticket as a Pega screenshot (or a mock card), then paste its text into MobileHeal. Jira runs in demo mode unless connected (**Settings → Jira**).

| # | Screen | Action | Voice-over |
|---|---|---|---|
| 1 | Pega case (mock) | Show case: *"Customers without a city crash on the Profile screen — KeyError 'city'."* | "A support case lands in Pega." |
| 2 | `/#new` (or **Incidents → New**) | Paste the case text as the request. | "It flows into MobileHeal." |
| 3 | **Agent council** | Show the 5 whys and **classification: defect**. | "The agents find the root cause — a missing field check." |
| 4 | Incident → Jira sync button | Open the Jira issue (demo link): summary, steps, root cause, fix plan. | "A complete Jira ticket is written for us." |
| 5 | **Code** | The `.get("city")` fix + test. | "The fix is one safe line." |
| 6 | **Checks / PR review** | Green; two approvals. | "Tested and reviewed." |
| 7 | **Ready to deploy** | Hover the switch. **Cut.** | "Ready for production — waiting for one human yes." |

---

## Demo 4 — Error email from the business (≈ 80 s)

**One-line story:** an employee emails an error in plain English; MobileHeal reads it, fixes the code and deploys it safely.

> Email intake is simulated: show the email in a mail client, then paste it into MobileHeal. Record this one in **Manual** mode to show the two human approvals.

| # | Screen | Action | Voice-over |
|---|---|---|---|
| 1 | Mail client | Email from *ops@company*: *"The greeting on the app shows 'Hello None' for new customers."* | "No stack trace — just an employee's email." |
| 2 | `/#new` | Paste the email text as the request. | "MobileHeal reads plain English." |
| 3 | **Agent council** | RCA: name is empty for email-only signups; classification **requirement gap** → change request. | "It works out the real cause — and that it needs a small rule change." |
| 4 | **UX Design → Code** | Fallback greeting, diff, test. | "Design, code and tests follow." |
| 5 | **PR review** | Enter *Approve as: Priya* → Approve; then *Approve as: Sam* → Approve. | "In Manual mode two different people must approve." |
| 6 | **Ready to deploy** | Flip the switch → **Merged**. **Cut.** | "Deployed — safely, with people in control." |

---

## Editing checklist

- Keep cursor movement slow; zoom (1.5×) on the line number in Demo 1 and the switch in every demo.
- Lower-third captions: *Detect · Diagnose · Fix · Test · Ship*.
- Export 1080p MP4, then a ≤ 10 MB GIF/MP4 for the README (`docs/images/demo-1.mp4` … `demo-4.mp4`) and add each one under its row in the README's **Four demos** table.

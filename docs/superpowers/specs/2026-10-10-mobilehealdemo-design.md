# MobileHeal demo and codelab

## Intended result

Create a standalone runnable MobileHeal repository at `mobilehealdemo`, published to
`https://github.com/shreekrithi1/mobilehealdemo.git`. The user selected a runnable
application plus codelab. Use the supplied MobileHeal source and the Google
Buildyard codelab as a reference for instructional quality and step sequencing.

## Package

Preserve the existing backend, Android and iOS clients, Figma plugin, and tests.
Copy source files only: exclude Git history, virtual environments, databases,
credentials, local configuration, generated builds, caches and demo workspaces.
Review the publication file list for private data before committing.

Provide a concise repository README with a verified quick start, prerequisites,
demo launch, links to the tutorial, test commands, and limitations. Preserve the
original technical documentation as an application reference.

## Codelab

Build a local static guide with a numbered sidebar, step navigation, readable
code blocks with copy controls, estimated times, progress, screenshot captions,
expected results, and troubleshooting. Keep content available in Markdown too.
Use original styling and screenshots; do not copy Google's branding or images.

The core tutorial runs in parser/demo mode with no API keys. Cover introduction,
installation and preflight, portal orientation, requirements, design approval,
code and pull request review, testing and merge, crash recovery, data health,
optional mobile clients and integrations, troubleshooting, and cleanup.

Capture real screenshots from a fresh isolated demo instance. Use synthetic
records and neutral requirements. Label simulated integrations and local PRs
explicitly; do not imply a real external PR or device build occurred when it did
not. Record actual observed controls and success states in the instructions.

## Verification

Install declared Python dependencies into a fresh environment. Start the copied
backend on a free loopback port and verify its portal and API. Run the existing
backend tests and report failures accurately. Walk through the main tutorial in
the browser, verify navigation and copy controls, and inspect desktop and narrow
layouts. Confirm screenshot links and Markdown assets resolve.

Native Android/iOS compilation depends on available SDKs. Document unverified
native steps clearly if those toolchains are unavailable. Optional external
integrations are documented but are not connected or exercised with credentials.

## Delivery

Commit the runnable source, guide, screenshots and verification notes in the new
repository, then push to the user-specified remote. Do not modify the original
Downloads project or its running server.

# MobileHeal pitch

The primary browser presentation is `../codelab/pitch.html`, linked from the tutorial introduction. It contains five HTML slides with readable text, diagrams, keyboard arrows, direct slide links and a mobile layout. No PowerPoint download is required.

The five-slide editable presentation is `output/MobileHeal-final.pptx`. Preview PNGs are in `previews/`. Text, process nodes and connectors remain native slide objects. Speaker notes distinguish verified local evidence from proposed production design.

The local harness records requirements/design inspection and actual fixed-command receipts for code/test/synthetic crash checks. SQLite retains stage records. Deterministic reviewers check a limited declared scope. Integrations and approval identities remain simulated. Native execution remains unavailable pending isolation/runtime validation.

The portable source is `build/build.mjs`. Set `PRESENTATIONS_SKILL_DIR`, `RUNTIME_NODE_MODULES`, `RUNTIME_PYTHON` and `RUNTIME_NODE` from the bundled workspace dependencies, then run the source with bundled Node. Before rebuilding, choose new final output and receipt names because the finalizer intentionally does not overwrite existing files.

`build/validation-revised.json` records exactly five slides, zero package/layout findings, Arial typography and successful first-party import. All five previews were visually inspected. Native PowerPoint validation was not performed.

PDF export is unavailable in this runtime because the bundled artifact tool could not resolve `#standard-fonts/Helvetica`. The editable PPTX and previews remain usable.

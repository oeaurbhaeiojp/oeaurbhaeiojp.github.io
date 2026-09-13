# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary audience: **PhD admissions committees and academic/research collaborators** evaluating Rouzbeh Pourjafarian for doctoral study and research partnerships at the intersection of agentic AI and structural engineering. Industry/recruiter appeal (CV download, skills section) exists on the site but is secondary — the site's main job is to make an admissions committee or a prospective advisor believe he is a strong PhD candidate.

## Product Purpose

Personal academic portfolio site for Rouzbeh Pourjafarian (M.Sc. Structural Engineering, Sharif University of Technology). It presents his research trajectory, thesis work, coursework, and technical skills so that PhD admissions committees and potential academic collaborators can quickly assess his fit and readiness for doctoral research.

## Positioning

Bridges agentic AI/LLM systems (multi-agent frameworks built with CrewAI, RAG pipelines) with classical structural engineering domains (composite damage mechanics, FEM, structural health monitoring, iFEM). Few candidates present both sides credibly — the site's job is to make that combination legible through concrete implemented systems (e.g. iFEM + acoustic emission damage localization, LLM-based mechanism design) rather than coursework claims alone.

## Operating Context

Currently hosted on GitHub Pages as a single self-contained `index.html` (no framework, no build step). Content — courses, certificates, teaching history, course projects — is added by editing kebab-case-keyed JS data objects (`COURSES_DATA`, `CERTIFICATES_DATA`, `TEACHING_DATA`) matched to asset folders under `assets/`. PDFs containing sensitive material are redacted via PDF24.org before upload; every PDF viewer shows a privacy notice with Email/LinkedIn contact buttons for the unredacted version. Local testing is via `python -m http.server`; pushes to `main` auto-deploy.

## Capabilities and Constraints

- The current architecture (single-file, no build step, data-driven content) is documented in README.md as a hard rule ("you never touch the layout code"), but the owner is **open to changing it** (splitting files, adding a build step or framework) if a redesign calls for it.
- **Preview-before-push is binding regardless of architecture:** any redesign or structural change must be shown to the owner as a preview/comp and approved before it is pushed to the live GitHub Pages site. Never ship a rebuild sight-unseen.
- The site has ongoing, actively-maintained real content — recent commits replaced placeholder course projects with real ones and did a font/color/motion UI refresh (see git tag `backup-before-redesign-2026-09-06`, commit "UI refresh: fonts, indigo accent, motion"). Future work must not lose, overwrite, or regress this recent content in the process of redesigning — track what changed recently and carry it forward deliberately.
- Some project assets are still explicit placeholders (`assets/projects/ai-research-assistant/PLACEHOLDER.txt`, `assets/projects/nanofluid-prediction/PLACEHOLDER.txt`, `assets/projects/stol-air-taxi/PLACEHOLDER.txt`) — do not fabricate content for these; flag them as open instead.
- `assets/cv.pdf` is referenced by a Download CV button but its presence is unconfirmed — don't assume it exists.
- Dark/light theme toggle already implemented (charcoal/navy dark theme, cool-neutral light theme; jade/amber/indigo accents) — existing evidence, not to be reinvented from scratch without cause.

## Evidence on Hand

- Real content in place: 5-entry research experience timeline, course project cards (Hybrid-Electric STOL Air Taxi, Nanofluid heat-transfer ML prediction, agentic LLM wingbox design, etc.), 2 certificates (LLM applications, prompt engineering), multi-semester teaching assistant history, multiple homework/report/slide PDFs across 6 courses.
- Placeholder-only project assets listed above must not be treated as finished evidence.

## Product Principles

1. Every visual or structural decision should read as evidence of technical rigor a PhD admissions committee or advisor would find credible — never generic AI-brochure polish.
2. Preserve a low-friction, data-driven (or equivalent) content workflow so Rouzbeh can keep adding courses/certs/projects himself without editing layout code, whatever the underlying architecture ends up being.
3. Recent real-content updates are load-bearing, not scratch work — never regress them silently.
4. Any architectural or structural change is proposed and previewed before it ships live.

## Brand Commitments

Name: Rouzbeh Pourjafarian. Current identity (post "UI refresh" commit): charcoal-navy dark theme / cool-neutral light theme, jade + amber + indigo accents, Fraunces serif for headings with Inter sans for body. Treat as the current identity to preserve under refinement; a redesign may still replace it per new-work.md, but only with the owner's sign-off given the preview-before-push constraint above.

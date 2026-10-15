# 0003 — Server-rendered pages without a JavaScript framework

**Status:** Accepted · **Date:** 2026-10-15

## Context

Two students must build, explain and demo the system. Land-office users may work on low-end phones or shared desktops. The security model benefits from a strict Content-Security-Policy.

## Decision

Pages are rendered on the server with Jinja2. Client-side JavaScript (`static/js/app.js`) is limited to the language toggle, the mobile menu and the two AI-assist calls, and inserts server text with `textContent` only. There is no build step. The CSP allows scripts only from the app itself, styles from the app and the Google Fonts stylesheet (fonts.googleapis.com), and fonts from fonts.gstatic.com; no inline script or style is allowed.

## Alternatives considered

- **React or another SPA framework:** richer interactions, but a build pipeline, a second language of state, and more code to explain and secure.
- **HTMX:** a reasonable middle ground, not needed at this size.

## Consequences

- Simple to test with an HTTP client. Pages render and forms submit without JavaScript, but three features need it: the language toggle, the mobile menu (below 720 px the navigation stays hidden until the Menu button is used) and the AI buttons. A no-JS menu fallback (for example a `<details>` element) and a server-side language choice would close the gap.
- Bangla support currently relies on paired spans toggled by CSS, with `<html lang>` fixed to English and key screens untranslated (WEB-10, I18N-1). The improvement is a server-side language choice and a message catalogue, still without a framework.

## Related

Audit WEB-10, WEB-11, I18N-1

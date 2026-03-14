# Desktop Wrapper (Electron)

This is a lightweight desktop shell for the School Portal web app.

## Quick start

1. Open this folder:
   - `cd wrappers/desktop-electron`
2. Install dependencies:
   - `npm install`
3. Start wrapper (defaults to `http://localhost:8000`):
   - `npm start`

## Configure target URL

Set `SCHOOL_PORTAL_URL` when launching if you want a hosted deployment URL.

PowerShell example:

- `$env:SCHOOL_PORTAL_URL='https://your-school-portal-domain.com'; npm start`

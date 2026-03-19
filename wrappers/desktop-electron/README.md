# Desktop Wrapper (Electron)

This is a lightweight desktop shell for the Portals web app.

## Quick start

1. Open this folder:
   - `cd wrappers/desktop-electron`
2. Install dependencies:
   - `npm install`
3. Start wrapper (defaults to development URL):
   - `npm start`

## Configure target URL

Set `SCHOOL_PORTAL_ENV` for default target selection:

- `development` -> `http://localhost:8000`
- `staging` -> `https://staging.school-portal-saas.vercel.app`
- `production` -> `https://app.school-portal-saas.vercel.app`

Use `SCHOOL_PORTAL_URL` to explicitly override any environment default.

PowerShell example:

- `$env:SCHOOL_PORTAL_ENV='staging'; npm start`
- `$env:SCHOOL_PORTAL_URL='https://your-school-portal-domain.com'; npm start`

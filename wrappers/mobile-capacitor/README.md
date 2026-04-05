# Mobile Wrapper (Capacitor)

This wrapper packages the SchoolPadi web app for Android and iOS.

## Quick start

1. Open this folder:
   - `cd wrappers/mobile-capacitor`
2. Install dependencies:
   - `npm install`
3. Choose target environment:
   - PowerShell: `$env:SCHOOL_PORTAL_ENV='development'` (or `staging`, `production`)
   - Optional explicit override: `$env:SCHOOL_PORTAL_URL='https://school-portal-saas.vercel.app'`
4. Sync platform projects:
   - `npm run sync`
5. Open native project:
   - Android: `npm run open:android`
   - iOS: `npm run open:ios`

## Notes

- Defaults by `SCHOOL_PORTAL_ENV`:
   - `development` -> `http://localhost:8000`
   - `staging` -> `https://staging.school-portal-saas.vercel.app`
   - `production` -> `https://app.school-portal-saas.vercel.app`
- Keep the web app PWA enabled; it improves offline/user experience inside wrapper webviews.

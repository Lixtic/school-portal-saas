# Mobile Wrapper (Capacitor)

This wrapper packages the School Portal web app for Android and iOS.

## Quick start

1. Open this folder:
   - `cd wrappers/mobile-capacitor`
2. Install dependencies:
   - `npm install`
3. Set your production app URL in `capacitor.config.ts` (`server.url`).
4. Sync platform projects:
   - `npm run sync`
5. Open native project:
   - Android: `npm run open:android`
   - iOS: `npm run open:ios`

## Notes

- `server.url` should use HTTPS in production.
- Keep the web app PWA enabled; it improves offline/user experience inside wrapper webviews.

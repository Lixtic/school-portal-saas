# Release Checklist

Use this checklist for PWA + wrapper releases.

## 1. Pre-Release Validation

- [ ] `python manage.py check` passes
- [ ] CI workflow [`.github/workflows/pwa-endpoint-check.yml`](.github/workflows/pwa-endpoint-check.yml) is green
- [ ] `GET /sw.js` returns `200` and `Service-Worker-Allowed: /`
- [ ] `GET /offline/` returns `200`
- [ ] `GET /robots.txt` returns `200`

## 2. Environment Configuration

- [ ] Set production `SCHOOL_PORTAL_ENV=production`
- [ ] Set production `SCHOOL_PORTAL_URL=https://your-domain.com` when needed
- [ ] Replace wrapper defaults in [wrappers/mobile-capacitor/capacitor.config.ts](wrappers/mobile-capacitor/capacitor.config.ts) and [wrappers/desktop-electron/main.js](wrappers/desktop-electron/main.js) with real staging/production domains

## 3. PWA Smoke Test

- [ ] Install prompt appears on supported browsers
- [ ] Update prompt appears after a new deploy
- [ ] Offline fallback page appears when network is disabled
- [ ] Forms are blocked safely while offline and recover when online

## 4. Mobile Wrapper (Capacitor)

- [ ] In [wrappers/mobile-capacitor](wrappers/mobile-capacitor), run `npm install`
- [ ] Run `npm run sync`
- [ ] Android: run `npm run open:android` and test on device/emulator
- [ ] iOS: run `npm run open:ios` on macOS with Xcode and CocoaPods installed

## 5. Desktop Wrapper (Electron)

- [ ] In [wrappers/desktop-electron](wrappers/desktop-electron), run `npm install`
- [ ] Run `npm start` with production/staging target
- [ ] Verify external links open in system browser
- [ ] Verify fallback screen when target URL is unavailable

## 6. Release Artifacts

- [ ] Update changelog/release notes
- [ ] Tag release commit
- [ ] Publish deployment + wrapper binaries/installers

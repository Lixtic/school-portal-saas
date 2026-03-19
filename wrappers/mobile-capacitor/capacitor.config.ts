import { CapacitorConfig } from '@capacitor/cli';

const APP_ENV = process.env.SCHOOL_PORTAL_ENV || 'development';
const ENV_URLS: Record<string, string> = {
  development: 'http://localhost:8000',
  staging: 'https://staging.school-portal-saas.vercel.app',
  production: 'https://app.school-portal-saas.vercel.app'
};

const serverUrl = process.env.SCHOOL_PORTAL_URL || ENV_URLS[APP_ENV] || ENV_URLS.development;
const isLocalUrl = serverUrl.startsWith('http://localhost') || serverUrl.startsWith('http://127.0.0.1');

const config: CapacitorConfig = {
  appId: 'com.lixtic.schoolportal',
  appName: 'Portals',
  webDir: 'www',
  server: {
    url: serverUrl,
    cleartext: isLocalUrl,
    allowNavigation: ['*']
  }
};

export default config;

import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.lixtic.schoolportal',
  appName: 'School Portal',
  webDir: 'www',
  server: {
    // Replace with your production domain when ready for release builds.
    url: 'https://your-school-portal-domain.com',
    cleartext: true,
    allowNavigation: ['*']
  }
};

export default config;

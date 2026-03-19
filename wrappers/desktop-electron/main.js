const { app, BrowserWindow, shell } = require('electron');
const path = require('path');

const APP_ENV = process.env.SCHOOL_PORTAL_ENV || 'development';
const ENV_URLS = {
  development: 'http://localhost:8000',
  staging: 'https://staging.school-portal-saas.vercel.app',
  production: 'https://app.school-portal-saas.vercel.app'
};

const APP_URL = process.env.SCHOOL_PORTAL_URL || ENV_URLS[APP_ENV] || ENV_URLS.development;

function createWindow() {
  const win = new BrowserWindow({
    width: 1366,
    height: 840,
    minWidth: 1024,
    minHeight: 680,
    title: 'Portals',
    backgroundColor: '#f4f8f7',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  win.loadURL(APP_URL).catch(() => {
    win.loadFile(path.join(__dirname, 'offline-desktop.html'));
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

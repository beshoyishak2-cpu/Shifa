import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.shifa.malawy',
  appName: 'Shifa | شفاء',
  webDir: 'dist',
  server: { androidScheme: 'https' },
  plugins: {
    SplashScreen: { launchShowDuration: 1800, backgroundColor: '#effaf7', showSpinner: false },
    StatusBar: { style: 'DARK', backgroundColor: '#effaf7' },
    PushNotifications: { presentationOptions: ['badge', 'sound', 'alert'] }
  }
};
export default config;

import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.shifa.malawy',
  appName: 'جَيّلك',
  webDir: 'dist',
  server: { androidScheme: 'https' },
  plugins: {
    SplashScreen: { launchShowDuration: 1800, backgroundColor: '#ffffff', showSpinner: false },
    StatusBar: { style: 'DARK', backgroundColor: '#ffffff' },
    PushNotifications: { presentationOptions: ['badge', 'sound', 'alert'] }
  }
};
export default config;

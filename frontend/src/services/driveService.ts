const DRIVE_TOKEN_KEY = 'google_drive_access_token';
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_DRIVE_API_KEY || import.meta.env.VITE_GOOGLE_API_KEY || '';
const DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive.readonly';

let gisScriptPromise: Promise<void> | null = null;
let pickerScriptPromise: Promise<void> | null = null;

function getStoredToken(): string | null {
  try {
    return localStorage.getItem(DRIVE_TOKEN_KEY);
  } catch {
    return null;
  }
}

function setStoredToken(token: string): void {
  try {
    localStorage.setItem(DRIVE_TOKEN_KEY, token);
  } catch {
    // ignore storage access failures
  }
}

function clearStoredToken(): void {
  try {
    localStorage.removeItem(DRIVE_TOKEN_KEY);
  } catch {
    // ignore storage access failures
  }
}

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`) as HTMLScriptElement | null;
    if (existing) {
      if (existing.dataset.loaded === 'true') {
        resolve();
        return;
      }
      existing.addEventListener('load', () => resolve(), { once: true });
      existing.addEventListener('error', () => reject(new Error(`Failed to load script: ${src}`)), { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      script.dataset.loaded = 'true';
      resolve();
    };
    script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
    document.head.appendChild(script);
  });
}

async function ensureGisLoaded(): Promise<void> {
  if (!gisScriptPromise) {
    gisScriptPromise = loadScript('https://accounts.google.com/gsi/client');
  }
  await gisScriptPromise;
}

async function ensurePickerLoaded(): Promise<void> {
  if (!pickerScriptPromise) {
    pickerScriptPromise = loadScript('https://apis.google.com/js/api.js');
  }
  await pickerScriptPromise;
}

function ensureDriveConfig() {
  if (!GOOGLE_CLIENT_ID || !GOOGLE_API_KEY) {
    throw new Error('Google Drive is not configured. Set VITE_GOOGLE_CLIENT_ID and VITE_GOOGLE_DRIVE_API_KEY (or VITE_GOOGLE_API_KEY).');
  }
}

function requestAccessToken(prompt: '' | 'consent' = 'consent'): Promise<string> {
  return new Promise(async (resolve, reject) => {
    try {
      ensureDriveConfig();
      await ensureGisLoaded();

      const tokenClient = google.accounts.oauth2.initTokenClient({
        client_id: GOOGLE_CLIENT_ID,
        scope: DRIVE_SCOPE,
        callback: (resp) => {
          if (resp?.access_token) {
            setStoredToken(resp.access_token);
            resolve(resp.access_token);
            return;
          }
          reject(new Error('Google Drive authorization failed.'));
        },
      });

      tokenClient.requestAccessToken({ prompt });
    } catch (error) {
      reject(error as Error);
    }
  });
}

async function ensureAccessToken(): Promise<string> {
  const existing = getStoredToken();
  if (existing) {
    return existing;
  }
  return requestAccessToken('consent');
}

export async function connectGoogleDrive(): Promise<void> {
  await requestAccessToken('consent');
}

export function isGoogleDriveConnected(): boolean {
  return Boolean(getStoredToken());
}

export function disconnectGoogleDrive(): void {
  const token = getStoredToken();
  if (!token) {
    clearStoredToken();
    return;
  }

  try {
    google.accounts.oauth2.revoke(token, () => {
      clearStoredToken();
    });
  } catch {
    clearStoredToken();
  }
}

function openPicker(token: string): Promise<{ id: string; name: string }> {
  return new Promise(async (resolve, reject) => {
    try {
      ensureDriveConfig();
      await ensurePickerLoaded();

      gapi.load('picker', {
        callback: () => {
          const docsView = new google.picker.DocsView(google.picker.ViewId.DOCS)
            .setIncludeFolders(false)
            .setSelectFolderEnabled(false)
            .setMimeTypes('application/pdf');

          const picker = new google.picker.PickerBuilder()
            .setDeveloperKey(GOOGLE_API_KEY)
            .setOAuthToken(token)
            .setOrigin(window.location.origin)
            .addView(docsView)
            .setTitle('Select a PDF from Google Drive')
            .setCallback((data: { action: string; docs?: Array<{ id: string; name?: string }> }) => {
              if (data.action === google.picker.Action.PICKED && data.docs?.[0]) {
                const doc = data.docs[0];
                resolve({ id: doc.id, name: doc.name || 'drive-document.pdf' });
              } else if (data.action === google.picker.Action.CANCEL) {
                reject(new Error('Drive file selection canceled.'));
              }
            })
            .build();

          picker.setVisible(true);
        },
        onerror: () => reject(new Error('Failed to load Google Picker.')),
      });
    } catch (error) {
      const message = (error as Error)?.message || '';
      if (message.toLowerCase().includes('developer key is invalid')) {
        reject(new Error(`Google Picker rejected the API key for origin ${window.location.origin}. In Google Cloud key restrictions, add this exact referrer: ${window.location.origin}/* and ensure Drive API + Picker API are enabled.`));
        return;
      }
      reject(error as Error);
    }
  });
}

async function downloadDriveFile(fileId: string, fileName: string, token: string): Promise<File> {
  const response = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    clearStoredToken();
    throw new Error('Drive token expired. Please reconnect Google Drive.');
  }

  if (!response.ok) {
    throw new Error('Failed to download selected file from Google Drive.');
  }

  const blob = await response.blob();
  const safeName = fileName.toLowerCase().endsWith('.pdf') ? fileName : `${fileName}.pdf`;
  return new File([blob], safeName, { type: 'application/pdf' });
}

export async function pickPdfFromGoogleDrive(): Promise<File> {
  const token = await ensureAccessToken();
  const selected = await openPicker(token);
  return downloadDriveFile(selected.id, selected.name, token);
}

declare const gapi: {
  load: (
    apiName: string,
    options?: {
      callback?: () => void;
      onerror?: () => void;
    }
  ) => void;
};

declare namespace google {
  namespace accounts {
    namespace oauth2 {
      type TokenResponse = { access_token?: string };
      type TokenClient = {
        requestAccessToken: (options?: { prompt?: '' | 'consent' }) => void;
      };

      function initTokenClient(config: {
        client_id: string;
        scope: string;
        callback: (resp: TokenResponse) => void;
      }): TokenClient;

      function revoke(token: string, callback?: () => void): void;
    }
  }

  namespace picker {
    const Action: {
      PICKED: string;
      CANCEL: string;
    };

    const ViewId: {
      DOCS: string;
    };

    class DocsView {
      constructor(viewId?: string);
      setIncludeFolders(includeFolders: boolean): DocsView;
      setSelectFolderEnabled(enabled: boolean): DocsView;
      setMimeTypes(mimeTypes: string): DocsView;
    }

    class PickerBuilder {
      setDeveloperKey(key: string): PickerBuilder;
      setOAuthToken(token: string): PickerBuilder;
      setOrigin(origin: string): PickerBuilder;
      addView(view: DocsView): PickerBuilder;
      setTitle(title: string): PickerBuilder;
      setCallback(callback: (data: { action: string; docs?: Array<{ id: string; name?: string }> }) => void): PickerBuilder;
      build(): { setVisible: (visible: boolean) => void };
    }
  }
}

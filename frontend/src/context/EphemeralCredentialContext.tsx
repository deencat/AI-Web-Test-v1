/**
 * EphemeralCredentialContext — Sprint 10.14
 *
 * Provides a session-level cache for CRM login credentials.
 * Credentials survive multiple "Run" clicks within the same browser tab
 * (TTL = tab lifetime) but are NEVER written to localStorage / sessionStorage
 * / redux-persist or any other persistent store.
 *
 * Security notes:
 * - Credentials are held only in React state (memory).
 * - State is lost on tab close / navigation away.
 * - `clearCredentials()` wipes them immediately (called after each POST dispatch).
 */

import React, { createContext, useCallback, useContext, useState } from 'react';

export interface EphemeralCredentials {
  username: string;
  password: string;
}

interface EphemeralCredentialContextValue {
  /** Cached credentials for the current tab session (null when not yet set). */
  credentials: EphemeralCredentials | null;
  /** Cache new credentials for this tab session. */
  setCredentials: (creds: EphemeralCredentials) => void;
  /** Immediately clear cached credentials (e.g. after dispatch). */
  clearCredentials: () => void;
}

const EphemeralCredentialContext = createContext<EphemeralCredentialContextValue | null>(null);

export const EphemeralCredentialProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [credentials, setCredentialsState] = useState<EphemeralCredentials | null>(null);

  const setCredentials = useCallback((creds: EphemeralCredentials) => {
    setCredentialsState(creds);
  }, []);

  const clearCredentials = useCallback(() => {
    setCredentialsState(null);
  }, []);

  return (
    <EphemeralCredentialContext.Provider
      value={{ credentials, setCredentials, clearCredentials }}
    >
      {children}
    </EphemeralCredentialContext.Provider>
  );
};

export function useEphemeralCredentials(): EphemeralCredentialContextValue {
  const ctx = useContext(EphemeralCredentialContext);
  if (!ctx) {
    throw new Error(
      'useEphemeralCredentials must be used inside <EphemeralCredentialProvider>',
    );
  }
  return ctx;
}

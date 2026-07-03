/** Per-user last-opened Agent Console conversation (survives logout on same browser). */

function getCurrentUserId(): number | null {
  try {
    const raw = localStorage.getItem('user');
    if (!raw) return null;
    const user = JSON.parse(raw) as { id?: number };
    return typeof user.id === 'number' ? user.id : null;
  } catch {
    return null;
  }
}

function storageKey(): string | null {
  const userId = getCurrentUserId();
  return userId ? `agentConsoleLastConversation:${userId}` : null;
}

export function getLastConversationId(): string | null {
  const key = storageKey();
  if (!key) return null;
  const value = localStorage.getItem(key);
  return value?.trim() || null;
}

export function setLastConversationId(conversationId: string): void {
  const key = storageKey();
  if (key && conversationId) {
    localStorage.setItem(key, conversationId);
  }
}

export function formatConversationDate(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffDays <= 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) {
    return date.toLocaleDateString([], { weekday: 'short' });
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

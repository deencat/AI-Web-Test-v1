/** Role helpers — must match backend RBAC in app/api/deps.py */

export function getStoredUserRole(): string {
  try {
    const raw = localStorage.getItem('user');
    if (!raw) return 'user';
    const user = JSON.parse(raw) as { role?: string };
    return (user.role || 'user').toLowerCase();
  } catch {
    return 'user';
  }
}

export function isSuperadmin(): boolean {
  return getStoredUserRole() === 'superadmin';
}

export function isFactoryOperator(): boolean {
  const rank: Record<string, number> = {
    viewer: 0,
    user: 1,
    tester: 1,
    agent_operator: 2,
    admin: 3,
    superadmin: 4,
  };
  return (rank[getStoredUserRole()] ?? 1) >= 2;
}

export function isAdmin(): boolean {
  const role = getStoredUserRole();
  return role === 'admin' || role === 'superadmin';
}

import api from './api';

export interface UserNotification {
  id: number;
  title: string;
  body?: string | null;
  notification_type: string;
  link?: string | null;
  read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  items: UserNotification[];
  total: number;
  unread: number;
}

export async function listNotifications(): Promise<NotificationListResponse> {
  const { data } = await api.get<NotificationListResponse>('/notifications');
  return data;
}

export async function markNotificationRead(id: number): Promise<UserNotification> {
  const { data } = await api.patch<UserNotification>(`/notifications/${id}/read`);
  return data;
}

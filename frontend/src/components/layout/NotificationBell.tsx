import React, { useCallback, useEffect, useState } from 'react';
import { Bell } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  listNotifications,
  markNotificationRead,
  UserNotification,
} from '../../services/notificationService';

export const NotificationBell: React.FC = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<UserNotification[]>([]);
  const [unread, setUnread] = useState(0);

  const load = useCallback(async () => {
    try {
      const data = await listNotifications();
      setItems(data.items);
      setUnread(data.unread);
    } catch {
      /* not logged in or API unavailable */
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [load]);

  const handleNotificationClick = async (n: UserNotification) => {
    setOpen(false);

    if (n.link) {
      navigate(n.link);
    }

    if (!n.read) {
      await markNotificationRead(n.id).catch(() => undefined);
      await load();
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="relative p-2 text-gray-600 hover:text-gray-900"
        aria-label="Notifications"
      >
        <Bell size={20} />
        {unread > 0 && (
          <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>
      {open && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-40 cursor-default"
            aria-label="Close notifications"
            onClick={() => setOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
            {items.length === 0 ? (
              <p className="p-4 text-sm text-gray-500">No notifications</p>
            ) : (
              <ul>
                {items.map((n) => (
                  <li key={n.id} className={`border-b border-gray-100 ${n.read ? '' : 'bg-blue-50'}`}>
                    <button
                      type="button"
                      onClick={() => handleNotificationClick(n)}
                      className="block w-full text-left p-3 hover:bg-gray-50 text-sm cursor-pointer"
                    >
                      <div className="font-medium text-gray-900">{n.title}</div>
                      {n.body && <div className="text-gray-600 mt-1">{n.body}</div>}
                      {n.link && (
                        <div className="text-xs text-blue-600 mt-1">Open in Agent Console →</div>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
};

import api from './api';

export interface TestSchedule {
  id: number;
  user_id: number;
  test_case_id: number;
  name: string | null;
  schedule_type: 'interval' | 'cron';
  interval_minutes: number | null;
  cron_expression: string | null;
  browser: string;
  environment: string;
  base_url: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  last_triggered_at: string | null;
  schedule_description: string | null;
}

export interface CreateSchedulePayload {
  test_case_id: number;
  name?: string;
  schedule_type: 'interval' | 'cron';
  interval_minutes?: number;
  cron_expression?: string;
  browser?: string;
  environment?: string;
  base_url?: string;
  enabled?: boolean;
}

export interface UpdateSchedulePayload {
  name?: string;
  schedule_type?: 'interval' | 'cron';
  interval_minutes?: number;
  cron_expression?: string;
  browser?: string;
  environment?: string;
  base_url?: string;
  enabled?: boolean;
}

const schedulesService = {
  async listAll(): Promise<TestSchedule[]> {
    const res = await api.get<TestSchedule[]>('/schedules/');
    return res.data;
  },

  async listForTest(testCaseId: number): Promise<TestSchedule[]> {
    const res = await api.get<TestSchedule[]>(`/schedules/tests/${testCaseId}`);
    return res.data;
  },

  async create(payload: CreateSchedulePayload): Promise<TestSchedule> {
    const res = await api.post<TestSchedule>('/schedules/', payload);
    return res.data;
  },

  async update(scheduleId: number, payload: UpdateSchedulePayload): Promise<TestSchedule> {
    const res = await api.put<TestSchedule>(`/schedules/${scheduleId}`, payload);
    return res.data;
  },

  async toggle(scheduleId: number): Promise<TestSchedule> {
    const res = await api.post<TestSchedule>(`/schedules/${scheduleId}/toggle`);
    return res.data;
  },

  async remove(scheduleId: number): Promise<void> {
    await api.delete(`/schedules/${scheduleId}`);
  },
};

export default schedulesService;

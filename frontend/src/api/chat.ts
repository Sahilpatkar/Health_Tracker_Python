import api from './client';

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  action_data?: ActionData[];
}

export interface ActionData {
  action_id: number;
  action_type: 'update_goals' | 'create_workout' | 'log_food' | 'log_water';
  display_data: Record<string, unknown>;
}

export interface Memory {
  id: number;
  category: string;
  content: string;
  created_at: string;
}

export type SSEEvent =
  | { event: 'text'; data: string }
  | { event: 'status'; data: string }
  | { event: 'action'; data: ActionData }
  | { event: 'done'; data: string };

export async function streamMessage(
  content: string,
  onEvent: (evt: SSEEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/chat/message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ content }),
    signal,
  });

  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    throw new Error(`Chat request failed: ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    let currentEvent = '';
    let currentData = '';

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7);
        currentData = '';
      } else if (line.startsWith('data: ')) {
        currentData += (currentData ? '\n' : '') + line.slice(6);
      } else if (line === '' && currentEvent) {
        let parsed: SSEEvent;
        if (currentEvent === 'action') {
          try {
            parsed = { event: 'action', data: JSON.parse(currentData) as ActionData };
          } catch {
            currentEvent = '';
            currentData = '';
            continue;
          }
        } else {
          switch (currentEvent) {
            case 'text':
            case 'status':
            case 'done':
              parsed = { event: currentEvent, data: currentData };
              break;
            default:
              parsed = { event: 'text', data: currentData };
          }
        }
        onEvent(parsed);
        currentEvent = '';
        currentData = '';
      }
    }
  }
}

export async function getChatHistory(limit = 50): Promise<ChatMessage[]> {
  const res = await api.get<ChatMessage[]>('/chat/history', { params: { limit } });
  return res.data;
}

export async function confirmAction(actionId: number) {
  const res = await api.post('/chat/confirm-action', { action_id: actionId });
  return res.data;
}

export async function rejectAction(actionId: number) {
  const res = await api.post('/chat/reject-action', { action_id: actionId });
  return res.data;
}

export async function getMemories(): Promise<Memory[]> {
  const res = await api.get<Memory[]>('/chat/memories');
  return res.data;
}

export async function deleteMemory(id: number) {
  const res = await api.delete(`/chat/memories/${id}`);
  return res.data;
}

export async function clearHistory() {
  const res = await api.delete('/chat/history');
  return res.data;
}

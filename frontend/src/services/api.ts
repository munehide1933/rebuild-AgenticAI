import axios from 'axios';
import type { ChatRequest, ChatResponse, Conversation, ConversationDetail } from '@/types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

interface StreamHandlers {
  onChunk: (chunk: string) => void;
  onDone: (payload: ChatResponse) => void;
}

export const chatApi = {
  sendMessage: (data: ChatRequest) => api.post<ChatResponse>('/chat/message', data),
  streamMessage: async (data: ChatRequest, handlers: StreamHandlers) => {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Stream request failed: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';

      for (const event of events) {
        const line = event
          .split('\n')
          .find((item) => item.startsWith('data: '));
        if (!line) continue;

        try {
          const parsed = JSON.parse(line.replace('data: ', ''));
          if (parsed.type === 'chunk') {
            handlers.onChunk(parsed.content || '');
          }
          if (parsed.type === 'done') {
            handlers.onDone(parsed.payload as ChatResponse);
          }
        } catch {
          // ignore malformed chunks
        }
      }
    }
  },
  listConversations: () => api.get<Conversation[]>('/chat/conversations'),
  getConversation: (conversationId: string) =>
    api.get<ConversationDetail>(`/chat/conversations/${conversationId}`),
  deleteConversation: (conversationId: string) =>
    api.delete<{ success: boolean }>(`/chat/conversations/${conversationId}`),
};

export default api;

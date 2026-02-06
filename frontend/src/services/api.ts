import axios from 'axios';
import type { ChatRequest, ChatResponse, Conversation, ConversationDetail } from '@/types';

const api = axios.create({
  baseURL: '/api',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
});

interface StreamHandlers {
  onChunk: (chunk: string) => void;
  onDone: (payload: ChatResponse) => void;
  onStatus?: (status: string) => void;
  onError?: (message: string) => void;
}

const handleStreamError = (error: unknown, handlers: StreamHandlers) => {
  if (error instanceof Error) {
    handlers.onError?.(error.message);
  } else {
    handlers.onError?.('Unknown error occurred');
  }
};

export const chatApi = {
  sendMessage: (data: ChatRequest) => api.post<ChatResponse>('/chat/message', data),

  streamMessage: async (data: ChatRequest, handlers: StreamHandlers) => {
    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Stream request failed: ${response.status} ${response.statusText}`);
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

            switch (parsed.type) {
              case 'chunk':
                handlers.onChunk(parsed.content || '');
                break;
              case 'status':
                handlers.onStatus?.(parsed.content || '');
                break;
              case 'error':
                handlers.onError?.(parsed.message || 'Stream error');
                break;
              case 'done':
                handlers.onDone(parsed.payload as ChatResponse);
                break;
              default:
                break;
            }
          } catch {
            // ignore malformed chunks
          }
        }
      }
    } catch (error) {
      handleStreamError(error, handlers);
      throw error;
    }
  },

  listConversations: () => api.get<Conversation[]>('/chat/conversations'),
  getConversation: (conversationId: string) =>
    api.get<ConversationDetail>(`/chat/conversations/${conversationId}`),
  deleteConversation: (conversationId: string) =>
    api.delete<{ success: boolean }>(`/chat/conversations/${conversationId}`),
};

export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      const detail = (error.response.data as { detail?: string })?.detail;
      return detail || `Request failed with status ${error.response.status}`;
    }
    if (error.request) {
      return 'No response received from server';
    }
    return error.message || 'Unexpected error';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Unexpected error';
};

export default api;

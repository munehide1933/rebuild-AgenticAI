<<<<<<< HEAD
import axios from 'axios';
=======
// frontend/src/services/api.ts
import axios, { AxiosError, AxiosRequestConfig } from 'axios';
>>>>>>> 81cede4 (Initial commit)
import type { ChatRequest, ChatResponse, Conversation, ConversationDetail } from '@/types';

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 120 秒超时
  headers: {
    'Content-Type': 'application/json',
  },
});

<<<<<<< HEAD
=======
// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证 token
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.config.url} - ${response.status}`);
    return response;
  },
  (error: AxiosError) => {
    console.error('[API Response Error]', error);
    
    // 统一错误处理
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          console.error('Bad Request:', data);
          break;
        case 401:
          console.error('Unauthorized - redirecting to login');
          // 可以重定向到登录页
          break;
        case 404:
          console.error('Not Found:', error.config?.url);
          break;
        case 429:
          console.error('Rate Limited - too many requests');
          break;
        case 500:
          console.error('Internal Server Error');
          break;
        default:
          console.error(`Error ${status}:`, data);
      }
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Request setup error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

>>>>>>> 81cede4 (Initial commit)
interface StreamHandlers {
  onChunk: (chunk: string) => void;
  onDone: (payload: ChatResponse) => void;
  onStatus?: (status: string) => void;
  onError?: (message: string) => void;
}

export const chatApi = {
<<<<<<< HEAD
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
          if (parsed.type === 'status') {
            handlers.onStatus?.(parsed.content || '');
          }
          if (parsed.type === 'error') {
            handlers.onError?.(parsed.message || 'Stream error');
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
=======
  sendMessage: (data: ChatRequest) => 
    api.post<ChatResponse>('/chat/message', data),
  
  streamMessage: async (data: ChatRequest, handlers: StreamHandlers) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 120秒超时
    
    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Stream request failed: ${response.status} ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
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
              case 'ping':
                // 心跳包，忽略
                break;
              default:
                console.warn('Unknown event type:', parsed.type);
            }
          } catch (parseError) {
            console.error('Failed to parse SSE event:', parseError);
          }
        }
      }
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          handlers.onError?.('请求超时，请重试');
        } else {
          handlers.onError?.(error.message);
        }
      } else {
        handlers.onError?.('Unknown error occurred');
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  },
  
  listConversations: (params?: { limit?: number; offset?: number }) => 
    api.get<Conversation[]>('/chat/conversations', { params }),
  
  getConversation: (conversationId: string) =>
    api.get<ConversationDetail>(`/chat/conversations/${conversationId}`),
  
  deleteConversation: (conversationId: string) =>
    api.delete<{ success: boolean }>(`/chat/conversations/${conversationId}`),
  
  getReasoningStats: () =>
    api.get('/chat/reasoning-stats'),
>>>>>>> 81cede4 (Initial commit)
};

export default api;
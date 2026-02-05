import axios from 'axios';
import type { ChatRequest, ChatResponse } from '@/types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chat API
export const chatApi = {
  sendMessage: (data: ChatRequest) =>
    api.post<ChatResponse>('/chat/message', data),
};

export default api;

import axios from 'axios';
import type { ChatRequest, ChatResponse, Conversation, ConversationDetail } from '@/types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatApi = {
  sendMessage: (data: ChatRequest) => api.post<ChatResponse>('/chat/message', data),
  listConversations: () => api.get<Conversation[]>('/chat/conversations'),
  getConversation: (conversationId: string) =>
    api.get<ConversationDetail>(`/chat/conversations/${conversationId}`),
  deleteConversation: (conversationId: string) =>
    api.delete<{ success: boolean }>(`/chat/conversations/${conversationId}`),
};

export default api;

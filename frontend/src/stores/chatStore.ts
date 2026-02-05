import { create } from 'zustand';
import type { ChatRequest, Conversation, Message } from '@/types';
import { chatApi } from '@/services/api';

interface ChatState {
  currentConversationId: string | null;
  messages: Message[];
  conversations: Conversation[];
  isLoading: boolean;
  isHistoryLoading: boolean;
  error: string | null;

  startNewConversation: () => void;
  sendMessage: (request: ChatRequest) => Promise<void>;
  clearMessages: () => void;
  loadConversations: () => Promise<void>;
  loadConversationDetail: (conversationId: string) => Promise<void>;
  deleteConversation: (conversationId: string) => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  currentConversationId: null,
  messages: [],
  conversations: [],
  isLoading: false,
  isHistoryLoading: false,
  error: null,

  startNewConversation: () => {
    set({ currentConversationId: null, messages: [], error: null });
  },

  loadConversations: async () => {
    set({ isHistoryLoading: true, error: null });
    try {
      const response = await chatApi.listConversations();
      set({ conversations: response.data, isHistoryLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to load conversations', isHistoryLoading: false });
    }
  },

  loadConversationDetail: async (conversationId: string) => {
    set({ isHistoryLoading: true, error: null });
    try {
      const response = await chatApi.getConversation(conversationId);
      set({
        currentConversationId: response.data.id,
        messages: response.data.messages,
        isHistoryLoading: false,
      });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to load conversation', isHistoryLoading: false });
    }
  },

  deleteConversation: async (conversationId: string) => {
    set({ error: null });
    try {
      await chatApi.deleteConversation(conversationId);
      set((state) => ({
        conversations: state.conversations.filter((item) => item.id !== conversationId),
        ...(state.currentConversationId === conversationId
          ? { currentConversationId: null, messages: [] }
          : {}),
      }));
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to delete conversation' });
    }
  },

  sendMessage: async (request: ChatRequest) => {
    set({ isLoading: true, error: null });

    const userMessage: Message = {
      id: `local-user-${Date.now()}`,
      role: 'user',
      content: request.message,
      created_at: new Date().toISOString(),
    };

    set((state) => ({ messages: [...state.messages, userMessage] }));

    try {
      const response = await chatApi.sendMessage({
        ...request,
        conversation_id: request.conversation_id ?? get().currentConversationId ?? undefined,
      });

      const assistantMessage: Message = {
        id: response.data.message_id,
        role: 'assistant',
        content: response.data.content,
        meta_info: {
          workflow_phase: response.data.workflow_state?.current_phase,
          code_modifications: response.data.code_modifications,
          security_warnings: response.data.suggestions,
          mcp: response.data.workflow_state?.phase_outputs?.mcp,
        },
        created_at: new Date().toISOString(),
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        currentConversationId: response.data.conversation_id,
        isLoading: false,
      }));

      await get().loadConversations();
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to send message',
        isLoading: false,
      });
    }
  },

  clearMessages: () => {
    set({ messages: [], currentConversationId: null });
  },
}));

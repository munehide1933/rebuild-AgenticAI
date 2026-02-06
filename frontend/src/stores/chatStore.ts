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

    const localAssistantId = `local-assistant-${Date.now()}`;
    const assistantMessage: Message = {
      id: localAssistantId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
    };

    set((state) => ({ messages: [...state.messages, userMessage, assistantMessage] }));

    try {
      await chatApi.streamMessage(
        {
          ...request,
          conversation_id: request.conversation_id ?? get().currentConversationId ?? undefined,
        },
        {
          onChunk: (chunk) => {
            set((state) => ({
              messages: state.messages.map((msg) =>
                msg.id === localAssistantId
                  ? { ...msg, content: `${msg.content}${chunk}` }
                  : msg,
              ),
            }));
          },
          onStatus: (status) => {
            set((state) => ({
              messages: state.messages.map((msg) =>
                msg.id === localAssistantId && msg.content.length === 0
                  ? { ...msg, content: status }
                  : msg,
              ),
            }));
          },
          onError: (message) => {
            set((state) => ({
              messages: state.messages.map((msg) =>
                msg.id === localAssistantId ? { ...msg, content: message } : msg,
              ),
              error: message,
              isLoading: false,
            }));
          },
          onDone: (payload) => {
            set((state) => ({
              messages: state.messages.map((msg) =>
                msg.id === localAssistantId
                  ? {
                      ...msg,
                      id: payload.message_id,
                      content: payload.content,
                      meta_info: {
                        workflow_phase: payload.workflow_state?.current_phase,
                        code_modifications: payload.code_modifications,
                        security_warnings: payload.suggestions,
                        mcp: payload.workflow_state?.phase_outputs?.mcp,
                        reasoning_trace: payload.workflow_state?.phase_outputs?.reasoning_trace,
                        react_steps: payload.workflow_state?.phase_outputs?.react_steps,
                        reflection: payload.workflow_state?.phase_outputs?.reflection,
                      },
                    }
                  : msg,
              ),
              currentConversationId: payload.conversation_id,
            }));
          },
        },
      );

      set({ isLoading: false });
      await get().loadConversations();
    } catch (error: any) {
      set((state) => ({
        messages: state.messages.filter((msg) => msg.id !== localAssistantId),
        error: error.response?.data?.detail || error.message || 'Failed to send message',
        isLoading: false,
      }));
    }
  },

  clearMessages: () => {
    set({ messages: [], currentConversationId: null });
  },
}));

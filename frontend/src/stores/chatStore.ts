import { create } from 'zustand';
import type { Message, ChatRequest } from '@/types';
import { chatApi } from '@/services/api';

interface ChatState {
  currentConversationId: string | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  
  startNewConversation: () => void;
  sendMessage: (request: ChatRequest) => Promise<void>;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  currentConversationId: null,
  messages: [],
  isLoading: false,
  error: null,

  startNewConversation: () => {
    set({ currentConversationId: null, messages: [] });
  },

  sendMessage: async (request: ChatRequest) => {
    set({ isLoading: true, error: null });
    
    // 添加用户消息到UI
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: request.message,
      created_at: new Date().toISOString(),
    };
    
    set((state) => ({
      messages: [...state.messages, userMessage],
    }));

    try {
      const response = await chatApi.sendMessage(request);
      
      // 添加助手消息
      const assistantMessage: Message = {
        id: response.data.message_id,
        role: 'assistant',
        content: response.data.content,
        meta_info: {
          workflow_phase: response.data.workflow_state?.current_phase,
          code_modifications: response.data.code_modifications,
          security_warnings: response.data.suggestions,
        },
        created_at: new Date().toISOString(),
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        currentConversationId: response.data.conversation_id,
        isLoading: false,
      }));
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

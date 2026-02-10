'use client';

import React, { useState, useRef, KeyboardEvent } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { Send } from 'lucide-react';

const InputArea: React.FC = () => {
  const [message, setMessage] = useState('');
  const [deepThinking, setDeepThinking] = useState(false);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const { sendMessage, isLoading, currentConversationId } = useChatStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const messageText = message;
    setMessage('');

    await sendMessage({
      message: messageText,
      conversation_id: currentConversationId ?? undefined,
      deep_thinking: deepThinking,
      web_search_enabled: webSearchEnabled,
    });

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
  };

  return (
    <div className="border-t border-gray-200 bg-white px-6 py-4">
      <form onSubmit={handleSubmit} className="flex items-end gap-3">
        {/* Textarea */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="输入消息... (Shift + Enter 换行)"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            rows={1}
            disabled={isLoading}
          />
        </div>

        {/* Send Button */}
        <button
          type="submit"
          disabled={!message.trim() || isLoading}
          className="p-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>

      <div className="mt-3 flex items-center gap-4 text-xs text-gray-600">
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            checked={deepThinking}
            onChange={(e) => setDeepThinking(e.target.checked)}
            disabled={isLoading}
          />
          Deep Thinking
        </label>

        <label className="inline-flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            checked={webSearchEnabled}
            onChange={(e) => setWebSearchEnabled(e.target.checked)}
            disabled={isLoading}
          />
          Web Search
        </label>
      </div>

      {/* Helper Text */}
      <div className="mt-2 text-xs text-gray-400 text-center">
        Meta-Agent 支持多阶段分析、代码生成建议与可选联网检索
      </div>
    </div>
  );
};

export default InputArea;

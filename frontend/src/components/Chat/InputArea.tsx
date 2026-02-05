import React, { useState, useRef, KeyboardEvent } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { Send } from 'lucide-react';

const InputArea: React.FC = () => {
  const [message, setMessage] = useState('');
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

      {/* Helper Text */}
      <div className="mt-2 text-xs text-gray-400 text-center">
        Meta-Agent 支持多角色协作、代码生成、安全审查等功能
      </div>
    </div>
  );
};

export default InputArea;

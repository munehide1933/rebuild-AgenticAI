'use client';

import React from 'react';
import { useChatStore } from '@/stores/chatStore';
import MessageList from './MessageList';
import InputArea from './InputArea';
import { AlertCircle, Plus } from 'lucide-react';

const ChatInterface: React.FC = () => {
  const { messages, isLoading, error, startNewConversation, currentConversationId } = useChatStore();

  return (
    <div className="flex flex-col h-full min-h-0 bg-white">
      <header className="flex-shrink-0 px-6 py-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">Meta-Agent</h2>
            <p className="text-sm text-gray-500 mt-1">
              {currentConversationId
                ? `会话 ID: ${currentConversationId.slice(0, 8)}...`
                : '智能开发助手'}
            </p>
          </div>
          <button
            type="button"
            onClick={startNewConversation}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            新对话
          </button>
        </div>
      </header>

      {error && (
        <div className="flex-shrink-0 mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-red-800">出现错误</h3>
            <p className="text-sm text-red-600 mt-1">{error}</p>
          </div>
        </div>
      )}

      <div className="flex-1 min-h-0 overflow-hidden">
        <MessageList messages={messages} isLoading={isLoading} />
      </div>

      <div className="flex-shrink-0 border-t border-gray-200">
        <InputArea />
      </div>
    </div>
  );
};

export default ChatInterface;

import React from 'react';
import { useChatStore } from '@/stores/chatStore';
import MessageList from './MessageList';
import InputArea from './InputArea';
import { AlertCircle, Plus } from 'lucide-react';

const ChatInterface: React.FC = () => {
  const { messages, isLoading, error, startNewConversation, currentConversationId } = useChatStore();

  return (
<<<<<<< HEAD
    <div className="flex flex-col h-full bg-white">
      {/* Header - Fixed */}
=======
    <div className="flex flex-col h-full min-h-0 bg-white">
>>>>>>> 3a0ffb3f0f5903549c7c3d0d57cb153bddbd4bc2
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

      {/* Error Banner - Fixed */}
      {error && (
        <div className="flex-shrink-0 mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-red-800">出现错误</h3>
            <p className="text-sm text-red-600 mt-1">{error}</p>
          </div>
        </div>
      )}

<<<<<<< HEAD
      {/* Message List Container - 关键修复：必须使用 min-h-0 和 overflow-hidden */}
=======
>>>>>>> 3a0ffb3f0f5903549c7c3d0d57cb153bddbd4bc2
      <div className="flex-1 min-h-0 overflow-hidden">
        <MessageList messages={messages} isLoading={isLoading} />
      </div>

      {/* Input Area - Fixed */}
      <div className="flex-shrink-0 border-t border-gray-200">
        <InputArea />
      </div>
    </div>
  );
};

export default ChatInterface;

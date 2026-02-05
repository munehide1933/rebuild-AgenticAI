import React from 'react';
import { useChatStore } from '@/stores/chatStore';
import MessageList from './MessageList';
import InputArea from './InputArea';
import { AlertCircle, Plus } from 'lucide-react';

const ChatInterface: React.FC = () => {
  const { messages, isLoading, error, startNewConversation } = useChatStore();

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header - 固定高度 */}
      <header className="flex-shrink-0 px-6 py-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              Meta-Agent
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              通用智能体对话
            </p>
          </div>
          <button
            type="button"
            onClick={startNewConversation}
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary-600 text-white rounded text-sm hover:bg-primary-700"
          >
            <Plus className="w-4 h-4" />
            新建对话
          </button>
        </div>
      </header>

      {/* Error - 固定高度 */}
      {error && (
        <div className="flex-shrink-0 mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-medium text-red-800">错误</h3>
            <p className="text-sm text-red-600 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Messages - 可滚动区域，flex-1 占据剩余空间 */}
      <div className="flex-1 overflow-hidden">
        <MessageList messages={messages} isLoading={isLoading} />
      </div>

      {/* Input - 固定高度 */}
      <div className="flex-shrink-0 border-t border-gray-200">
        <InputArea />
      </div>
    </div>
  );
};

export default ChatInterface;

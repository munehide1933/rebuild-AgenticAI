import React from 'react';
import { format } from 'date-fns';
import { MessageSquare, Trash2 } from 'lucide-react';
import type { Conversation } from '@/types';

interface ConversationSidebarProps {
  conversations: Conversation[];
  currentConversationId: string | null;
  isLoading: boolean;
  onSelect: (conversationId: string) => void;
  onDelete: (conversationId: string) => void;
}

const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  conversations,
  currentConversationId,
  isLoading,
  onSelect,
  onDelete,
}) => {
  return (
    <aside className="w-80 border-r border-gray-200 bg-white h-screen flex flex-col">
      <div className="px-4 py-4 border-b border-gray-100">
        <h2 className="font-semibold text-gray-800">会话历史</h2>
        <p className="text-xs text-gray-500 mt-1">摘要展示（删除仅隐藏，数据保留用于审计）</p>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {isLoading && <p className="text-sm text-gray-500">加载中...</p>}

        {!isLoading && conversations.length === 0 && (
          <p className="text-sm text-gray-400">暂无历史会话</p>
        )}

        {conversations.map((item) => {
          const active = item.id === currentConversationId;
          return (
            <div
              key={item.id}
              className={`group border rounded-lg p-3 cursor-pointer ${
                active ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => onSelect(item.id)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2 min-w-0">
                  <MessageSquare className="w-4 h-4 text-gray-500 mt-0.5" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{item.title || '未命名会话'}</p>
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{item.summary || '暂无摘要'}</p>
                  </div>
                </div>

                <button
                  type="button"
                  className="opacity-0 group-hover:opacity-100 transition text-red-500 hover:text-red-600"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(item.id);
                  }}
                  title="删除会话"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <p className="text-[11px] text-gray-400 mt-2">{format(new Date(item.updated_at), 'MM-dd HH:mm')}</p>
            </div>
          );
        })}
      </div>
    </aside>
  );
};

export default ConversationSidebar;

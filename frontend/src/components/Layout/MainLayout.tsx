import React, { useEffect } from 'react';
import ChatInterface from '../Chat/ChatInterface';
import ConversationSidebar from '../Chat/ConversationSidebar';
import { useChatStore } from '@/stores/chatStore';

const MainLayout: React.FC = () => {
  const {
    conversations,
    currentConversationId,
    isHistoryLoading,
    loadConversations,
    loadConversationDetail,
    deleteConversation,
  } = useChatStore();

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  return (
    <div className="flex h-screen bg-gray-50">
      <ConversationSidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        isLoading={isHistoryLoading}
        onSelect={loadConversationDetail}
        onDelete={deleteConversation}
      />

      <main className="flex-1 flex flex-col overflow-hidden">
        <ChatInterface />
      </main>
    </div>
  );
};

export default MainLayout;

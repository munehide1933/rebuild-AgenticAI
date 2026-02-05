import React from 'react';
import ChatInterface from '../Chat/ChatInterface';

const MainLayout: React.FC = () => (
  <div className="flex h-screen bg-gray-50">
    <main className="flex-1 flex flex-col overflow-hidden">
      <ChatInterface />
    </main>
  </div>
);

export default MainLayout;

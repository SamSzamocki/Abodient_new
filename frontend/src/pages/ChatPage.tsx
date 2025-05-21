
import React from 'react';
import ChatInterface from '@/components/chat/ChatInterface';

const ChatPage: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-foreground">Chat</h1>
      <ChatInterface />
    </div>
  );
};

export default ChatPage;

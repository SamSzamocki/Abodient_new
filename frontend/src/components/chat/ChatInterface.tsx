import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send } from 'lucide-react';
import Spinner from '@/components/ui/Spinner';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

const ChatInterface: React.FC = () => {
  // State to hold all chat messages
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', text: "Hello! How can I help you today?", sender: 'ai', timestamp: new Date() },
  ]);
  // State to hold the current input text
  const [inputText, setInputText] = useState('');
  // State to show loading indicator while waiting for API response
  const [loading, setLoading] = useState(false);

  // Function to send message to backend and update chat
  const handleSendMessage = async () => {
    if (inputText.trim() === '') return;
    const userMessage: Message = {
      id: String(Date.now()),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    try {
      // Send the user's message to the backend API
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const apiKey = import.meta.env.VITE_API_KEY || '';
      const response = await fetch(`${apiUrl}/main-agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': apiKey,
        },
        body: JSON.stringify({ session_id: 'frontend-session', text: inputText }),
      });
      if (!response.ok) {
        throw new Error('API error');
      }
      const data = await response.json();
      // Prepare the AI's response based on API output
      let aiText = '';
      if (data.clarifying_question) {
        aiText = data.clarifying_question;
      } else if (data.query_summary) {
        aiText = data.query_summary;
      } else {
        aiText = JSON.stringify(data);
      }
      const aiMessage: Message = {
        id: String(Date.now() + 1),
        text: aiText,
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      // Show an error message if the API call fails
      const errorMessage: Message = {
        id: String(Date.now() + 2),
        text: 'Sorry, there was a problem contacting the server.',
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] bg-card border border-border rounded-lg shadow-sm">
      <div className="p-4 border-b border-border flex justify-end">
        <Button variant="outline">Resolved Queries</Button>
      </div>
      <div className="flex-grow p-6 space-y-4 overflow-y-auto">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg shadow transition-all duration-200
                ${msg.sender === 'user' ? 'bg-primary text-primary-foreground' : ''}
                ${msg.sender === 'ai' ? 'bg-secondary text-secondary-foreground' : ''}
                ${msg.text.includes('problem contacting the server') ? 'bg-red-100 text-red-700 border border-red-400' : ''}
              `}
            >
              <p className="text-sm">{msg.text}</p>
              <p className={`text-xs mt-1 ${msg.sender === 'user' ? 'text-primary-foreground/70 text-right' : 'text-muted-foreground/70 text-left'}`}>
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}
        {/* Show a loading spinner while waiting for API response */}
        {loading && (
          <div className="flex justify-start">
            <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg shadow bg-secondary text-secondary-foreground flex items-center">
              <Spinner />
              <span className="ml-2 text-sm">Thinking...</span>
            </div>
          </div>
        )}
      </div>
      <div className="p-4 border-t border-border bg-background/50">
        <div className="flex items-center space-x-2">
          <Input
            type="text"
            placeholder="Type your message..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            className="flex-grow"
            disabled={loading}
          />
          <Button onClick={handleSendMessage} size="icon" disabled={loading}>
            <Send size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

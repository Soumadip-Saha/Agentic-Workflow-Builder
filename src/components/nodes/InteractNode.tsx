// src/components/nodes/InteractNode.tsx
import React, { useState, useRef, useEffect } from 'react';
import { useWorkflowStore } from '@/store/workflow-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send } from 'lucide-react';
import { callInvokeAPI } from '@/lib/api';

// THIS IS THE UPDATED MESSAGE COMPONENT
const Message = ({ msg }: { msg: any }) => {
  // User messages are simple and aligned to the right.
  if (msg.type === 'user') {
    return <div className="p-2 my-2 bg-blue-100 rounded-lg self-end max-w-lg whitespace-pre-wrap break-words">{msg.content}</div>;
  }
  
  // Error messages are simple and aligned to the left.
  if (msg.type === 'error') {
    return <div className="p-2 my-2 bg-red-100 text-red-700 rounded-lg self-start max-w-lg">{msg.content}</div>;
  }
  
  // All other messages (ai, tool) are complex and aligned to the left.
  return (
    <div className="flex flex-col items-start self-start max-w-lg w-full">
      {/* This is the new header that displays the node name. */}
      {msg.node?.name && (
        <div className="text-xs font-bold text-gray-500 px-2">
          {/* We can use different icons for different message types */}
          {msg.type === 'tool' ? '🛠️' : '🤖'} {msg.node.name}
        </div>
      )}
      <div className="p-2 mt-1 bg-gray-100 rounded-lg w-full whitespace-pre-wrap break-words">
        {msg.content}
        {/* This part correctly displays tool call information if it exists */}
        {msg.tool_calls && (
          <div className="mt-2 p-2 border-t border-gray-300">
              <p className="font-bold text-xs">Tool Call:</p>
              <pre className="text-xs bg-gray-200 p-2 rounded mt-1">{JSON.stringify(msg.tool_calls, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
};

// The rest of this component is unchanged.
export function InteractNode() {
  const { chatMessages, addChatMessage, streamMessage, clearChatMessages } = useWorkflowStore();
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [chatMessages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;
    setIsLoading(true);

    const userMessage = { type: 'user', content: inputValue };
    addChatMessage(userMessage);
    const query = inputValue;
    setInputValue('');

    await callInvokeAPI(query, streamMessage, addChatMessage);

    setIsLoading(false);
  };

  return (
    <div className="w-[450px] h-[600px] bg-white rounded-lg border-2 border-gray-400 flex flex-col shadow-xl">
      <div className="p-3 font-bold border-b">💬 Chat Interaction</div>
      <div className="flex-grow p-4 overflow-y-auto bg-gray-50 flex flex-col gap-2">
        {chatMessages.map((msg, index) => (
          <Message key={index} msg={msg} />
        ))}
        {isLoading && chatMessages[chatMessages.length - 1]?.type === 'user' && (
            <div className="p-2 my-2 bg-gray-100 rounded-lg self-start italic">Thinking...</div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="p-3 border-t flex items-center gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <Button onClick={handleSendMessage} disabled={isLoading} size="icon">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
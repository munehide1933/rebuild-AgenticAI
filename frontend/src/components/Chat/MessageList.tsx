import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Message } from '@/types';
import { Bot, User, Clock } from 'lucide-react';
import { format } from 'date-fns';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isLoading }) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div
      ref={scrollContainerRef}
<<<<<<< HEAD
      className="flex-1 overflow-y-auto px-6 py-4 space-y-6"
      style={{ 
        maxHeight: '100%',
        overflowY: 'auto',
        WebkitOverflowScrolling: 'touch'
      }}
=======
      onScroll={updateAutoScroll}
      className="flex-1 min-h-0 overflow-y-auto px-6 py-4 space-y-6 scrollbar-thin"
>>>>>>> 3a0ffb3f0f5903549c7c3d0d57cb153bddbd4bc2
    >
      {messages.length === 0 && !isLoading && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <Bot className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">开始新的对话</p>
            <p className="text-sm text-gray-400 mt-2">我可以帮您回答问题、编写代码、提供建议</p>
          </div>
        </div>
      )}

      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}

      {isLoading && (
        <div className="flex items-start gap-4">
          <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
            <Bot className="w-5 h-5 text-primary-600 animate-pulse" />
          </div>
          <div className="flex-1">
            <div className="bg-gray-50 px-4 py-3 rounded-2xl rounded-tl-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
};

interface MessageItemProps {
  message: Message;
}

const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const isUser = message.role === 'user';
<<<<<<< HEAD
=======
  const hasMetadata = !!message.meta_info && Object.keys(message.meta_info).length > 0;
>>>>>>> 3a0ffb3f0f5903549c7c3d0d57cb153bddbd4bc2

  return (
    <div className={`flex items-start gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div 
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser ? 'bg-gray-200' : 'bg-primary-100'
        }`}
      >
        {isUser ? (
          <User className="w-5 h-5 text-gray-600" />
        ) : (
          <Bot className="w-5 h-5 text-primary-600" />
        )}
      </div>

      <div className={`flex-1 max-w-3xl ${isUser ? 'flex flex-col items-end' : ''}`}>
        <div className={`flex items-center gap-2 mb-2 ${isUser ? 'flex-row-reverse' : ''}`}>
          <span className="font-medium text-gray-700 text-sm">
            {isUser ? 'You' : 'AI Assistant'}
          </span>
          <span className="text-xs text-gray-400 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {format(new Date(message.created_at), 'HH:mm')}
          </span>
        </div>

        <div 
          className={`prose prose-sm max-w-none ${
            isUser 
              ? 'bg-primary-600 text-white px-4 py-3 rounded-2xl rounded-tr-sm' 
              : 'bg-gray-50 px-4 py-3 rounded-2xl rounded-tl-sm text-gray-800'
          }`}
        >
          {isUser ? (
            <p className="text-white whitespace-pre-wrap m-0 leading-relaxed">
              {message.content}
            </p>
          ) : (
<<<<<<< HEAD
            <ReactMarkdown 
              components={{
                p: ({ children }) => <p className="m-0 mb-2 last:mb-0 leading-relaxed">{children}</p>,
                code: ({ inline, children }) => 
                  inline ? (
                    <code className="bg-gray-200 text-gray-800 px-1.5 py-0.5 rounded text-sm">
                      {children}
                    </code>
                  ) : (
                    <code className="block bg-gray-800 text-gray-100 p-3 rounded-lg my-2 overflow-x-auto">
                      {children}
                    </code>
                  ),
                ul: ({ children }) => <ul className="my-2 ml-4 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="my-2 ml-4 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
=======
            <ReactMarkdown>{message.content}</ReactMarkdown>
          )}
        </div>

        {hasMetadata && !isUser && (
          <div className="mt-3 space-y-2">
            {(message.meta_info?.code_modifications?.length ?? 0) > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-2">
                  <Code className="w-4 h-4 text-amber-600" />
                  <span className="text-sm font-medium text-amber-800">
                    代码建议 ({message.meta_info?.code_modifications?.length ?? 0})
                  </span>
                </div>
                <div className="space-y-1">
                  {message.meta_info?.code_modifications?.map((mod, idx) => (
                    <div key={idx} className="text-xs text-amber-700">
                      <span className="font-mono">{mod.file_path}</span>
                      <span className="ml-2 px-1.5 py-0.5 bg-amber-200 rounded">{mod.modification_type}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(message.meta_info?.security_warnings?.length ?? 0) > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span className="text-sm font-medium text-red-800">安全提示</span>
                </div>
                <div className="space-y-1">
                  {message.meta_info?.security_warnings?.map((warning, idx) => (
                    <p key={idx} className="text-xs text-red-700">{warning}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
>>>>>>> 3a0ffb3f0f5903549c7c3d0d57cb153bddbd4bc2
      </div>
    </div>
  );
};

export default MessageList;

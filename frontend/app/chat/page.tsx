"use client";

import { MessageSquare, Send, Bot, User, Sparkles, History, Plus, ChevronDown, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const mockConversations = [
  { id: "1", title: "Gold analysis for today", date: "2 hours ago" },
  { id: "2", title: "NASDAQ support levels", date: "Yesterday" },
  { id: "3", title: "Oil price prediction", date: "2 days ago" },
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I'm your AI trading assistant. I can help you with market analysis, price predictions, and trading strategies. What would you like to know?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: getAIResponse(input),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const getAIResponse = (query: string): string => {
    const lower = query.toLowerCase();
    if (lower.includes("gold") || lower.includes("xau")) {
      return "Based on current technical analysis, Gold (XAUUSD) is showing bullish momentum. Key levels:\n\n📈 Resistance: $5,020\n📉 Support: $4,945\n\nThe recent breakout above $5,000 suggests continuation toward $5,050. RSI is at 62, indicating room for further upside before overbought conditions.";
    }
    if (lower.includes("nasdaq") || lower.includes("ndx")) {
      return "NASDAQ is trading in a strong uptrend. Technical indicators:\n\n• Price above all major EMAs\n• Volume supporting the move\n• Next target: 22,800\n\nConsider entering on pullbacks to 22,200 support.";
    }
    if (lower.includes("oil") || lower.includes("wti")) {
      return "WTI Crude showing mixed signals:\n\n⚠️ Bearish: Supply concerns easing\n✅ Bullish: Geopolitical tensions support\n\nCurrent range: $74-$77\nWatch for breakout above $77 for bullish continuation.";
    }
    return "I can help you analyze any of our supported markets: XAUUSD (Gold), NASDAQ, DAX, USOIL, VIX, and DXY. What specific asset would you like to discuss?";
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-800 bg-gray-900/30 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <button className="w-full flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg transition-colors">
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          <p className="text-xs text-gray-500 uppercase tracking-wider px-3 py-2">Recent</p>
          {mockConversations.map((conv) => (
            <button
              key={conv.id}
              className="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-white transition-colors truncate"
            >
              {conv.title}
            </button>
          ))}
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <div className="h-14 border-b border-gray-800 flex items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-purple-400" />
            <span className="font-semibold">AI Trading Assistant</span>
            <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 text-xs rounded-full border border-purple-500/20">Pro</span>
          </div>
          <button className="text-gray-400 hover:text-white">
            <History className="w-5 h-5" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-4",
                message.role === "user" && "flex-row-reverse"
              )}
            >
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
                message.role === "assistant" ? "bg-purple-500/20" : "bg-gray-700"
              )}>
                {message.role === "assistant" ? (
                  <Sparkles className="w-4 h-4 text-purple-400" />
                ) : (
                  <User className="w-4 h-4 text-gray-400" />
                )}
              </div>
              <div className={cn(
                "max-w-3xl p-4 rounded-xl",
                message.role === "assistant" 
                  ? "bg-gray-900/50 border border-gray-800" 
                  : "bg-purple-500/10 border border-purple-500/20"
              )}>
                <p className="text-sm whitespace-pre-line">{message.content}</p>
                <span className="text-xs text-gray-500 mt-2 block">
                  {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-purple-400" />
              </div>
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-800">
          <div className="max-w-4xl mx-auto relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about any market..."
              className="w-full pl-4 pr-12 py-3 bg-gray-900 border border-gray-800 rounded-xl text-white placeholder:text-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
            />
            <button
              onClick={handleSend}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-purple-500 hover:bg-purple-600 rounded-lg transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-center text-xs text-gray-600 mt-2">
            AI can make mistakes. Always verify important trading decisions.
          </p>
        </div>
      </main>
    </div>
  );
}

import { useCallback, useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Trash2, Brain } from 'lucide-react';
import toast from 'react-hot-toast';
import MessageBubble from '../components/chat/MessageBubble';
import ActionCard from '../components/chat/ActionCard';
import TypingIndicator from '../components/chat/TypingIndicator';
import StatusBadge from '../components/chat/StatusBadge';
import {
  streamMessage,
  getChatHistory,
  clearHistory,
  getMemories,
  deleteMemory,
  type ChatMessage,
  type ActionData,
  type Memory,
  type SSEEvent,
} from '../api/chat';

interface DisplayMessage {
  id: number | string;
  role: 'user' | 'assistant';
  content: string;
  actions?: ActionData[];
  isStreaming?: boolean;
}

export default function Chat() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [statusText, setStatusText] = useState('');
  const [memories, setMemories] = useState<Memory[]>([]);
  const [showMemories, setShowMemories] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    });
  }, []);

  useEffect(() => {
    getChatHistory().then((history) => {
      const mapped: DisplayMessage[] = history.map((m: ChatMessage) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        actions: m.action_data,
      }));
      setMessages(mapped);
      setTimeout(scrollToBottom, 100);
    });
  }, [scrollToBottom]);

  useEffect(() => {
    if (showMemories) {
      getMemories().then(setMemories);
    }
  }, [showMemories]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    setInput('');
    setIsLoading(true);
    setStatusText('');

    const userMsg: DisplayMessage = { id: `u-${Date.now()}`, role: 'user', content: text };
    const assistantMsg: DisplayMessage = { id: `a-${Date.now()}`, role: 'assistant', content: '', actions: [], isStreaming: true };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    scrollToBottom();

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await streamMessage(
        text,
        (evt: SSEEvent) => {
          switch (evt.event) {
            case 'text':
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.id === assistantMsg.id) {
                  updated[updated.length - 1] = { ...last, content: last.content + evt.data };
                }
                return updated;
              });
              scrollToBottom();
              break;

            case 'status':
              setStatusText(evt.data);
              break;

            case 'action': {
              const action = evt.data as unknown as ActionData;
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.id === assistantMsg.id) {
                  updated[updated.length - 1] = {
                    ...last,
                    actions: [...(last.actions || []), action],
                  };
                }
                return updated;
              });
              scrollToBottom();
              break;
            }

            case 'done':
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.id === assistantMsg.id) {
                  updated[updated.length - 1] = { ...last, isStreaming: false };
                }
                return updated;
              });
              break;
          }
        },
        controller.signal,
      );
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      toast.error('Failed to get response');
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last.id === assistantMsg.id) {
          updated[updated.length - 1] = {
            ...last,
            content: last.content || 'Sorry, something went wrong. Please try again.',
            isStreaming: false,
          };
        }
        return updated;
      });
    } finally {
      setIsLoading(false);
      setStatusText('');
      abortRef.current = null;
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = async () => {
    await clearHistory();
    setMessages([]);
    toast.success('Chat history cleared');
  };

  const handleDeleteMemory = async (id: number) => {
    await deleteMemory(id);
    setMemories((prev) => prev.filter((m) => m.id !== id));
    toast.success('Memory removed');
  };

  const handleActionResolved = (_actionId: number, _status: 'confirmed' | 'rejected') => {
    scrollToBottom();
  };

  return (
    <div className="flex flex-col h-[calc(100dvh-4rem)] md:h-[calc(100dvh-2rem)] max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between py-4 px-1">
        <div>
          <h1 className="text-2xl font-bold">AI Trainer</h1>
          <p className="text-sm text-[var(--color-text-muted)]">Your personal fitness coach</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowMemories(!showMemories)}
            className="p-2 rounded-xl hover:bg-[var(--color-surface-dim)] text-[var(--color-text-muted)] transition-colors"
            title="Memories"
          >
            <Brain size={18} />
          </button>
          <button
            onClick={handleClear}
            className="p-2 rounded-xl hover:bg-red-50 dark:hover:bg-red-950/20 text-[var(--color-text-muted)] hover:text-red-500 transition-colors"
            title="Clear history"
          >
            <Trash2 size={18} />
          </button>
        </div>
      </div>

      {/* Memories panel */}
      <AnimatePresence>
        {showMemories && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 mb-3">
              <h3 className="text-sm font-semibold mb-2">Trainer Memories</h3>
              {memories.length === 0 ? (
                <p className="text-xs text-[var(--color-text-muted)]">No memories saved yet. Chat with the trainer and it will remember important context about you.</p>
              ) : (
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {memories.map((m) => (
                    <div key={m.id} className="flex items-start justify-between gap-2 text-xs">
                      <div>
                        <span className="inline-block px-1.5 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 font-medium mr-1.5">
                          {m.category}
                        </span>
                        {m.content}
                      </div>
                      <button
                        onClick={() => handleDeleteMemory(m.id)}
                        className="shrink-0 p-1 rounded hover:bg-red-50 dark:hover:bg-red-950/20 text-[var(--color-text-muted)] hover:text-red-500"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-4 px-1 pb-4"
      >
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mb-4">
              <Brain size={28} className="text-emerald-600 dark:text-emerald-300" />
            </div>
            <h2 className="text-lg font-semibold mb-1">Hey! I'm your AI Trainer</h2>
            <p className="text-sm text-[var(--color-text-muted)] max-w-sm">
              I can help you set goals, plan workouts, track nutrition, and more. Tell me about yourself or ask me anything!
            </p>
            <div className="flex flex-wrap gap-2 mt-4 justify-center">
              {[
                'Help me set my fitness goals',
                'Plan a push day workout',
                "What should I eat today?",
                'Review my progress this week',
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => { setInput(q); inputRef.current?.focus(); }}
                  className="px-3 py-1.5 rounded-full text-xs border border-[var(--color-border)] hover:bg-[var(--color-surface-dim)] transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id}>
            <MessageBubble
              role={msg.role}
              content={msg.content}
              isStreaming={msg.isStreaming}
            />
            {msg.actions && msg.actions.length > 0 && (
              <div className="ml-2 sm:ml-11 mt-2 space-y-2">
                {msg.actions.map((a) => (
                  <ActionCard
                    key={a.action_id}
                    action={a}
                    onResolved={handleActionResolved}
                  />
                ))}
              </div>
            )}
          </div>
        ))}

        <AnimatePresence>
          {isLoading && statusText && (
            <div className="ml-2 sm:ml-11">
              <StatusBadge text={statusText} />
            </div>
          )}
        </AnimatePresence>

        {isLoading && !messages[messages.length - 1]?.content && (
          <TypingIndicator />
        )}
      </div>

      {/* Input */}
      <div className="border-t border-[var(--color-border)] pt-3 pb-2 px-1">
        <div className="flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask your trainer anything..."
            rows={1}
            className="flex-1 resize-none px-4 py-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 max-h-32"
            style={{ minHeight: '44px' }}
          />
          <motion.button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            whileTap={{ scale: 0.95 }}
            className="p-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={18} />
          </motion.button>
        </div>
      </div>
    </div>
  );
}

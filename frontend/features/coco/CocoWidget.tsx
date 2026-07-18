"use client";

/**
 * Coco widget (Milestone 2): floating launcher button on every authenticated
 * page plus a slide-over chat panel. Talks to the backend only through
 * services/coco.ts; writes Coco proposes are out of scope for this milestone.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { createClient } from "@/lib/supabase/client";
import { sendChat } from "@/services/coco";
import type { ProposedAction } from "@/types/coco";

import { ConfirmActionCard } from "./ConfirmActionCard";
import { Markdown } from "./Markdown";

const ERROR_LINE = "Sorry, something went wrong. Please try again.";

type Message = {
  id: string;
  role: "USER" | "COCO";
  text: string;
  isError?: boolean;
  action?: ProposedAction;
};

async function getAccessToken(): Promise<string> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) {
    throw new Error("Your session has expired. Please sign in again.");
  }
  return session.access_token;
}

export function CocoWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);

  // conversation_id lives only in this ref: every page load is a fresh Coco
  // session. Nothing is persisted, so refresh / new tab / restart / re-login
  // all start a new conversation and never restore old messages.
  const conversationIdRef = useRef<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Escape closes the panel.
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  // Stick to the latest message / typing indicator.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending, open]);

  // Focus the input when the panel opens.
  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const submit = useCallback(async () => {
    const text = input.trim();
    if (!text || pending) return;

    setInput("");
    setMessages((prev) => [
      ...prev,
      { id: `local-${prev.length}-${text.length}`, role: "USER", text },
    ]);
    setPending(true);
    try {
      const token = await getAccessToken();
      const res = await sendChat(text, conversationIdRef.current, token);
      conversationIdRef.current = res.conversation_id;
      setMessages((prev) => [
        ...prev,
        {
          id: `reply-${prev.length}`,
          role: "COCO",
          text: res.reply,
          action: res.proposed_action ?? undefined,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: `error-${prev.length}`, role: "COCO", text: ERROR_LINE, isError: true },
      ]);
    } finally {
      setPending(false);
      inputRef.current?.focus();
    }
  }, [input, pending]);

  function onInputKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void submit();
    }
  }

  return (
    <>
      {/* Floating launcher */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open Coco, your AI study companion"
        className={`fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-neutral-900 text-white shadow-lg transition-all duration-200 hover:scale-110 hover:shadow-xl dark:bg-white dark:text-neutral-900 ${
          open ? "pointer-events-none scale-90 opacity-0" : "scale-100 opacity-100"
        }`}
      >
        <ChatIcon />
      </button>

      {/* Backdrop (mobile emphasis; click closes) */}
      <div
        aria-hidden
        onClick={() => setOpen(false)}
        className={`fixed inset-0 z-40 bg-black/30 transition-opacity duration-300 sm:bg-transparent ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      />

      {/* Slide-over panel: full-screen on mobile, ~400px sheet on desktop */}
      <aside
        role="dialog"
        aria-label="Coco chat"
        className={`fixed inset-0 z-50 flex flex-col border-neutral-200 bg-white shadow-2xl transition-transform duration-300 ease-out dark:border-neutral-800 dark:bg-neutral-900 sm:inset-y-0 sm:left-auto sm:right-0 sm:w-[400px] sm:border-l ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-neutral-200 px-4 py-3 dark:border-neutral-800">
          <div>
            <h2 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">
              Coco
            </h2>
            <p className="text-xs text-neutral-500">Your AI Study Companion</p>
          </div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close Coco chat"
            className="rounded-lg p-2 text-neutral-500 transition hover:bg-neutral-100 hover:text-neutral-900 dark:hover:bg-neutral-800 dark:hover:text-neutral-100"
          >
            <CloseIcon />
          </button>
        </div>

        {/* Conversation */}
        <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
          {messages.length === 0 && !pending && (
            <p className="py-8 text-center text-sm text-neutral-500">
              Hi! Ask me about your attendance, assignments, or what to do next.
            </p>
          )}
          {messages.map((m) => (
            <div key={m.id}>
              <div
                className={`flex ${m.role === "USER" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-sm ${
                    m.role === "USER"
                      ? "rounded-br-sm bg-neutral-900 text-white dark:bg-white dark:text-neutral-900"
                      : m.isError
                        ? "rounded-bl-sm border border-red-200 bg-red-50 text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300"
                        : "rounded-bl-sm bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-neutral-100"
                  }`}
                >
                  {m.role === "COCO" && !m.isError ? (
                    <Markdown text={m.text} />
                  ) : (
                    <p className="whitespace-pre-wrap">{m.text}</p>
                  )}
                </div>
              </div>
              {m.action && (
                <div className="mt-2 flex justify-start">
                  <div className="max-w-[85%]">
                    <ConfirmActionCard action={m.action} />
                  </div>
                </div>
              )}
            </div>
          ))}
          {pending && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void submit();
          }}
          className="flex items-end gap-2 border-t border-neutral-200 px-4 py-3 dark:border-neutral-800"
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onInputKeyDown}
            disabled={pending}
            rows={1}
            placeholder="Ask Coco…"
            className="max-h-32 flex-1 resize-none rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 placeholder:text-neutral-400 outline-none focus:border-neutral-500 disabled:opacity-60 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-100 dark:placeholder:text-neutral-500"
          />
          <button
            type="submit"
            disabled={pending || !input.trim()}
            className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 disabled:opacity-60 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
          >
            Send
          </button>
        </form>
      </aside>
    </>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-sm bg-neutral-100 px-3.5 py-3 dark:bg-neutral-800">
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-400 dark:bg-neutral-500"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
    </div>
  );
}

function ChatIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

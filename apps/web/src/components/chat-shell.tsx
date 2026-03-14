"use client";

import { FormEvent, useEffect, useState } from "react";
import { ArrowUp, LoaderCircle, SearchCheck, ShieldCheck } from "lucide-react";

import { ChatMessageCard } from "@/components/chat-message-card";
import { SidebarStatusCard } from "@/components/sidebar-status-card";
import { fetchDocumentStatus, sendQuestion, triggerReindex } from "@/lib/api";
import { ChatMessage, ConversationEntry, DocumentStatus } from "@/types/chat";

const SAMPLE_QUESTIONS = [
  "What is the PTO carryover policy?",
  "What is the parental leave policy?",
  "What are the paid holidays?",
  "What is the work from home policy?"
];

const IS_DEV = process.env.NODE_ENV !== "production";

export function ChatShell() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ConversationEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<DocumentStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [isReindexing, setIsReindexing] = useState(false);

  const history: ChatMessage[] = messages.map((message) => ({
    role: message.role,
    content: message.content
  }));

  async function loadStatus() {
    try {
      const nextStatus = await fetchDocumentStatus();
      setStatus(nextStatus);
      setStatusError(null);
    } catch (statusLoadError) {
      setStatusError(
        statusLoadError instanceof Error
          ? statusLoadError.message
          : "Unable to load knowledge base status."
      );
    }
  }

  useEffect(() => {
    void loadStatus();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = input.trim();
    if (!question || isLoading) {
      return;
    }

    const nextMessages: ConversationEntry[] = [...messages, { role: "user", content: question }];
    setMessages(nextMessages);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendQuestion(question, history);
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          grounded: response.grounded
        }
      ]);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "The assistant could not process your request."
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleReindex() {
    if (!IS_DEV || isReindexing) {
      return;
    }

    setIsReindexing(true);
    setStatusError(null);
    try {
      await triggerReindex();
      await loadStatus();
    } catch (reindexError) {
      setStatusError(
        reindexError instanceof Error ? reindexError.message : "Unable to reindex documents."
      );
    } finally {
      setIsReindexing(false);
    }
  }

  return (
    <div className="min-h-screen bg-app-shell text-ink">
      <div className="mx-auto grid min-h-screen max-w-[1600px] grid-cols-1 lg:grid-cols-[292px_minmax(0,1fr)]">
        <aside className="border-b border-line/80 bg-panel px-6 py-8 text-black lg:border-b-0 lg:border-r">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-line/80 bg-white">
              <SearchCheck className="h-5 w-5 text-accent-500" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-navy-500">
                myhr-ai
              </p>
              <h1 className="mt-1 text-xl font-semibold tracking-tight text-navy-950">
                HR Policy Assistant
              </h1>
            </div>
          </div>

          <SidebarStatusCard
            isDev={IS_DEV}
            isReindexing={isReindexing}
            onReindex={handleReindex}
            status={status}
            statusError={statusError}
          />

          <section className="mt-6 rounded-[28px] border border-line/80 bg-white p-5 shadow-[0_8px_24px_rgba(14,30,56,0.05)]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-navy-500">
              Suggested Questions
            </p>
            <div className="mt-4 space-y-3">
              {SAMPLE_QUESTIONS.map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => setInput(question)}
                  className="w-full rounded-2xl border border-line/80 bg-panel px-4 py-3 text-left text-sm leading-6 text-navy-900 transition hover:bg-white"
                >
                  {question}
                </button>
              ))}
            </div>
          </section>
        </aside>

        <section className="flex min-h-screen flex-col">
          <header className="sticky top-0 z-10 border-b border-line/80 bg-white/96 px-5 py-5 backdrop-blur md:px-8">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-accent-500">
                  Enterprise HR Policy Q&A
                </p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-navy-950">
                  Ask grounded questions about your indexed HR policy documents
                </h2>
              </div>
              <div className="hidden items-center gap-2 rounded-full border border-line bg-panel px-4 py-2 text-sm text-navy-700 md:flex">
                <ShieldCheck className="h-4 w-4 text-accent-500" />
                Citations on every supported answer
              </div>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto px-5 pb-40 pt-6 md:px-8">
            {error ? (
              <div className="mx-auto mb-6 max-w-4xl rounded-2xl border border-accent-500/20 bg-accent-500/8 px-4 py-3 text-sm text-accent-700">
                {error}
              </div>
            ) : null}

            {messages.length === 0 ? (
              <div className="mx-auto max-w-4xl rounded-[32px] border border-line/80 bg-white px-8 py-10 shadow-card">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-navy-500">
                  Ready To Help
                </p>
                <h3 className="mt-3 max-w-3xl text-4xl font-semibold leading-tight tracking-tight text-navy-950">
                  Search your HR policy knowledge base with source-backed answers and page citations.
                </h3>
                <p className="mt-4 max-w-2xl text-base leading-7 text-navy-700">
                  Use the questions below to begin. The assistant answers only from indexed policy
                  documents and clearly flags unsupported responses.
                </p>
                <div className="mt-8 grid gap-4 md:grid-cols-2">
                  {SAMPLE_QUESTIONS.map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => setInput(question)}
                      className="rounded-[24px] border border-line/80 bg-panel px-5 py-5 text-left text-sm leading-6 text-navy-900 transition hover:border-navy-200 hover:bg-white"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="mx-auto flex max-w-4xl flex-col gap-6">
                {messages.map((message, index) => (
                  <ChatMessageCard key={`${message.role}-${index}`} message={message} />
                ))}

                {isLoading ? (
                  <div className="max-w-[92%] rounded-[28px] border border-line/80 bg-white px-5 py-4 shadow-[0_12px_30px_rgba(14,30,56,0.06)]">
                    <div className="flex items-center gap-3 text-sm text-navy-700">
                      <LoaderCircle className="h-4 w-4 animate-spin text-accent-500" />
                      Searching the knowledge base and drafting a grounded response...
                    </div>
                  </div>
                ) : null}
              </div>
            )}
          </div>

          <div className="fixed bottom-0 left-0 right-0 border-t border-line/80 bg-white/98 px-4 py-4 backdrop-blur lg:left-[292px]">
            <form onSubmit={handleSubmit} className="mx-auto max-w-4xl">
              <div className="rounded-[30px] border border-line/80 bg-white px-4 py-4 shadow-[0_18px_40px_rgba(14,30,56,0.08)]">
                <div className="flex items-end gap-3">
                  <div className="flex-1 rounded-[24px] bg-panel px-4 py-3">
                    <label htmlFor="question" className="sr-only">
                      Ask a question about the HR policy
                    </label>
                    <textarea
                      id="question"
                      value={input}
                      onChange={(event) => setInput(event.target.value)}
                      placeholder="Ask a question about PTO, leave, holidays, or any indexed HR policy topic..."
                      rows={3}
                      className="h-24 w-full resize-none bg-transparent text-sm leading-6 text-ink outline-none placeholder:text-navy-500"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-accent-500 text-white transition hover:bg-accent-600 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <ArrowUp className="h-5 w-5" />
                  </button>
                </div>
                <div className="mt-3 flex flex-col gap-2 text-[11px] uppercase tracking-[0.18em] text-navy-500 md:flex-row md:items-center md:justify-between">
                  <span>Knowledge base documents: {status?.discovered_documents.length ?? 0}</span>
                  <span>
                    {status?.indexing_status
                      ? `Index status: ${status.indexing_status}`
                      : "Index status: loading"}
                  </span>
                </div>
              </div>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}

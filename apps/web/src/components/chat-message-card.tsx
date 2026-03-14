"use client";

import { FileText } from "lucide-react";

import { ConversationEntry } from "@/types/chat";

interface ChatMessageCardProps {
  message: ConversationEntry;
}

export function ChatMessageCard({ message }: ChatMessageCardProps) {
  const isAssistant = message.role === "assistant";

  return (
    <article className={`space-y-3 ${isAssistant ? "max-w-[92%]" : "ml-auto max-w-[78%]"}`}>
      <div
        className={`rounded-[28px] px-5 py-4 text-sm leading-7 shadow-sm ${
          isAssistant
            ? "border border-line/90 bg-white text-ink shadow-[0_12px_30px_rgba(14,30,56,0.06)]"
            : "bg-navy-900 text-white shadow-[0_14px_28px_rgba(8,24,45,0.2)]"
        }`}
      >
        {isAssistant ? (
          <div className="mb-3 flex items-center justify-between gap-3">
            <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-navy-500">
              Assistant
            </span>
            <GroundedBadge grounded={message.grounded ?? false} />
          </div>
        ) : (
          <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.22em] text-white/70">
            You
          </div>
        )}
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>

      {isAssistant ? (
        <div className="rounded-[24px] border border-line/80 bg-panel px-5 py-4">
          <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-navy-500">
            <FileText className="h-4 w-4 text-accent-500" />
            Citations
          </div>
          {message.citations && message.citations.length > 0 ? (
            <div className="mt-3 space-y-3">
              {message.citations.map((citation) => (
                <div
                  key={citation.chunk_id}
                  className="rounded-[20px] border border-line/80 bg-white px-4 py-3 shadow-[0_6px_16px_rgba(14,30,56,0.04)]"
                >
                  <p className="text-sm font-semibold text-navy-900">
                    {citation.document_name} · page {citation.page_number}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-navy-700">{citation.excerpt}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm text-navy-700">
              No citations were returned because the answer was not grounded in the indexed policy.
            </p>
          )}
        </div>
      ) : null}
    </article>
  );
}

interface GroundedBadgeProps {
  grounded: boolean;
}

function GroundedBadge({ grounded }: GroundedBadgeProps) {
  return (
    <span
      className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${
        grounded
          ? "bg-navy-50 text-navy-700 ring-1 ring-inset ring-navy-100"
          : "bg-accent-500/10 text-accent-600 ring-1 ring-inset ring-accent-500/20"
      }`}
    >
      {grounded ? "Grounded" : "Not grounded"}
    </span>
  );
}

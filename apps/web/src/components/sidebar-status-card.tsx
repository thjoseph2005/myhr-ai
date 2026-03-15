"use client";

import { Database, FolderOpen, LoaderCircle, RefreshCcw } from "lucide-react";

import { DocumentStatus } from "@/types/chat";

interface SidebarStatusCardProps {
  isDev: boolean;
  isReindexing: boolean;
  onReindex: () => void;
  status: DocumentStatus | null;
  statusError: string | null;
}

export function SidebarStatusCard({
  isDev,
  isReindexing,
  onReindex,
  status,
  statusError
}: SidebarStatusCardProps) {
  return (
    <section className="mt-8 rounded-[28px] border border-white/10 bg-white/[0.04] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-navy-200">
            Knowledge Base
          </p>
          <p className="mt-3 text-sm leading-6 text-navy-50/90">
            Repository-managed policy PDFs are indexed for grounded answers.
          </p>
        </div>
        <div className="rounded-2xl bg-white/10 p-2">
          <Database className="h-4 w-4 text-accent-500" />
        </div>
      </div>

      <div className="mt-5 space-y-3">
        <StatusRow label="Documents" value={String(status?.discovered_documents.length ?? 0)} />
        <StatusRow label="Index status" value={status?.indexing_status ?? "loading"} />
        <StatusRow label="Runtime" value={status?.azure_enabled ? "Azure" : "Mock"} />
      </div>

      <div className="mt-5 rounded-2xl border border-white/10 bg-black/10 px-4 py-3">
        <div className="flex items-start gap-3">
          <FolderOpen className="mt-0.5 h-4 w-4 text-navy-200" />
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-navy-200">
              Source Folder
            </p>
            <p className="mt-1 break-all text-xs leading-5 text-navy-100/80">
              {status?.knowledge_base_path ?? "Loading..."}
            </p>
          </div>
        </div>
      </div>

      {isDev ? (
        <button
          type="button"
          onClick={onReindex}
          disabled={isReindexing}
          className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white px-4 py-3 text-sm font-semibold text-navy-950 transition hover:bg-navy-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isReindexing ? (
            <LoaderCircle className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCcw className="h-4 w-4" />
          )}
          Reindex documents
        </button>
      ) : null}

      {status?.last_indexed_at ? (
        <p className="mt-4 text-xs leading-5 text-navy-200/85">
          Last indexed {new Date(status.last_indexed_at).toLocaleString()}
        </p>
      ) : null}

      {statusError ? <p className="mt-4 text-sm text-accent-500">{statusError}</p> : null}
    </section>
  );
}

interface StatusRowProps {
  label: string;
  value: string;
}

function StatusRow({ label, value }: StatusRowProps) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm">
      <span className="text-navy-100/80">{label}</span>
      <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-white">
        {value}
      </span>
    </div>
  );
}

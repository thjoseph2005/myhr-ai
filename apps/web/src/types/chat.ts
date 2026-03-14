export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface ConversationEntry extends ChatMessage {
  citations?: Citation[];
  grounded?: boolean;
}

export interface Citation {
  document_name: string;
  page_number: number;
  chunk_id: string;
  excerpt: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  grounded: boolean;
}

export interface DocumentInfo {
  document_id: string;
  document_name: string;
  path: string;
}

export interface DocumentStatus {
  knowledge_base_path: string;
  discovered_documents: DocumentInfo[];
  indexing_status: string;
  last_indexed_at: string | null;
  indexed_document_count: number;
  azure_enabled: boolean;
}

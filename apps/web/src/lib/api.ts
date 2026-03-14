import { ChatMessage, ChatResponse, DocumentStatus } from "@/types/chat";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function sendQuestion(
  question: string,
  history: ChatMessage[]
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      question,
      history
    }),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("The assistant is temporarily unavailable.");
  }

  return (await response.json()) as ChatResponse;
}

export async function fetchDocumentStatus(): Promise<DocumentStatus> {
  const response = await fetch(`${API_BASE_URL}/api/documents/status`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Unable to load knowledge base status.");
  }

  return (await response.json()) as DocumentStatus;
}

export async function triggerReindex(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/documents/reindex`, {
    method: "POST"
  });

  if (!response.ok) {
    throw new Error("Unable to start reindexing.");
  }
}

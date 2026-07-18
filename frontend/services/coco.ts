/**
 * Coco API service (Phase 9 / Milestone 2). Built on lib/api.ts. Each call
 * needs the caller's Supabase access token for the backend JWT gate.
 */

import { apiFetch } from "@/lib/api";
import type { ChatHistoryOut, ChatOut } from "@/types/coco";

/** Send one message to Coco. A null conversation id starts a new conversation. */
export async function sendChat(
  message: string,
  conversationId: string | null,
  accessToken: string,
): Promise<ChatOut> {
  return apiFetch<ChatOut>("/coco/chat", {
    method: "POST",
    body: JSON.stringify({ message, conversation_id: conversationId }),
    accessToken,
  });
}

/** All messages of one conversation, oldest first. Unknown id → empty list. */
export async function getChatHistory(
  conversationId: string,
  accessToken: string,
): Promise<ChatHistoryOut> {
  return apiFetch<ChatHistoryOut>(
    `/coco/history?conversation_id=${encodeURIComponent(conversationId)}`,
    { accessToken },
  );
}

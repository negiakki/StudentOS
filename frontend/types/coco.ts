/**
 * Coco chat types, mirroring backend/app/schemas/coco.py (ChatIn/ChatOut/
 * ChatHistoryOut). Kept in sync by hand like the other type modules.
 */

export type ProposedAction = {
  // V1 scope: only the two writes where chat beats the UI form. Creating
  // todos/assignments went back to the forms (Docs/06 scope change).
  type: "complete_todo" | "mark_attendance";
  payload: Record<string, unknown>;
  summary: string;
};

export type ChatOut = {
  conversation_id: string;
  reply: string;
  proposed_action: ProposedAction | null;
  coco_available: boolean;
};

export type ChatHistoryMessage = {
  id: string;
  role: "USER" | "COCO";
  message: string;
  created_at: string;
};

export type ChatHistoryOut = {
  conversation_id: string;
  messages: ChatHistoryMessage[];
};

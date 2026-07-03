import type { FactoryJobEvent } from '../services/agentFactoryService';

const BOILERPLATE_REPLIES = new Set([
  'orchestrator cli finished',
  'open chat completed',
  'orchestrator reply',
]);

export function isBoilerplateReply(text: string): boolean {
  const lower = text.trim().toLowerCase();
  if (!lower || BOILERPLATE_REPLIES.has(lower)) return true;
  if (lower.startsWith('orchestrator cli started')) return true;
  if (lower.startsWith('bridge completed')) return true;
  return false;
}

export function isSystemStatusMessage(text: string): boolean {
  const lower = text.trim().toLowerCase();
  if (!lower || isBoilerplateReply(text)) return true;
  if (lower.startsWith('job queued:')) return true;
  if (lower.startsWith('job accepted')) return true;
  if (lower.startsWith('open chat:')) return true;
  if (lower.includes('initializing agent')) return true;
  if (lower.startsWith('query:')) return true;
  return false;
}

function looksLikeVerboseCliDump(text: string): boolean {
  const lower = text.toLowerCase();
  return (
    lower.includes('initializing agent') ||
    lower.startsWith('query:') ||
    (text.includes('{') && text.includes('"status"') && !extractJsonSummaryOnly(text))
  );
}

function normalizeSummaryText(text: string): string {
  return text.replace(/\s+/g, ' ').trim();
}

export function cleanHermesResumeSession(value: unknown): string | null {
  if (value == null) return null;
  const session = String(value).trim();
  if (!session || ['none', 'null', 'undefined'].includes(session.toLowerCase())) {
    return null;
  }
  return session;
}

function hermesCliReply(raw: string): string | null {
  const stripped = raw.trim();
  if (!stripped) return null;

  const lines: string[] = [];
  for (const line of stripped.split('\n')) {
    const ln = line.trim();
    if (!ln) continue;
    const lower = ln.toLowerCase();
    if (lower.startsWith('query:')) continue;
    if (lower === 'initializing agent...') continue;
    if (lower.startsWith('goodbye')) continue;
    lines.push(ln);
  }

  if (!lines.length) return null;

  const message = lines.join(' ');
  const lower = message.toLowerCase();
  if (
    lower.includes('session not found') ||
    lower.includes('error:') ||
    lower.includes('failed') ||
    lower.includes('unavailable') ||
    lower.includes('could not')
  ) {
    return message;
  }
  return null;
}

export function extractJsonSummaryOnly(raw: string | null | undefined): string | null {
  if (!raw?.trim()) return null;
  const trimmed = raw.trim();

  const candidates = [trimmed];
  const firstBrace = trimmed.indexOf('{');
  const lastBrace = trimmed.lastIndexOf('}');
  if (firstBrace >= 0 && lastBrace > firstBrace) {
    candidates.push(trimmed.slice(firstBrace, lastBrace + 1));
  }

  for (const candidate of candidates) {
    try {
      const parsed = JSON.parse(candidate) as { summary?: unknown };
      if (typeof parsed.summary === 'string' && parsed.summary.trim()) {
        return normalizeSummaryText(parsed.summary);
      }
    } catch {
      // Hermes CLI often pretty-prints JSON with line breaks inside string values.
    }
  }

  const summaryMatch = trimmed.match(/"summary"\s*:\s*"([\s\S]*?)"\s*,/);
  if (summaryMatch?.[1]) {
    return normalizeSummaryText(summaryMatch[1]);
  }

  return null;
}

function extractAssistantReplyFromEvent(ev: FactoryJobEvent): string | null {
  const turns = ev.llm_turns;
  if (!Array.isArray(turns)) return null;
  for (let i = turns.length - 1; i >= 0; i -= 1) {
    const turn = turns[i] as Record<string, unknown>;
    if (turn?.role === 'assistant' && typeof turn.content === 'string' && turn.content.trim()) {
      return turn.content.trim();
    }
  }
  return null;
}

export function extractChatReplyFromJob(
  events: FactoryJobEvent[],
  orchestratorReply: string | null,
): string | null {
  for (let i = events.length - 1; i >= 0; i -= 1) {
    const ev = events[i];
    const fromTurns = extractAssistantReplyFromEvent(ev);
    if (!fromTurns) continue;

    const jsonSummary = extractJsonSummaryOnly(fromTurns);
    if (jsonSummary) return jsonSummary;

    const cliReply = hermesCliReply(fromTurns);
    if (cliReply) return cliReply;

    const profile = (ev.profile || '').toLowerCase();
    if (
      ev.event_type === 'delegate_complete' &&
      profile.includes('orchestrator') &&
      !isSystemStatusMessage(fromTurns) &&
      !looksLikeVerboseCliDump(fromTurns)
    ) {
      return fromTurns;
    }
  }

  for (let i = events.length - 1; i >= 0; i -= 1) {
    const payloadSummary = events[i].payload_summary?.summary;
    if (typeof payloadSummary === 'string' && payloadSummary.trim()) {
      return payloadSummary.trim();
    }
  }

  const apiReply = orchestratorReply?.trim();
  if (!apiReply || isSystemStatusMessage(apiReply)) return null;

  const jsonSummary = extractJsonSummaryOnly(apiReply);
  if (jsonSummary) return jsonSummary;

  const cliReply = hermesCliReply(apiReply);
  if (cliReply) return cliReply;

  if (!looksLikeVerboseCliDump(apiReply) && !apiReply.includes('{')) {
    return apiReply;
  }

  return null;
}

export function extractHermesResumeSession(events: FactoryJobEvent[]): string | null {
  for (let i = events.length - 1; i >= 0; i -= 1) {
    const fromPayload = cleanHermesResumeSession(events[i].payload_summary?.hermes_resume_session);
    if (fromPayload) return fromPayload;
    const fromTurns = extractAssistantReplyFromEvent(events[i]);
    if (fromTurns) {
      const sessionMatch =
        fromTurns.match(/Session:\s*(\S+)/) ?? fromTurns.match(/hermes --resume (\S+)/);
      if (sessionMatch?.[1]) return sessionMatch[1].trim();
    }
  }
  return null;
}

export function getMonitorMessage(ev: FactoryJobEvent): string {
  const assistantReply = extractAssistantReplyFromEvent(ev);
  if (assistantReply) {
    const summary = extractJsonSummaryOnly(assistantReply);
    if (summary) return summary;
    if (!isBoilerplateReply(assistantReply) && !isSystemStatusMessage(assistantReply)) {
      return assistantReply;
    }
  }
  const fromMessage = extractJsonSummaryOnly(ev.message);
  if (fromMessage) return fromMessage;
  return ev.message || ev.event_type;
}

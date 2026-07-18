/**
 * Tiny markdown renderer for Coco replies. Builds React elements directly
 * (no HTML injection). Covers what chat replies actually use: paragraphs,
 * **bold**, *italic*, `code`, and -/* or 1. lists.
 */
// ponytail: regex-based subset, swap for react-markdown if replies outgrow it.

import type { ReactNode } from "react";

/** Inline: `code`, **bold**, *italic*. */
function renderInline(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const re = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("`")) {
      parts.push(
        <code
          key={key++}
          className="rounded bg-neutral-100 px-1 py-0.5 font-mono text-[0.85em] dark:bg-neutral-800"
        >
          {tok.slice(1, -1)}
        </code>,
      );
    } else if (tok.startsWith("**")) {
      parts.push(<strong key={key++}>{tok.slice(2, -2)}</strong>);
    } else {
      parts.push(<em key={key++}>{tok.slice(1, -1)}</em>);
    }
    last = m.index + tok.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

/** Block: paragraphs separated by blank lines; contiguous list lines become lists. */
export function Markdown({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="space-y-2">
      {blocks.map((block, i) => {
        const lines = block.split("\n").filter((l) => l.trim() !== "");
        const isUl = lines.length > 0 && lines.every((l) => /^\s*[-*]\s+/.test(l));
        const isOl = lines.length > 0 && lines.every((l) => /^\s*\d+[.)]\s+/.test(l));
        if (isUl || isOl) {
          const items = lines.map((l, j) => (
            <li key={j}>{renderInline(l.replace(/^\s*(?:[-*]|\d+[.)])\s+/, ""))}</li>
          ));
          return isUl ? (
            <ul key={i} className="list-disc space-y-1 pl-4">
              {items}
            </ul>
          ) : (
            <ol key={i} className="list-decimal space-y-1 pl-4">
              {items}
            </ol>
          );
        }
        return (
          <p key={i} className="whitespace-pre-wrap">
            {renderInline(block)}
          </p>
        );
      })}
    </div>
  );
}

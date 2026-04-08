import { useState } from "react";

export interface Citation {
  doc_name: string;
  section: string;
  url: string;
  chunk_text: string;
  last_updated: string;
}

interface Props {
  citation: Citation;
  index: number;
}

export default function CitationCard({ citation, index }: Props) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-gray-200 rounded-lg text-xs bg-gray-50 overflow-hidden">
      <button
        onClick={() => setExpanded((prev) => !prev)}
        className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-gray-100 transition-colors"
        aria-expanded={expanded}
        aria-label={`Source ${index + 1}: ${citation.doc_name}`}
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="shrink-0 w-5 h-5 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-medium text-[10px]">
            {index + 1}
          </span>
          <div className="min-w-0">
            <span className="font-medium text-gray-700 truncate block">{citation.doc_name}</span>
            {citation.section && (
              <span className="text-gray-500 truncate block">{citation.section}</span>
            )}
          </div>
        </div>
        <span className="text-gray-400 ml-2">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="px-3 pb-3 border-t border-gray-200">
          <p className="mt-2 text-gray-600 leading-relaxed line-clamp-6">{citation.chunk_text}</p>
          <div className="mt-2 flex items-center justify-between gap-2 text-gray-400">
            {citation.last_updated && <span>Updated: {citation.last_updated}</span>}
            {citation.url && (
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-600 hover:underline"
                aria-label={`Open source document: ${citation.doc_name}`}
              >
                View source →
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

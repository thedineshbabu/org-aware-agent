import CitationCard, { type Citation } from "./CitationCard";

interface Props {
  citations: Citation[];
}

export default function CitationList({ citations }: Props) {
  if (citations.length === 0) return null;

  return (
    <div className="w-full space-y-1" aria-label="Source citations">
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Sources</p>
      {citations.map((citation, index) => (
        <CitationCard key={`${citation.doc_name}-${index}`} citation={citation} index={index} />
      ))}
    </div>
  );
}

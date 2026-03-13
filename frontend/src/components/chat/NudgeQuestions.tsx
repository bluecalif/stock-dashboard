import { useState, useEffect } from "react";
import { fetchNudgeQuestions } from "../../api/chat";

interface Props {
  pageId: string;
  onSelect: (question: string) => void;
}

export default function NudgeQuestions({ pageId, onSelect }: Props) {
  const [questions, setQuestions] = useState<string[]>([]);

  useEffect(() => {
    fetchNudgeQuestions(pageId)
      .then(setQuestions)
      .catch(() => setQuestions([]));
  }, [pageId]);

  if (questions.length === 0) return null;

  return (
    <div className="px-4 py-3 space-y-2">
      <p className="text-xs text-gray-400">이런 질문은 어떠세요?</p>
      <div className="flex flex-wrap gap-1.5">
        {questions.map((q, i) => (
          <button
            key={i}
            onClick={() => onSelect(q)}
            className="text-xs text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-full px-3 py-1.5 transition-colors text-left"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

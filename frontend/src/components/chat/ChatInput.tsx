import { useState, useRef, useCallback } from "react";

interface Props {
  onSend: (content: string) => void;
  disabled: boolean;
  deepMode: boolean;
  onToggleDeepMode: () => void;
}

export default function ChatInput({ onSend, disabled, deepMode, onToggleDeepMode }: Props) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [text, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-200 p-3 bg-white">
      <div className="flex items-center gap-2 mb-2">
        <button
          type="button"
          onClick={onToggleDeepMode}
          className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors
            ${deepMode
              ? "bg-purple-100 text-purple-700 border border-purple-300"
              : "bg-gray-100 text-gray-500 border border-gray-200 hover:bg-gray-200"
            }`}
        >
          <span className={`inline-block w-2 h-2 rounded-full ${deepMode ? "bg-purple-500" : "bg-gray-400"}`} />
          심층모드
        </button>
        <span className="text-xs text-gray-400">
          {deepMode ? "GPT-5 (정밀 분석)" : "GPT-5 Mini (빠른 응답)"}
        </span>
      </div>
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            e.target.style.height = "auto";
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
          }}
          onKeyDown={handleKeyDown}
          placeholder="메시지를 입력하세요..."
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm
            focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50
            max-h-[120px]"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white
            hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors"
        >
          전송
        </button>
      </div>
    </div>
  );
}

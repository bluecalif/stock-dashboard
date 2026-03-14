import { useCallback, useRef } from "react";
import type { SSEEvent, UIAction } from "../types/chat";

interface UseSSECallbacks {
  onTextDelta?: (content: string) => void;
  onToolCall?: (name: string, args: Record<string, unknown>) => void;
  onToolResult?: (name: string, data: unknown) => void;
  onUIAction?: (action: UIAction) => void;
  onStatus?: (step: string, message: string) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
}

/**
 * fetch + ReadableStream 기반 SSE 파싱 훅.
 * POST 메서드를 지원하며, EventSource 대신 사용.
 */
export function useSSE() {
  const abortRef = useRef<(() => void) | null>(null);

  const startStream = useCallback(
    async (
      fetchResponse: Promise<Response>,
      abort: () => void,
      callbacks: UseSSECallbacks,
    ) => {
      abortRef.current = abort;

      try {
        const res = await fetchResponse;
        if (!res.ok) {
          callbacks.onError?.(`HTTP ${res.status}`);
          return;
        }

        const reader = res.body?.getReader();
        if (!reader) {
          callbacks.onError?.("No response body");
          return;
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;

            try {
              const event: SSEEvent = JSON.parse(jsonStr);

              switch (event.type) {
                case "text_delta":
                  callbacks.onTextDelta?.(event.content || "");
                  break;
                case "tool_call":
                  callbacks.onToolCall?.(event.name || "", event.args || {});
                  break;
                case "tool_result":
                  callbacks.onToolResult?.(event.name || "", event.data);
                  break;
                case "ui_action":
                  if (event.action) {
                    callbacks.onUIAction?.({
                      action: event.action as UIAction["action"],
                      payload: event.payload || {},
                    });
                  }
                  break;
                case "status": {
                  const d = event.data as { step?: string; message?: string } | undefined;
                  callbacks.onStatus?.(d?.step || "", d?.message || "");
                  break;
                }
                case "done":
                  callbacks.onDone?.();
                  break;
                case "error":
                  callbacks.onError?.(event.content || "Unknown error");
                  break;
              }
            } catch {
              // JSON parse 실패 무시
            }
          }
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        callbacks.onError?.(err instanceof Error ? err.message : "Stream error");
      } finally {
        abortRef.current = null;
      }
    },
    [],
  );

  const stopStream = useCallback(() => {
    abortRef.current?.();
    abortRef.current = null;
  }, []);

  return { startStream, stopStream };
}

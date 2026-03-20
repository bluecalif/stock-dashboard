import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import ChatPanel from "../chat/ChatPanel";
import PageGuide from "../onboarding/PageGuide";
import { useChatStore } from "../../store/chatStore";
import { usePageTracking } from "../../hooks/usePageTracking";

export default function Layout() {
  usePageTracking();
  const togglePanel = useChatStore((s) => s.togglePanel);
  const isPanelOpen = useChatStore((s) => s.isPanelOpen);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>

      {/* Chat toggle button */}
      <button
        onClick={togglePanel}
        className={`fixed bottom-6 right-6 z-40 rounded-full w-14 h-14 shadow-lg
          flex items-center justify-center text-2xl transition-colors
          ${isPanelOpen ? "bg-gray-600 text-white" : "bg-blue-600 text-white hover:bg-blue-700"}`}
        title="AI 분석 도우미"
      >
        💬
      </button>

      <ChatPanel />
      <PageGuide />
    </div>
  );
}

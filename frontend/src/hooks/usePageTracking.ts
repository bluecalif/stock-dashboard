import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { recordPageVisit } from "../api/profile";
import { useAuthStore } from "../store/authStore";

const PATH_TO_PAGE_ID: Record<string, string> = {
  "/": "home",
  "/prices": "prices",
  "/correlation": "correlation",
  "/indicators": "indicators",
  "/strategy": "strategy",
};

export function usePageTracking() {
  const { pathname } = useLocation();
  const accessToken = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    if (!accessToken) return;
    const pageId = PATH_TO_PAGE_ID[pathname];
    if (!pageId) return;

    recordPageVisit({ page_id: pageId }).catch(() => {
      // 실패 무시 — 핵심 기능 아님
    });
  }, [pathname, accessToken]);
}

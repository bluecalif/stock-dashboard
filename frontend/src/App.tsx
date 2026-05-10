import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import SilverLayout from "./pages/silver/components/SilverLayout";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import IceBreakingModal from "./components/onboarding/IceBreakingModal";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import CompareMainPage from "./pages/silver/CompareMainPage";
import SignalDetailPage from "./pages/silver/SignalDetailPage";
import { useAuthStore } from "./store/authStore";
import { useProfileStore } from "./store/profileStore";

export default function App() {
  const loadUser = useAuthStore((s) => s.loadUser);
  const accessToken = useAuthStore((s) => s.accessToken);
  const loadProfile = useProfileStore((s) => s.loadProfile);
  const profile = useProfileStore((s) => s.profile);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    if (accessToken) {
      loadProfile();
    }
  }, [accessToken, loadProfile]);

  const showIceBreaking = !!accessToken && profile !== null && !profile.onboarding_completed;

  return (
    <BrowserRouter>
      {showIceBreaking && <IceBreakingModal />}
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        <Route element={<ProtectedRoute />}>
          {/* ── Silver 페이지 (SilverLayout: 상단 가로 nav) ── */}
          <Route element={<SilverLayout />}>
            <Route path="silver/compare" element={<CompareMainPage />} />
            <Route path="silver/signals" element={<SignalDetailPage />} />
          </Route>

          {/* ── Bronze → Silver redirect ── */}
          <Route index element={<Navigate to="/silver/compare" replace />} />
          <Route path="dashboard" element={<Navigate to="/silver/compare" replace />} />
          <Route path="prices" element={<Navigate to="/silver/compare" replace />} />
          <Route path="correlation" element={<Navigate to="/silver/compare" replace />} />
          <Route path="indicators" element={<Navigate to="/silver/compare" replace />} />
          <Route path="factors" element={<Navigate to="/silver/compare" replace />} />
          <Route path="signals" element={<Navigate to="/silver/compare" replace />} />
          <Route path="strategy" element={<Navigate to="/silver/compare" replace />} />

        </Route>
      </Routes>
    </BrowserRouter>
  );
}

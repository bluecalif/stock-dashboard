import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/layout/Layout";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import DashboardPage from "./pages/DashboardPage";
import PricePage from "./pages/PricePage";
import CorrelationPage from "./pages/CorrelationPage";
import IndicatorSignalPage from "./pages/IndicatorSignalPage";
import StrategyPage from "./pages/StrategyPage";
import { useAuthStore } from "./store/authStore";

export default function App() {
  const loadUser = useAuthStore((s) => s.loadUser);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="prices" element={<PricePage />} />
            <Route path="correlation" element={<CorrelationPage />} />
            <Route path="indicators" element={<IndicatorSignalPage />} />
            <Route path="factors" element={<Navigate to="/indicators" replace />} />
            <Route path="signals" element={<Navigate to="/indicators" replace />} />
            <Route path="strategy" element={<StrategyPage />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

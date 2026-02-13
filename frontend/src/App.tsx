import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";
import DashboardPage from "./pages/DashboardPage";
import PricePage from "./pages/PricePage";
import CorrelationPage from "./pages/CorrelationPage";
import FactorPage from "./pages/FactorPage";
import SignalPage from "./pages/SignalPage";
import StrategyPage from "./pages/StrategyPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="prices" element={<PricePage />} />
          <Route path="correlation" element={<CorrelationPage />} />
          <Route path="factors" element={<FactorPage />} />
          <Route path="signals" element={<SignalPage />} />
          <Route path="strategy" element={<StrategyPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

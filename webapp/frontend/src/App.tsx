import { Route, Routes, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { useWS } from "./lib/ws";
import { useBootstrapData } from "./lib/useBootstrapData";
import { Dashboard } from "./routes/Dashboard";
import { Trading } from "./routes/Trading";
import { TradingDesk } from "./routes/TradingDesk";
import { Analysis } from "./routes/Analysis";
import { AIAdvisor } from "./routes/AIAdvisor";
import { Strategy } from "./routes/Strategy";
import { Learning } from "./routes/Learning";
import { LearningChapter } from "./routes/LearningChapter";
import { Glossary } from "./routes/Glossary";
import { Portfolio } from "./routes/Portfolio";
import { Journal } from "./routes/Journal";
import { Onboarding } from "./features/Onboarding";
import { Logs } from "./routes/Logs";
import { Settings } from "./routes/Settings";

export default function App() {
  const onboardingDone = localStorage.getItem("onboarding_completed") === "1";

  return (
    <>
      {!onboardingDone ? <OnboardingRedirect /> : <AppContent />}
    </>
  );
}

function OnboardingRedirect() {
  const navigate = useNavigate();
  return <Onboarding onDone={() => { navigate("/learning"); }} />;
}

function AppContent() {
  useWS();
  useBootstrapData();
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg text-fg">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-4 lg:p-6 xl:p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/advisor" element={<AIAdvisor />} />
            <Route path="/trading" element={<Trading />} />
            <Route path="/desk" element={<TradingDesk />} />
            <Route path="/learning" element={<Learning />} />
            <Route path="/learning/:chapterId" element={<LearningChapter />} />
            <Route path="/glossary" element={<Glossary />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/strategy" element={<Strategy />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/journal" element={<Journal />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

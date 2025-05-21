
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import MainLayout from "./components/layout/MainLayout";
import ActionsPage from "./pages/ActionsPage"; // Renamed from ActivityPage
import TasksPage from "./pages/TasksPage";
import ContactsPage from "./pages/ContactsPage";
import CalendarPage from "./pages/CalendarPage";
import ReportsPage from "./pages/ReportsPage";
import DatabasePage from "./pages/DatabasePage"; // Renamed from KnowledgePage
import ChatPage from "./pages/ChatPage";
import ConfigurationPage from "./pages/ConfigurationPage"; // Renamed from SettingsPage
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <MainLayout>
          <Routes>
            <Route path="/" element={<ActionsPage />} /> {/* Changed from ActivityPage */}
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/contacts" element={<ContactsPage />} />
            <Route path="/calendar" element={<CalendarPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/database" element={<DatabasePage />} /> {/* New route for Database */}
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/configuration" element={<ConfigurationPage />} /> {/* New route for Configuration */}
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </MainLayout>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;

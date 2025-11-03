// src/App.tsx
// (Arquivo ajustado, entregando completo conforme solicitado)

import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import NotFound from "./pages/NotFound";

// --- NOSSAS NOVAS IMPORTAÇÕES ---
import { AuthProvider } from "@/context/AuthContext";
import Login from "./pages/Login";
import ProtectedRoute from "@/components/ProtectedRoute";
import AdminRoute from "@/components/AdminRoute"; // <-- 1. IMPORTAR O ADMINROUTE
import Configuracoes from "./pages/Configuracoes"; // <-- 2. IMPORTAR A NOVA PÁGINA
// --- FIM DAS NOVAS IMPORTAÇÕES ---

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <AuthProvider>
        <Toaster />
        <Sonner richColors />
        <BrowserRouter>
          <Routes>
            {/* Rota de Login (Pública) */}
            <Route path="/login" element={<Login />} />

            {/* Rota Principal (Protegida por Login) */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />

            {/* 3. NOVA ROTA DE CONFIGURAÇÕES (Protegida por Admin) */}
            <Route
              path="/configuracoes"
              element={
                <AdminRoute>
                  {/* O AdminRoute vai garantir que só Admins cheguem aqui */}
                  <Configuracoes />
                </AdminRoute>
              }
            />

            {/* Rota "Não Encontrado" (Pública) */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;

import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import NotFound from "./pages/NotFound";

// --- NOSSAS NOVAS IMPORTAÇÕES ---
// O "Cérebro" do Login
import { AuthProvider } from "@/context/AuthContext";
// A "Porta" de entrada
import Login from "./pages/Login";
// O "Segurança"
import ProtectedRoute from "@/components/ProtectedRoute";
// --- FIM DAS NOVAS IMPORTAÇÕES ---

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      {/* 1. O AuthProvider (Cérebro) abraça tudo.
           Agora todo o App sabe quem está logado.
      */}
      <AuthProvider>
        <Toaster />
        <Sonner richColors /> {/* Mantive seus Toasters */}
        <BrowserRouter>
          <Routes>
            {/* 2. Rota de Login (Pública)
                 Qualquer um pode acessar /login
            */}
            <Route path="/login" element={<Login />} />

            {/* 3. Rota Principal (Protegida)
                 Só pode acessar "/" quem estiver logado (passar pelo ProtectedRoute)
            */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
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

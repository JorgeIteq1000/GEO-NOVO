// src/components/AdminRoute.tsx
// (Novo arquivo completo)

import { ReactNode } from "react";
import { useAuth } from "@/context/AuthContext";
import { Navigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

interface AdminRouteProps {
  children: ReactNode;
}

export default function AdminRoute({ children }: AdminRouteProps) {
  const { user, isLoading } = useAuth();
  console.log("[AdminRoute] Verificando acesso...");

  if (isLoading) {
    console.log("[AdminRoute] Carregando autenticação...");
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    console.log("[AdminRoute] Usuário não logado. Redirecionando para /login.");
    // Usuário não está logado, redireciona para o login
    return <Navigate to="/login" replace />;
  }

  if (user.role !== "Admin") {
    console.warn("[AdminRoute] Acesso negado. Usuário não é Admin.");
    // Usuário está logado, mas NÃO é Admin
    // Redireciona para o Dashboard e mostra um aviso
    toast.error("Acesso Negado", {
      description: "Você não tem permissão para acessar esta página.",
    });
    return <Navigate to="/" replace />;
  }

  console.log("[AdminRoute] Acesso de Admin concedido.");
  // Usuário logado E é Admin
  return <>{children}</>;
}

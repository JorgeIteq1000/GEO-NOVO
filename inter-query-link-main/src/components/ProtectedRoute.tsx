import { useAuth } from "@/context/AuthContext";
import { Navigate, useLocation } from "react-router-dom";
import { Loader2 } from "lucide-react";

// Este componente "tranca" uma página
export default function ProtectedRoute({
  children,
}: {
  children: JSX.Element;
}) {
  const { token, isLoading } = useAuth();
  const location = useLocation();

  // 1. Se estiver carregando o token do localStorage, mostra um spinner
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
      </div>
    );
  }

  // 2. Se terminou de carregar E não tem token, redireciona para o login
  if (!token) {
    console.log("[ProtectedRoute] Sem token, redirecionando para /login");
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 3. Se tem token, permite o acesso (renderiza o 'children', ex: o Dashboard)
  return children;
}

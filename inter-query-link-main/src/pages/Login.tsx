import { useState } from "react";
// --- MUDANÇA: Importar hooks de navegação e redirecionamento ---
import { useNavigate, useLocation, Navigate } from "react-router-dom";
// --- FIM DA MUDANÇA ---
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

export default function Login() {
  const [login, setLogin] = useState("");
  const [senha, setSenha] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const auth = useAuth();
  // --- MUDANÇA: Inicializar os hooks de navegação ---
  const navigate = useNavigate();
  const location = useLocation();
  // Pega a página de "origem" (para onde o usuário ia) ou volta para "/"
  const from = location.state?.from?.pathname || "/";
  // --- FIM DA MUDANÇA ---

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!login || !senha) {
      toast.error("Por favor, preencha o login e a senha.");
      return;
    }

    setIsLoading(true);
    console.log(`[Login] Tentando logar com: ${login}`);

    try {
      const response = await fetch("http://localhost:5000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ login, senha }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Erro desconhecido no login");
      }

      // SUCESSO!
      auth.login(data.access_token, data.user);

      // --- MUDANÇA: Forçar o redirecionamento após o login ---
      // 'replace: true' limpa o histórico de login (o usuário não pode "voltar" para o login)
      navigate(from, { replace: true });
      // --- FIM DA MUDANÇA ---
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Ocorreu um erro";
      console.error("[Login] Falha no login:", errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // --- MUDANÇA: Se o usuário já estiver logado, redireciona AGORA ---
  // Isso impede que um usuário logado acesse a página /login
  if (auth.isLoading) {
    // Se ainda estiver checando o localStorage, mostre um spinner
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
      </div>
    );
  }

  if (auth.token) {
    console.log(
      "[Login] Usuário já logado, redirecionando para o dashboard..."
    );
    return <Navigate to="/" replace />;
  }
  // --- FIM DA MUDANÇA ---

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="w-full max-w-md p-8 space-y-6 bg-card rounded-lg shadow-lg">
        <h1 className="text-2xl font-bold text-center text-foreground">
          Acessar Sistema TCA
        </h1>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="login">Login</Label>
            <Input
              id="login"
              type="text"
              placeholder="Digite seu login"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="senha">Senha</Label>
            <Input
              id="senha"
              type="password"
              placeholder="Digite sua senha"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              "Entrar"
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}

import { useState, FormEvent } from "react";
import { useAuth } from "@/context/AuthContext";
import { Navigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export default function Login() {
  const [login, setLogin] = useState("admin");
  const [senha, setSenha] = useState("admin123");
  const [isLoading, setIsLoading] = useState(false);
  const { user, login: authLogin } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    console.log(`[Login] Tentando logar com: ${login}`);

    try {
      // --- MUDANÇA AQUI ---
      // Usa a variável de ambiente para a URL da API
      const apiUrl = `${import.meta.env.VITE_API_BASE_URL}/api/login`;
      console.log(`[Login] Conectando em: ${apiUrl}`); // Log para depuração
      // --- FIM DA MUDANÇA ---

      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ login, senha }),
      });

      const data = await response.json();

      if (!response.ok) {
        console.error("[Login] Erro da API:", data.error);
        throw new Error(data.error || "Falha no login");
      }

      console.log("[Login] Login bem-sucedido, recebido:", data);
      if (data.access_token && data.user) {
        authLogin(data.access_token, data.user);
      } else {
        throw new Error("Resposta de login inválida do servidor.");
      }
    } catch (error) {
      console.error("[Login] Falha no login:", (error as Error).message, error);
      toast.error("Falha no Login", {
        description: (error as Error).message,
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (user) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader>
          <CardTitle className="text-center text-2xl font-bold">
            Sistema de Consulta GEO
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="login">Usuário</Label>
              <Input
                id="login"
                type="text"
                value={login}
                onChange={(e) => setLogin(e.target.value)}
                placeholder="Seu usuário"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="senha">Senha</Label>
              <Input
                id="senha"
                type="password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                placeholder="Sua senha"
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                "Entrar"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

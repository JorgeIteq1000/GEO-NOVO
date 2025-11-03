import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { Navigate } from "react-router-dom";
import { apiFetch } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
// import { Switch } from "@/components/ui/switch"; // (Não estamos usando o Switch, mas sim botões)
import { Loader2, PlusCircle, UserX, UserCheck } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import Sidebar from "@/components/Sidebar";

// Tipo para o objeto colaborador
interface Colaborador {
  id: number;
  nome_colaborador: string;
  login: string;
  role: "Admin" | "User";
  is_ativo: boolean;
}

export default function Configuracoes() {
  // --- MUDANÇA: Chave '}' extra removida ---
  const { user } = useAuth();
  // --- FIM DA MUDANÇA ---

  const [colaboradores, setColaboradores] = useState<Colaborador[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Estados para o formulário de novo usuário
  const [novoNome, setNovoNome] = useState("");
  const [novoLogin, setNovoLogin] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [novoRole, setNovoRole] = useState<"User" | "Admin">("User");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Função para carregar os usuários
  const fetchColaboradores = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch(
        "http://localhost:5000/api/colaboradores"
      );
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Falha ao carregar usuários");
      }
      const data = await response.json();
      setColaboradores(data);
    } catch (err) {
      if (err instanceof Error && err.message.includes("401")) {
        // O apiFetch já vai lidar com isso, mas podemos ser explícitos
        console.error("Erro de autenticação ao buscar colaboradores");
      } else {
        toast.error(err instanceof Error ? err.message : "Erro desconhecido");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Carrega os usuários ao montar a página
  useEffect(() => {
    fetchColaboradores();
  }, []);

  // Handler para criar novo usuário
  const handleCreateUser = async () => {
    if (!novoNome || !novoLogin || !novaSenha) {
      toast.error("Nome, Login e Senha são obrigatórios.");
      return;
    }
    setIsSubmitting(true);
    try {
      const response = await apiFetch(
        "http://localhost:5000/api/colaboradores",
        {
          method: "POST",
          body: JSON.stringify({
            nome: novoNome,
            login: novoLogin,
            senha: novaSenha,
            role: novoRole,
          }),
        }
      );

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Falha ao criar usuário");
      }

      toast.success("Usuário criado com sucesso!");
      setIsDialogOpen(false); // Fecha o modal
      fetchColaboradores(); // Recarrega a lista
      // Limpa o formulário
      setNovoNome("");
      setNovoLogin("");
      setNovaSenha("");
      setNovoRole("User");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handler para atualizar (bloquear/promover)
  const handleUpdateUser = async (
    colaborador: Colaborador,
    action: "toggleAtivo" | "toggleRole"
  ) => {
    let newRole = colaborador.role;
    let newIsAtivo = colaborador.is_ativo;

    if (action === "toggleAtivo") {
      newIsAtivo = !colaborador.is_ativo;
    }
    if (action === "toggleRole") {
      newRole = colaborador.role === "User" ? "Admin" : "User";
    }

    if (colaborador.login === user?.login) {
      toast.error("Você não pode alterar seu próprio acesso.");
      return;
    }

    try {
      const response = await apiFetch(
        `http://localhost:5000/api/colaboradores/${colaborador.id}`,
        {
          method: "PUT",
          body: JSON.stringify({
            role: newRole,
            is_ativo: newIsAtivo,
          }),
        }
      );

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Falha ao atualizar usuário");
      }

      toast.success("Usuário atualizado!");
      fetchColaboradores(); // Recarrega a lista
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro desconhecido");
    }
  };

  // Redireciona se não for Admin (dupla segurança)
  // Verifica *após* o loading inicial do auth
  if (!user && !isLoading) {
    return <Navigate to="/login" replace />;
  }
  if (user && user.role !== "Admin") {
    toast.error("Acesso negado.");
    return <Navigate to="/" replace />;
  }

  // Mostra um spinner de página inteira
  if (isLoading && colaboradores.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* O Sidebar é necessário aqui pois esta é uma página "irmã" do Dashboard */}
      <Sidebar
        activeSection="Configurações"
        onSectionChange={(section) => {
          // Se clicar em qualquer outra seção, volta para a home (Dashboard)
          if (section !== "Configurações") {
            window.location.href = "/";
          }
        }}
      />
      <main className="ml-64 p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-3xl font-bold text-foreground">
              Gerenciar Colaboradores
            </h2>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <PlusCircle className="mr-2 h-4 w-4" />
                  Novo Colaborador
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Criar Novo Colaborador</DialogTitle>
                  <DialogDescription>
                    A senha deve ser forte e informada ao usuário.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="nome">Nome Completo</Label>
                    <Input
                      id="nome"
                      value={novoNome}
                      onChange={(e) => setNovoNome(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login">Login (sem espaços)</Label>
                    <Input
                      id="login"
                      value={novoLogin}
                      onChange={(e) => setNovoLogin(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="senha">Senha</Label>
                    <Input
                      id="senha"
                      type="password"
                      value={novaSenha}
                      onChange={(e) => setNovaSenha(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="role">Permissão (Role)</Label>
                    <Select
                      value={novoRole}
                      onValueChange={(val) =>
                        setNovoRole(val as "User" | "Admin")
                      }
                    >
                      <SelectTrigger id="role">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="User">
                          Usuário Padrão (User)
                        </SelectItem>
                        <SelectItem value="Admin">
                          Administrador (Admin)
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setIsDialogOpen(false)}
                    disabled={isSubmitting}
                  >
                    Cancelar
                  </Button>
                  <Button onClick={handleCreateUser} disabled={isSubmitting}>
                    {isSubmitting && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    Salvar
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {/* Tabela de Usuários */}
          <div className="bg-card rounded-lg shadow-card overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Login</TableHead>
                  <TableHead>Permissão</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading && colaboradores.length === 0 ? ( // Ajuste para mostrar loading na tabela
                  <TableRow>
                    <TableCell colSpan={5} className="text-center p-8">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                    </TableCell>
                  </TableRow>
                ) : (
                  colaboradores.map((colaborador) => (
                    <TableRow key={colaborador.id}>
                      <TableCell className="font-medium">
                        {colaborador.nome_colaborador}
                      </TableCell>
                      <TableCell>{colaborador.login}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            colaborador.role === "Admin"
                              ? "default"
                              : "secondary"
                          }
                        >
                          {colaborador.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            colaborador.is_ativo ? "success" : "destructive"
                          }
                        >
                          {colaborador.is_ativo ? "Ativo" : "Bloqueado"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right space-x-2">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={() =>
                                handleUpdateUser(colaborador, "toggleAtivo")
                              }
                              disabled={user?.login === colaborador.login}
                            >
                              {colaborador.is_ativo ? (
                                <UserX className="h-4 w-4" />
                              ) : (
                                <UserCheck className="h-4 w-4" />
                              )}
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>
                              {colaborador.is_ativo ? "Bloquear" : "Ativar"}{" "}
                              Usuário
                            </p>
                          </TooltipContent>
                        </Tooltip>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={() =>
                                handleUpdateUser(colaborador, "toggleRole")
                              }
                              disabled={user?.login === colaborador.login}
                            >
                              {colaborador.role === "User" ? "Admin" : "User"}
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>
                              {colaborador.role === "User"
                                ? "Promover para Admin"
                                : "Rebaixar para User"}
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </main>
    </div>
  );
}

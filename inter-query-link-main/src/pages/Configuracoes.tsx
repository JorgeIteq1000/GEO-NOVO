// src/pages/Configuracoes.tsx
// (Novo arquivo completo)

import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import { apiFetch } from "@/lib/api";
import { toast } from "sonner";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Loader2, UserPlus, Save } from "lucide-react";

// Tipo para o Colaborador (baseado no seu api_server.py)
interface Colaborador {
  id: number;
  nome_colaborador: string;
  login: string;
  role: "Admin" | "User";
  is_ativo: boolean;
}

export default function Configuracoes() {
  const [colaboradores, setColaboradores] = useState<Colaborador[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Estados do Formulário de Novo Usuário
  const [nome, setNome] = useState("");
  const [login, setLogin] = useState("");
  const [senha, setSenha] = useState("");
  const [role, setRole] = useState<"User" | "Admin">("User");

  const API_URL = "http://localhost:5000/api/colaboradores";

  // Função para buscar os dados
  const fetchColaboradores = async () => {
    console.log("[Configurações] Buscando lista de colaboradores...");
    setIsLoading(true);
    try {
      const response = await apiFetch(API_URL);
      if (!response.ok) {
        throw new Error("Falha ao buscar dados");
      }
      const data: Colaborador[] = await response.json();
      console.log("[Configurações] Colaboradores recebidos:", data);
      setColaboradores(data);
    } catch (error) {
      console.error("[Configurações] Erro ao buscar colaboradores:", error);
      toast.error("Erro ao carregar colaboradores.");
    } finally {
      setIsLoading(false);
    }
  };

  // Buscar dados ao carregar a página
  useEffect(() => {
    fetchColaboradores();
  }, []);

  // Função para criar um novo colaborador
  const handleCreateColaborador = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nome || !login || !senha) {
      toast.warning("Preencha todos os campos obrigatórios.");
      return;
    }
    console.log(
      `[Configurações] Criando novo usuário: ${login}, Role: ${role}`
    );
    setIsSubmitting(true);
    try {
      const response = await apiFetch(API_URL, {
        method: "POST",
        body: JSON.stringify({
          nome,
          login,
          senha,
          role,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Falha ao criar usuário");
      }

      toast.success(`Usuário ${nome} criado com sucesso!`);
      // Limpa o formulário
      setNome("");
      setLogin("");
      setSenha("");
      setRole("User");
      // Atualiza a lista
      fetchColaboradores();
    } catch (error) {
      console.error("[Configurações] Erro ao criar:", error);
      toast.error("Erro ao criar usuário.", {
        description: (error as Error).message,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Função para atualizar Role ou Status
  const handleUpdateColaborador = async (
    id: number,
    field: "role" | "is_ativo",
    value: "Admin" | "User" | boolean
  ) => {
    console.log(
      `[Configurações] Atualizando ID ${id}: Campo ${field}, Valor ${value}`
    );

    // Encontra o usuário no estado local para ter os dados completos
    const userToUpdate = colaboradores.find((c) => c.id === id);
    if (!userToUpdate) return;

    // Monta o payload (corpo da requisição)
    // O backend espera ambos os campos
    const payload = {
      role: field === "role" ? value : userToUpdate.role,
      is_ativo: field === "is_ativo" ? value : userToUpdate.is_ativo,
    };

    try {
      const response = await apiFetch(`${API_URL}/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Falha ao atualizar");
      }

      toast.success("Usuário atualizado com sucesso!");
      // Atualiza a lista localmente para refletir a mudança
      setColaboradores(
        colaboradores.map((c) => (c.id === id ? { ...c, [field]: value } : c))
      );
    } catch (error) {
      console.error("[Configurações] Erro ao atualizar:", error);
      toast.error("Erro ao atualizar usuário.", {
        description: (error as Error).message,
      });
      // Recarrega a lista do zero em caso de erro para reverter a mudança otimista
      fetchColaboradores();
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Usamos a prop 'Configuracoes' para a Sidebar saber qual item marcar */}
      <Sidebar
        activeSection={"Configuracoes"}
        onSectionChange={(section) => {
          // Se o usuário clicar em outra seção, nós navegamos
          window.location.href =
            section === "Dashboard" ? "/" : `/${section.toLowerCase()}`;
        }}
      />

      <main className="ml-64 p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <h1 className="text-3xl font-bold text-foreground">Configurações</h1>

          {/* Card de Novo Colaborador */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserPlus className="h-5 w-5" />
                Criar Novo Colaborador
              </CardTitle>
              <CardDescription>
                Preencha os dados para criar um novo acesso ao sistema.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateColaborador} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="nome">Nome Completo</Label>
                    <Input
                      id="nome"
                      value={nome}
                      onChange={(e) => setNome(e.target.value)}
                      placeholder="Ex: João da Silva"
                      disabled={isSubmitting}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login">Login de Acesso</Label>
                    <Input
                      id="login"
                      value={login}
                      onChange={(e) => setLogin(e.target.value)}
                      placeholder="Ex: joao.silva"
                      disabled={isSubmitting}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="senha">Senha Provisória</Label>
                    <Input
                      id="senha"
                      type="password"
                      value={senha}
                      onChange={(e) => setSenha(e.target.value)}
                      placeholder="••••••••"
                      disabled={isSubmitting}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="role">Nível de Acesso (Role)</Label>
                    <Select
                      value={role}
                      onValueChange={(value: "User" | "Admin") =>
                        setRole(value)
                      }
                      disabled={isSubmitting}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione o nível" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="User">Colaborador (User)</SelectItem>
                        <SelectItem value="Admin">
                          Administrador (Admin)
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Salvar Novo Colaborador
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Card da Lista de Colaboradores */}
          <Card>
            <CardHeader>
              <CardTitle>Gerenciar Colaboradores</CardTitle>
              <CardDescription>
                Atualize o nível de acesso e o status dos colaboradores.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center p-8">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nome</TableHead>
                      <TableHead>Login</TableHead>
                      <TableHead>Nível (Role)</TableHead>
                      <TableHead>Status (Ativo)</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {colaboradores.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell className="font-medium">
                          {user.nome_colaborador}
                        </TableCell>
                        <TableCell>{user.login}</TableCell>
                        <TableCell>
                          <Select
                            value={user.role}
                            onValueChange={(value: "User" | "Admin") =>
                              handleUpdateColaborador(user.id, "role", value)
                            }
                          >
                            <SelectTrigger className="w-[180px]">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="User">Colaborador</SelectItem>
                              <SelectItem value="Admin">
                                Administrador
                              </SelectItem>
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={user.is_ativo}
                            onCheckedChange={(checked) =>
                              handleUpdateColaborador(
                                user.id,
                                "is_ativo",
                                checked
                              )
                            }
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

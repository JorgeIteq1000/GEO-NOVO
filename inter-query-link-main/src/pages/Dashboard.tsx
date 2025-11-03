// src/pages/Dashboard.tsx
// (Arquivo completo com a correção de navegação)

// --- MUDANÇA 1: Importar o 'useNavigate' ---
import { useState } from "react";
import { useNavigate } from "react-router-dom"; // <-- ADICIONADO
import Sidebar from "@/components/Sidebar";
import SearchModule from "@/components/SearchModule";
import { Search, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

// Tipo para os resultados de todas as seções
type AllResultsState = Record<string, any[]>;

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState("Pessoa");

  // --- MUDANÇA 2: Inicializar o 'navigate' ---
  const navigate = useNavigate(); // <-- ADICIONADO

  // --- Estados que subiram do SearchModule ---
  const [query, setQuery] = useState("");
  const [isCpfSearch, setIsCpfSearch] = useState(false);
  const [allResults, setAllResults] = useState<AllResultsState | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // --- Fim dos estados ---

  // --- Lógica de busca que subiu ---
  const handleSearch = async () => {
    if (!query.trim()) {
      // Se a busca estiver vazia, limpa os resultados
      setAllResults(null);
      setError(null);
      return;
    }

    console.log(
      `[Modo Turbo Dashboard] Buscando... Query: ${query}, Modo CPF: ${isCpfSearch}`
    );
    setIsLoading(true);
    setError(null);

    try {
      const apiUrl = `http://localhost:5000/api/search/all?q=${encodeURIComponent(
        query
      )}&cpf=${isCpfSearch}`;

      console.log(`[Modo Turbo Dashboard] Chamando API Global: ${apiUrl}`);

      const response = await apiFetch(apiUrl);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(
          data.error ||
            `Erro na rede: ${response.status} ${response.statusText}`
        );
      }

      const data: AllResultsState = await response.json();
      console.log("[Modo Turbo Dashboard] Dados recebidos:", data);

      setAllResults(data); // Armazena o objeto completo de resultados
    } catch (err: unknown) {
      if (err instanceof Error) {
        console.error(
          "[Modo Turbo Dashboard] Erro na busca:",
          err.message,
          err
        );
        setError(`Erro ao buscar dados: ${err.message}.`);
      } else {
        console.error("[Modo Turbo Dashboard] Erro desconhecido:", err);
        setError("Ocorreu um erro desconhecido.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };
  // --- Fim da lógica de busca ---

  // --- MUDANÇA 3: Lógica de navegação corrigida ---
  const handleSectionChange = (section: string) => {
    // Se a seção for 'Configuracoes' (ou 'Relatórios'), navega para a rota dela
    if (section === "Configuracoes") {
      console.log("[Modo Turbo Dashboard] Navegando para /configuracoes...");
      navigate("/configuracoes");
      return; // Importante parar a execução aqui!
    }

    // NOTA: Se 'Relatórios' também virar uma página separada, adicione-a aqui:
    // if (section === "Relatórios") {
    //   console.log("[Modo Turbo Dashboard] Navegando para /relatorios...");
    //   navigate("/relatorios");
    //   return;
    // }

    // Se for qualquer outra seção, é uma aba de dados. Apenas atualiza o estado.
    setActiveSection(section);
    console.log(`[Modo Turbo Dashboard] Mudou para aba: ${section}`);
  };
  // --- FIM DA MUDANÇA ---

  return (
    <div className="min-h-screen bg-background">
      <Sidebar
        activeSection={activeSection}
        onSectionChange={handleSectionChange} // Esta função agora está correta
      />

      <main className="ml-64 p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* --- Barra de Busca (agora no Dashboard) --- */}
          <div className="bg-card rounded-lg p-6 shadow-card">
            <h2 className="text-2xl font-bold mb-6 text-foreground">
              Buscar Aluno (Global)
            </h2>

            <div className="flex flex-col gap-4">
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={`Digite ${
                      isCpfSearch ? "o CPF..." : "o Nome ou Matrícula..."
                    }`}
                    className="w-full pl-12 pr-4 py-3 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-background text-foreground"
                  />
                </div>
                <Button
                  onClick={handleSearch}
                  disabled={isLoading}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground px-8"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Buscando...
                    </>
                  ) : (
                    "Buscar"
                  )}
                </Button>
              </div>

              {/* --- Bloco do Checkbox --- */}
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="cpf-search"
                  checked={isCpfSearch}
                  onCheckedChange={(checked) =>
                    setIsCpfSearch(checked as boolean)
                  }
                />
                <Label
                  htmlFor="cpf-search"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Buscar apenas por CPF
                </Label>
              </div>
              {/* --- Fim da Mudança --- */}
            </div>
          </div>
          {/* --- Fim da Barra de Busca --- */}

          {/* O SearchModule agora está seguro, pois 'activeSection' NUNCA
            será "Configuracoes" (o componente navegará antes).
          */}
          <SearchModule
            type={activeSection}
            query={query} // Passa a query para saber o que foi buscado
            results={allResults ? allResults[activeSection] : null} // Passa SÓ os resultados desta seção
            isLoading={isLoading} // Passa o estado de loading
            error={error} // Passa o estado de erro
            onRefreshData={handleSearch}
            pessoaInfo={
              allResults && allResults.Pessoa && allResults.Pessoa.length > 0
                ? allResults.Pessoa[0]
                : null
            }
          />
        </div>
      </main>
    </div>
  );
}

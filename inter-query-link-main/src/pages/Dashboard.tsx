import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import SearchModule from "@/components/SearchModule";
import { Search, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
// --- MUDANÇA: Importar Checkbox e Label ---
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
// --- MUDANÇA: Importar nosso novo "Mensageiro" ---
import { apiFetch } from "@/lib/api";
// --- FIM DA MUDANÇA ---

// Tipo para os resultados de todas as seções
type AllResultsState = Record<string, any[]>;

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState("Pessoa");

  // --- Estados que subiram do SearchModule ---
  const [query, setQuery] = useState("");
  // --- MUDANÇA: Estado para o Checkbox ---
  const [isCpfSearch, setIsCpfSearch] = useState(false);
  // --- FIM DA MUDANÇA ---
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
      // --- MUDANÇA: Adiciona o parâmetro &cpf=true/false na URL ---
      const apiUrl = `http://localhost:5000/api/search/all?q=${encodeURIComponent(
        query
      )}&cpf=${isCpfSearch}`;
      // --- FIM DA MUDANÇA ---

      console.log(`[Modo Turbo Dashboard] Chamando API Global: ${apiUrl}`);

      // --- MUDANÇA: Trocar 'fetch' por 'apiFetch' ---
      const response = await apiFetch(apiUrl);
      // --- FIM DA MUDANÇA ---

      if (!response.ok) {
        // O apiFetch já vai tratar o 401, mas podemos ter outros erros
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

  // Limpa os resultados quando a secção muda
  const handleSectionChange = (section: string) => {
    setActiveSection(section);
    console.log(`[Modo Turbo Dashboard] Mudou para aba: ${section}`);
  };

  return (
    <div className="min-h-screen bg-background">
      <Sidebar
        activeSection={activeSection}
        onSectionChange={handleSectionChange}
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

              {/* --- MUDANÇA: Bloco do Checkbox --- */}
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

          {/* O SearchModule agora é apenas um 'Display' */}
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

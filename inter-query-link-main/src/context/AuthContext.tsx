import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { toast } from "sonner"; // Usaremos para dar "Boas-vindas"

// O que vamos armazenar sobre o usuário
interface User {
  login: string;
  nome: string;
  role: "Admin" | "User";
}

// O que o nosso "Cérebro" (Context) vai fornecer
interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// O componente "Provedor" que vai abraçar seu App
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Começa 'true' para checar o localStorage

  // Efeito para carregar o token do localStorage ao iniciar
  useEffect(() => {
    try {
      console.log("[AuthContext] Verificando login salvo...");
      const storedToken = localStorage.getItem("accessToken");
      const storedUser = localStorage.getItem("user");

      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        console.log("[AuthContext] Usuário carregado do localStorage.");
      }
    } catch (e) {
      console.error("[AuthContext] Erro ao carregar do localStorage", e);
      // Se der erro, limpa tudo por segurança
      localStorage.clear();
    } finally {
      setIsLoading(false); // Termina de carregar
    }
  }, []);

  // Função para fazer o Login
  const login = (newToken: string, newUser: User) => {
    console.log(`[AuthContext] Logando usuário: ${newUser.nome}`);
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem("accessToken", newToken);
    localStorage.setItem("user", JSON.stringify(newUser));
    toast.success(`Bem-vindo, ${newUser.nome}!`);
  };

  // Função para fazer o Logout
  const logout = () => {
    console.log("[AuthContext] Deslogando usuário.");
    setToken(null);
    setUser(null);
    localStorage.removeItem("accessToken");
    localStorage.removeItem("user");
    toast.info("Você foi desconectado.");
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook customizado para facilitar o uso
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider");
  }
  return context;
}

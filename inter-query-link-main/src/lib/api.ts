// src/lib/api.ts
// (Arquivo completo e corrigido)

// Esta função pega o token do localStorage
function getAuthToken(): string | null {
  console.log("[apiFetch] Buscando token do localStorage.");
  return localStorage.getItem("accessToken");
}

// Este é o nosso novo "fetch" inteligente
export async function apiFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  console.log(`[apiFetch] Chamando: ${url}`);
  const token = getAuthToken();

  // Prepara os cabeçalhos (headers)
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json"); // Sempre JSON

  if (token) {
    console.log(
      "[apiFetch] Token encontrado, anexando ao header Authorization."
    );
    headers.set("Authorization", `Bearer ${token}`);
  } else {
    console.warn("[apiFetch] Nenhum token encontrado no localStorage.");
  }

  // Monta a requisição final
  const response = await fetch(url, {
    ...options,
    headers: headers,
  });

  // --- MUDANÇA AQUI ---
  // Vamos deslogar o usuário SOMENTE se o erro for 401 (Não Autorizado)
  // Erros 403 (Proibido) ou 422 (Inválido) não devem deslogar,
  // apenas o 'catch' no Dashboard irá tratar e mostrar o erro.
  if (response.status === 401) {
    console.warn(`[apiFetch] Erro de autorização (401). Deslogando usuário.`);
    // Isso força o logout e o redirecionamento para a tela de login
    localStorage.clear();
    window.location.href = "/login"; // Redireciona para a tela de login

    // Lança um erro para interromper a execução do 'try' no Dashboard
    throw new Error(`Token expirado ou inválido (401)`);
  }
  // --- FIM DA MUDANÇA ---

  return response;
}

// Esta função pega o token do localStorage
function getAuthToken(): string | null {
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
    headers.set("Authorization", `Bearer ${token}`);
  }

  // Monta a requisição final
  const response = await fetch(url, {
    ...options,
    headers: headers,
  });

  // Se o token expirar (Erro 401 ou 403), desloga o usuário!
  if (response.status === 401 || response.status === 403) {
    console.warn("[apiFetch] Erro de autorização (401/403). Deslogando.");
    // Isso força o logout e o redirecionamento para a tela de login
    localStorage.clear();
    window.location.href = "/login"; // Redireciona para a tela de login
  }

  return response;
}

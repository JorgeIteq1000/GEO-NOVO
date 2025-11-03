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
  // Se o token expirar (401), for proibido (403) OU FOR INVÁLIDO (422), desloga o usuário!
  if (
    response.status === 401 ||
    response.status === 403 ||
    response.status === 422
  ) {
    console.warn(
      `[apiFetch] Erro de autorização (${response.status}). Deslogando usuário.`
    );
    // Isso força o logout e o redirecionamento para a tela de login
    localStorage.clear();
    window.location.href = "/login"; // Redireciona para a tela de login

    // Lança um erro para interromper a execução do 'try' no Dashboard
    throw new Error(`Erro de autorização: ${response.status}`);
  }
  // --- FIM DA MUDANÇA ---

  return response;
}

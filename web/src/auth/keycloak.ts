/**
 * Instância singleton do Keycloak.
 *
 * Configurada via variáveis VITE_ para que os valores mudem entre
 * ambientes. No build estático, os valores são incorporados pelo Vite.
 *
 * Quando VITE_KEYCLOAK_HABILITADO=false (padrão em dev local sem
 * Keycloak no ar), esta instância não é inicializada — o app funciona
 * sem autenticação para facilitar o desenvolvimento.
 */
import Keycloak from 'keycloak-js'

export const keycloakHabilitado =
  import.meta.env['VITE_KEYCLOAK_HABILITADO'] === 'true'

/**
 * Instância Keycloak configurada com as variáveis de ambiente.
 * Só use após chamar `keycloak.init()` em AuthProvider.
 */
export const keycloak = new Keycloak({
  url: import.meta.env['VITE_KEYCLOAK_URL'] ?? 'http://localhost:8080',
  realm: import.meta.env['VITE_KEYCLOAK_REALM'] ?? 'enxoval',
  clientId: import.meta.env['VITE_KEYCLOAK_CLIENT_ID'] ?? 'webapp',
})

// O StrictMode monta os efeitos duas vezes em desenvolvimento. O adapter
// permite init apenas uma vez por instância, então compartilhamos a promessa.
let inicializacao: Promise<boolean> | undefined

export function inicializarKeycloak(): Promise<boolean> {
  inicializacao ??= keycloak.init({
    onLoad: 'login-required',
    pkceMethod: 'S256',
    checkLoginIframe: false,
  })
  return inicializacao
}

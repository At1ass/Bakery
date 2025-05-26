// This file is generated at build time with the current environment variables
window.env = {
  AUTH_API_URL: '${AUTH_API_URL}',
  CATALOG_API_URL: '${CATALOG_API_URL}',
  ORDER_API_URL: '${ORDER_API_URL}',
  NODE_ENV: '${NODE_ENV}',
  SESSION_TIMEOUT: '${SESSION_TIMEOUT || 1800000}',  // 30 minutes in milliseconds
  TOKEN_REFRESH_INTERVAL: '${TOKEN_REFRESH_INTERVAL || 1500000}',  // 25 minutes in milliseconds
  AUTH_CLIENT_ID: '${AUTH_CLIENT_ID || "confectionery-frontend"}',
  AUTH_AUTHORITY: '${AUTH_AUTHORITY || ""}'
}; 
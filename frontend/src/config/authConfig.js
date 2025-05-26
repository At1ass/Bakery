export const msalConfig = {
  auth: {
    clientId: window.env?.AUTH_CLIENT_ID || "your_client_id",
    authority: window.env?.AUTH_AUTHORITY || window.env?.AUTH_API_URL || "http://localhost:8001",
    redirectUri: window.location.origin,
    postLogoutRedirectUri: window.location.origin,
    navigateToLoginRequestUrl: true
  },
  cache: {
    cacheLocation: "localStorage",
    storeAuthStateInCookie: false,
    secureCookies: true,
    claimsBasedCachingEnabled: true
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) {
          return;
        }
        switch (level) {
          case "Error":
            console.error(message);
            return;
          case "Info":
            console.info(message);
            return;
          case "Verbose":
            console.debug(message);
            return;
          case "Warning":
            console.warn(message);
            return;
          default:
            return;
        }
      },
      piiLoggingEnabled: false
    }
  }
};

export const loginRequest = {
  scopes: ["openid", "profile", "offline_access"]
};

export const protectedResources = {
  catalogApi: {
    endpoint: window.env?.CATALOG_API_URL || "http://localhost:8002",
    scopes: ["catalog.read", "catalog.write"]
  },
  orderApi: {
    endpoint: window.env?.ORDER_API_URL || "http://localhost:8003",
    scopes: ["orders.read", "orders.write"]
  }
}; 
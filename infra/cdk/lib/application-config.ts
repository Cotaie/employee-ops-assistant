export interface AgentApiApplicationConfig {
  readonly githubRepository: string;
  readonly jiraInstanceUrl: string;
  readonly jiraUsername: string;
  readonly llmModel: string;
  readonly oidcAudience: string;
}

export interface CaddyApplicationConfig {
  readonly appAddress: string;
}

export interface OAuth2ProxyApplicationConfig {
  readonly clientId: string;
  readonly cookieSecure: boolean;
  readonly emailDomains: string;
  readonly redirectUrl: string;
}

export interface ApplicationConfig {
  readonly agentApi: AgentApiApplicationConfig;
  readonly caddy: CaddyApplicationConfig;
  readonly oauth2Proxy: OAuth2ProxyApplicationConfig;
}

function requireRecord(value: unknown, path: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`CDK context ${path} must be an object.`);
  }

  return value as Record<string, unknown>;
}

function requireString(
  record: Record<string, unknown>,
  key: string,
  path: string,
): string {
  const value = record[key];
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`CDK context ${path}.${key} must be a non-empty string.`);
  }

  return value;
}

function requireBoolean(
  record: Record<string, unknown>,
  key: string,
  path: string,
): boolean {
  const value = record[key];
  if (typeof value !== "boolean") {
    throw new Error(`CDK context ${path}.${key} must be a boolean.`);
  }

  return value;
}

export function parseApplicationConfig(value: unknown): ApplicationConfig {
  const applicationConfig = requireRecord(value, "applicationConfig");
  const agentApi = requireRecord(
    applicationConfig.agentApi,
    "applicationConfig.agentApi",
  );
  const caddy = requireRecord(
    applicationConfig.caddy,
    "applicationConfig.caddy",
  );
  const oauth2Proxy = requireRecord(
    applicationConfig.oauth2Proxy,
    "applicationConfig.oauth2Proxy",
  );

  return {
    agentApi: {
      githubRepository: requireString(
        agentApi,
        "githubRepository",
        "applicationConfig.agentApi",
      ),
      jiraInstanceUrl: requireString(
        agentApi,
        "jiraInstanceUrl",
        "applicationConfig.agentApi",
      ),
      jiraUsername: requireString(
        agentApi,
        "jiraUsername",
        "applicationConfig.agentApi",
      ),
      llmModel: requireString(
        agentApi,
        "llmModel",
        "applicationConfig.agentApi",
      ),
      oidcAudience: requireString(
        agentApi,
        "oidcAudience",
        "applicationConfig.agentApi",
      ),
    },
    caddy: {
      appAddress: requireString(
        caddy,
        "appAddress",
        "applicationConfig.caddy",
      ),
    },
    oauth2Proxy: {
      clientId: requireString(
        oauth2Proxy,
        "clientId",
        "applicationConfig.oauth2Proxy",
      ),
      cookieSecure: requireBoolean(
        oauth2Proxy,
        "cookieSecure",
        "applicationConfig.oauth2Proxy",
      ),
      emailDomains: requireString(
        oauth2Proxy,
        "emailDomains",
        "applicationConfig.oauth2Proxy",
      ),
      redirectUrl: requireString(
        oauth2Proxy,
        "redirectUrl",
        "applicationConfig.oauth2Proxy",
      ),
    },
  };
}

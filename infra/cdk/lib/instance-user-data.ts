import { UserData } from "aws-cdk-lib/aws-ec2";

import type { ApplicationConfig } from "./application-config";

const APPLICATION_DIRECTORY =
  "/home/ubuntu/apps/employee-ops-assistant";
const REPOSITORY_URL =
  "https://github.com/Cotaie/employee-ops-assistant.git";

export interface InstanceUserDataProps {
  readonly agentApiSecretName: string;
  readonly applicationConfig: ApplicationConfig;
  readonly awsRegion: string;
  readonly oauth2ProxySecretName: string;
}

function encodeEnvironmentFile(values: Record<string, string | boolean>): string {
  const contents = `${Object.entries(values)
    .map(([key, value]) => `${key}=${String(value)}`)
    .join("\n")}\n`;

  return Buffer.from(contents, "utf8").toString("base64");
}

function decodeEnvironmentFileCommand(contents: string, path: string): string {
  return `printf '%s' '${contents}' | base64 --decode > ${path}`;
}

export function createInstanceUserData(props: InstanceUserDataProps): UserData {
  const userData = UserData.forLinux();
  const agentApiEnvironment = encodeEnvironmentFile({
    GITHUB_REPOSITORY: props.applicationConfig.agentApi.githubRepository,
    JIRA_INSTANCE_URL: props.applicationConfig.agentApi.jiraInstanceUrl,
    JIRA_USERNAME: props.applicationConfig.agentApi.jiraUsername,
    LLM_MODEL: props.applicationConfig.agentApi.llmModel,
    LLM_TIMEOUT_SECONDS: "300",
    OIDC_AUDIENCE: props.applicationConfig.agentApi.oidcAudience,
  });
  const caddyEnvironment = encodeEnvironmentFile({
    APP_ADDRESS: props.applicationConfig.caddy.appAddress,
  });
  const oauth2ProxyEnvironment = encodeEnvironmentFile({
    OAUTH2_PROXY_CLIENT_ID: props.applicationConfig.oauth2Proxy.clientId,
    OAUTH2_PROXY_COOKIE_SECURE:
      props.applicationConfig.oauth2Proxy.cookieSecure,
    OAUTH2_PROXY_EMAIL_DOMAINS:
      props.applicationConfig.oauth2Proxy.emailDomains,
    OAUTH2_PROXY_REDIRECT_URL:
      props.applicationConfig.oauth2Proxy.redirectUrl,
  });
  const agentApiEnvironmentPath =
    `${APPLICATION_DIRECTORY}/services/agent_api/.env`;
  const caddyEnvironmentPath = `${APPLICATION_DIRECTORY}/infra/.env`;
  const oauth2ProxyEnvironmentPath =
    `${APPLICATION_DIRECTORY}/infra/oauth2-proxy/.env`;

  userData.addCommands(
    "set -euxo pipefail",
    "export DEBIAN_FRONTEND=noninteractive",
    "apt-get update",
    "apt-get upgrade -y",
    "apt-get install -y awscli ca-certificates curl git gnupg jq",
    "if ! swapon --show=NAME --noheadings | grep -qx '/swapfile'; then",
    "  if [ ! -f /swapfile ]; then fallocate -l 4G /swapfile; fi",
    "  chmod 600 /swapfile",
    "  mkswap /swapfile",
    "  swapon /swapfile",
    "fi",
    "grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab",
    "install -m 0755 -d /etc/apt/keyrings",
    "curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc",
    "chmod a+r /etc/apt/keyrings/docker.asc",
    ". /etc/os-release",
    'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list',
    "apt-get update",
    "apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
    "usermod -aG docker ubuntu",
    "systemctl enable --now docker",
    "curl -fsSL https://ollama.com/install.sh | sh",
    "install -m 0755 -d /etc/systemd/system/ollama.service.d",
    "cat > /etc/systemd/system/ollama.service.d/override.conf <<'EOF'",
    "[Service]",
    'Environment="OLLAMA_HOST=0.0.0.0:11434"',
    "EOF",
    "systemctl daemon-reload",
    "systemctl enable --now ollama",
    "systemctl restart ollama",
    "for attempt in {1..30}; do",
    "  if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null; then break; fi",
    "  sleep 2",
    "done",
    "curl -fsS http://127.0.0.1:11434/api/tags >/dev/null",
    "curl -fsS -H 'Content-Type: application/json' http://127.0.0.1:11434/api/pull -d '{\"model\":\"qwen3:1.7b\",\"stream\":false}' >/dev/null",
    "curl -fsS -H 'Content-Type: application/json' http://127.0.0.1:11434/api/pull -d '{\"model\":\"nomic-embed-text:v1.5\",\"stream\":false}' >/dev/null",
    "install -d -o ubuntu -g ubuntu /home/ubuntu/apps",
    `if [ ! -d ${APPLICATION_DIRECTORY}/.git ]; then`,
    `  runuser -u ubuntu -- git clone ${REPOSITORY_URL} ${APPLICATION_DIRECTORY}`,
    "else",
    `  runuser -u ubuntu -- git -C ${APPLICATION_DIRECTORY} pull --ff-only origin main`,
    "fi",
    `install -d -o ubuntu -g ubuntu ${APPLICATION_DIRECTORY}/infra/oauth2-proxy`,
    "set +x",
    "umask 077",
    "agent_api_secret_file=$(mktemp)",
    "oauth2_proxy_secret_file=$(mktemp)",
    "trap 'rm -f \"$agent_api_secret_file\" \"$oauth2_proxy_secret_file\"' EXIT",
    `AWS_DEFAULT_REGION='${props.awsRegion}' aws secretsmanager get-secret-value --secret-id '${props.agentApiSecretName}' --query SecretString --output text > "$agent_api_secret_file"`,
    `AWS_DEFAULT_REGION='${props.awsRegion}' aws secretsmanager get-secret-value --secret-id '${props.oauth2ProxySecretName}' --query SecretString --output text > "$oauth2_proxy_secret_file"`,
    "jq -e '(.JIRA_API_TOKEN | type == \"string\" and length > 0) and (.GITHUB_API_TOKEN | type == \"string\" and length > 0)' \"$agent_api_secret_file\" >/dev/null",
    "jq -e '(.OAUTH2_PROXY_CLIENT_SECRET | type == \"string\" and length > 0) and (.OAUTH2_PROXY_COOKIE_SECRET | type == \"string\" and length > 0)' \"$oauth2_proxy_secret_file\" >/dev/null",
    decodeEnvironmentFileCommand(
      agentApiEnvironment,
      agentApiEnvironmentPath,
    ),
    "jq -r '\"JIRA_API_TOKEN=\" + .JIRA_API_TOKEN, \"GITHUB_API_TOKEN=\" + .GITHUB_API_TOKEN' \"$agent_api_secret_file\" >> " +
      agentApiEnvironmentPath,
    decodeEnvironmentFileCommand(
      oauth2ProxyEnvironment,
      oauth2ProxyEnvironmentPath,
    ),
    "jq -r '\"OAUTH2_PROXY_CLIENT_SECRET=\" + .OAUTH2_PROXY_CLIENT_SECRET, \"OAUTH2_PROXY_COOKIE_SECRET=\" + .OAUTH2_PROXY_COOKIE_SECRET' \"$oauth2_proxy_secret_file\" >> " +
      oauth2ProxyEnvironmentPath,
    decodeEnvironmentFileCommand(caddyEnvironment, caddyEnvironmentPath),
    `chown ubuntu:ubuntu ${agentApiEnvironmentPath} ${oauth2ProxyEnvironmentPath} ${caddyEnvironmentPath}`,
    `chmod 600 ${agentApiEnvironmentPath} ${oauth2ProxyEnvironmentPath} ${caddyEnvironmentPath}`,
    "rm -f \"$agent_api_secret_file\" \"$oauth2_proxy_secret_file\"",
    "trap - EXIT",
    "set -x",
    `runuser -u ubuntu -- docker compose -f ${APPLICATION_DIRECTORY}/infra/compose.yaml config --quiet`,
    `runuser -u ubuntu -- docker compose -f ${APPLICATION_DIRECTORY}/infra/compose.yaml up -d --build`,
    "docker --version",
    "docker compose version",
    "curl -fsS http://127.0.0.1:11434/api/tags >/dev/null",
  );

  return userData;
}

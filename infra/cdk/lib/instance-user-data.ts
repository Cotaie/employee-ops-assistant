import { UserData } from "aws-cdk-lib/aws-ec2";

const APPLICATION_DIRECTORY =
  "/home/ubuntu/apps/employee-ops-assistant";
const REPOSITORY_URL =
  "https://github.com/Cotaie/employee-ops-assistant.git";

export function createInstanceUserData(): UserData {
  const userData = UserData.forLinux();

  userData.addCommands(
    "set -euxo pipefail",
    "export DEBIAN_FRONTEND=noninteractive",
    "apt-get update",
    "apt-get upgrade -y",
    "apt-get install -y ca-certificates curl git gnupg",
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
    "ollama pull qwen3:1.7b",
    "install -d -o ubuntu -g ubuntu /home/ubuntu/apps",
    `if [ ! -d ${APPLICATION_DIRECTORY}/.git ]; then`,
    `  runuser -u ubuntu -- git clone ${REPOSITORY_URL} ${APPLICATION_DIRECTORY}`,
    "else",
    `  runuser -u ubuntu -- git -C ${APPLICATION_DIRECTORY} pull --ff-only origin main`,
    "fi",
    "docker --version",
    "docker compose version",
    "ollama list",
  );

  return userData;
}

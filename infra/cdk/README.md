# AWS CDK

This package defines the AWS infrastructure for Employee Ops Assistant using
AWS CDK and TypeScript.

The stack looks up the existing default VPC in the target account and Region.
This is a read-only context lookup: it does not create, modify, or import the
VPC into CloudFormation. Later infrastructure resources can use the resulting
VPC reference.

## Target environment

The non-secret deployment target is configured in `cdk.json`:

```text
AWS account: 634432338572
AWS region:  eu-central-1
Instance:    t2.medium
Root volume: 42 GiB
SSH key:     employee-ops-key
SSH source:  213.157.184.108/32
```

The application entry point validates these context values and passes them to
the stack. Update `sshAllowedCidr` if the administrator's public IP address
changes. This configuration does not authenticate with or deploy to the
account.

## Instance security group

The synthesized stack defines a security group in the existing default VPC
with the following inbound access:

- TCP 80 from any IPv4 address for HTTP.
- TCP 443 from any IPv4 address for HTTPS.
- TCP 22 only from the configured `sshAllowedCidr` for administration.

All outbound traffic is allowed so the EC2 instance can download system
packages, container images, models, and certificates.

## EC2 instance role

The stack defines a runtime IAM role trusted only by the EC2 service. It
attaches the AWS-managed
`AmazonSSMManagedInstanceCore` policy so the instance can register with
Systems Manager and support Session Manager access.

The role can read only the existing `employee-ops/agent-api` and
`employee-ops/oauth2-proxy` Secrets Manager secrets. It does not grant
administrator, general Secrets Manager, S3, or CloudWatch permissions.

## EC2 instance

The synthesized stack adds an `employee-ops-assistant` instance with:

- Ubuntu Server 26.04 LTS AMD64, resolved from Canonical's public SSM parameter
  and pinned in `cdk.context.json`.
- `t2.medium` compute capacity.
- A 42 GiB encrypted gp3 root volume that is deleted with the instance.
- Placement in an existing public subnet with an automatically assigned public
  IPv4 address.
- The existing `employee-ops-key` SSH key pair.
- The CDK-managed security group and EC2 runtime role.
- IMDSv2 required for instance metadata credentials.

This instance will be additional to the existing manually managed instance and
will incur EC2 and EBS charges if deployed. Elastic IP cutover remains a
separate, explicit migration step.

## First-boot user data

On its first boot, cloud-init runs a non-interactive setup script that:

- Updates Ubuntu and installs Git and required package-management tools.
- Creates and persists a 4 GiB swap file.
- Installs Docker Engine, Buildx, and the Compose plugin from Docker's official
  Ubuntu repository, adds `ubuntu` to the `docker` group, and enables Docker.
- Installs Ollama, binds it to `0.0.0.0:11434` for host-to-container access,
  enables its systemd service, and downloads `qwen3:1.7b` and
  `nomic-embed-text:v1.5`.
- Clones the public repository to
  `/home/ubuntu/apps/employee-ops-assistant` as the `ubuntu` user.
- Retrieves the two application secrets with the EC2 role, validates their
  expected JSON fields, and creates private Agent API and OAuth2 Proxy `.env`
  files.
- Creates `infra/.env` from the non-secret Caddy configuration, validates the
  complete Compose configuration, builds the application images, and starts
  the stack.

Secret retrieval runs with shell command tracing disabled, and generated
environment files are readable only by the `ubuntu` user. First-boot output is
available on EC2 in `/var/log/cloud-init-output.log`.

## Application configuration

Non-sensitive, deployment-specific values are grouped by service under
`applicationConfig` in `cdk.json`. Replace all placeholder Jira and Google
values before deployment.

The Agent API secret must contain `JIRA_API_TOKEN` and `GITHUB_API_TOKEN`. The
OAuth2 Proxy secret must contain `OAUTH2_PROXY_CLIENT_SECRET` and
`OAUTH2_PROXY_COOKIE_SECRET`. At first boot, user data combines those fields
with `applicationConfig` to generate:

- `services/agent_api/.env`
- `infra/oauth2-proxy/.env`
- `infra/.env`

## Local validation

```bash
cd infra/cdk
nvm use
npm install
npm run build
AWS_PROFILE=employee-ops npm run synth
```

`synth` generates a CloudFormation template under `cdk.out/`. It does not deploy
the template to AWS. The first synthesis queries AWS for the default VPC and
caches the non-secret lookup result in `cdk.context.json` for deterministic
future synthesis.

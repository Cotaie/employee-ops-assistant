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

The role does not grant administrator, Secrets Manager, S3, or CloudWatch
permissions. Those permissions can be added later with resource-level scope
when their concrete resources are defined.

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
will incur EC2 and EBS charges if deployed. Application configuration, Compose
startup, and Elastic IP cutover are intentionally deferred to later changes.

## First-boot user data

On its first boot, cloud-init runs a non-interactive setup script that:

- Updates Ubuntu and installs Git and required package-management tools.
- Creates and persists a 4 GiB swap file.
- Installs Docker Engine, Buildx, and the Compose plugin from Docker's official
  Ubuntu repository, adds `ubuntu` to the `docker` group, and enables Docker.
- Installs Ollama, binds it to `0.0.0.0:11434` for host-to-container access,
  enables its systemd service, and downloads `qwen3:1.7b`.
- Clones the public repository to
  `/home/ubuntu/apps/employee-ops-assistant` as the `ubuntu` user.

The bootstrap intentionally does not create `.env` files, download the
embeddings model, build application images, or start Docker Compose. First-boot
output is available on EC2 in `/var/log/cloud-init-output.log`.

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

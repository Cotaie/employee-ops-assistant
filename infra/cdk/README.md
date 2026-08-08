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

All outbound traffic is allowed so the future EC2 instance can download system
packages, container images, models, and certificates. The security group is not
created in AWS until the stack is deployed.

## EC2 instance role

The synthesized stack defines a runtime IAM role trusted only by the EC2
service. It initially attaches the AWS-managed
`AmazonSSMManagedInstanceCore` policy so the future instance can register with
Systems Manager and support Session Manager access.

The role does not grant administrator, Secrets Manager, S3, or CloudWatch
permissions. Those permissions can be added later with resource-level scope
when their concrete resources are defined. The role is not created or attached
to an instance until the stack is deployed.

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

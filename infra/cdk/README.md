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
```

The application entry point validates both context values and passes them to
the stack through its `env` property. This makes synthesized templates specific
to the intended AWS environment. It does not authenticate with or deploy to the
account.

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

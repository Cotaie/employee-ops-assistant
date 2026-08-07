# AWS CDK

This package defines the AWS infrastructure for Employee Ops Assistant using
AWS CDK and TypeScript.

The initial stack is intentionally empty. It can be synthesized locally, but it
does not create or modify AWS resources.

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
npm run synth
```

`synth` generates a CloudFormation template under `cdk.out/`. It does not deploy
the template to AWS.

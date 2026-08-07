# AWS CDK

This package defines the AWS infrastructure for Employee Ops Assistant using
AWS CDK and TypeScript.

The initial stack is intentionally empty. It can be synthesized locally, but it
does not create or modify AWS resources.

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


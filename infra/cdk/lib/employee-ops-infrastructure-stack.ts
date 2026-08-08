import { Stack, type StackProps } from "aws-cdk-lib";
import { Vpc, type IVpc } from "aws-cdk-lib/aws-ec2";
import type { Construct } from "constructs";

export class EmployeeOpsInfrastructureStack extends Stack {
  public readonly vpc: IVpc;

  public constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    this.vpc = Vpc.fromLookup(this, "DefaultVpc", {
      isDefault: true,
    });
  }
}

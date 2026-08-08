import { Stack, type StackProps } from "aws-cdk-lib";
import {
  Peer,
  Port,
  SecurityGroup,
  Vpc,
  type ISecurityGroup,
  type IVpc,
} from "aws-cdk-lib/aws-ec2";
import {
  ManagedPolicy,
  Role,
  ServicePrincipal,
  type IRole,
} from "aws-cdk-lib/aws-iam";
import type { Construct } from "constructs";

export interface EmployeeOpsInfrastructureStackProps extends StackProps {
  readonly sshAllowedCidr: string;
}

export class EmployeeOpsInfrastructureStack extends Stack {
  public readonly instanceRole: IRole;
  public readonly instanceSecurityGroup: ISecurityGroup;
  public readonly vpc: IVpc;

  public constructor(
    scope: Construct,
    id: string,
    props: EmployeeOpsInfrastructureStackProps,
  ) {
    super(scope, id, props);

    this.vpc = Vpc.fromLookup(this, "DefaultVpc", {
      isDefault: true,
    });

    this.instanceRole = new Role(this, "InstanceRole", {
      assumedBy: new ServicePrincipal("ec2.amazonaws.com"),
      description: "Runtime AWS permissions for Employee Ops Assistant EC2",
      managedPolicies: [
        ManagedPolicy.fromAwsManagedPolicyName(
          "AmazonSSMManagedInstanceCore",
        ),
      ],
    });

    this.instanceSecurityGroup = new SecurityGroup(
      this,
      "InstanceSecurityGroup",
      {
        allowAllOutbound: true,
        description: "Network access for the Employee Ops Assistant EC2 host",
        vpc: this.vpc,
      },
    );

    this.instanceSecurityGroup.addIngressRule(
      Peer.anyIpv4(),
      Port.tcp(80),
      "Allow public HTTP",
    );
    this.instanceSecurityGroup.addIngressRule(
      Peer.anyIpv4(),
      Port.tcp(443),
      "Allow public HTTPS",
    );
    this.instanceSecurityGroup.addIngressRule(
      Peer.ipv4(props.sshAllowedCidr),
      Port.tcp(22),
      "Allow SSH from the configured administrator address",
    );
  }
}

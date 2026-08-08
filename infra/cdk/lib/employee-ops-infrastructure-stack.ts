import { Stack, type StackProps } from "aws-cdk-lib";
import {
  BlockDeviceVolume,
  EbsDeviceVolumeType,
  Instance,
  InstanceType,
  KeyPair,
  MachineImage,
  OperatingSystemType,
  Peer,
  Port,
  SecurityGroup,
  SubnetType,
  Vpc,
  type IInstance,
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

import { createInstanceUserData } from "./instance-user-data";

const UBUNTU_2604_AMI_PARAMETER =
  "/aws/service/canonical/ubuntu/server/26.04/stable/current/amd64/hvm/ebs-gp3/ami-id";

export interface EmployeeOpsInfrastructureStackProps extends StackProps {
  readonly instanceType: string;
  readonly keyPairName: string;
  readonly rootVolumeSizeGiB: number;
  readonly sshAllowedCidr: string;
}

export class EmployeeOpsInfrastructureStack extends Stack {
  public readonly instance: IInstance;
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

    const keyPair = KeyPair.fromKeyPairName(
      this,
      "InstanceKeyPair",
      props.keyPairName,
    );
    const machineImage = MachineImage.fromSsmParameter(
      UBUNTU_2604_AMI_PARAMETER,
      {
        cachedInContext: true,
        os: OperatingSystemType.LINUX,
      },
    );
    const userData = createInstanceUserData();

    this.instance = new Instance(this, "Instance", {
      associatePublicIpAddress: true,
      blockDevices: [
        {
          deviceName: "/dev/sda1",
          volume: BlockDeviceVolume.ebs(props.rootVolumeSizeGiB, {
            deleteOnTermination: true,
            encrypted: true,
            volumeType: EbsDeviceVolumeType.GP3,
          }),
        },
      ],
      instanceName: "employee-ops-assistant",
      instanceType: new InstanceType(props.instanceType),
      keyPair,
      machineImage,
      propagateTagsToVolumeOnCreation: true,
      requireImdsv2: true,
      role: this.instanceRole,
      securityGroup: this.instanceSecurityGroup,
      userData,
      vpc: this.vpc,
      vpcSubnets: {
        subnetType: SubnetType.PUBLIC,
      },
    });
  }
}

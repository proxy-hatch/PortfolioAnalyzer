import {Stack} from 'aws-cdk-lib';
import {SubnetType, Vpc} from 'aws-cdk-lib/aws-ec2';
import {Construct} from 'constructs';
import {StackCreationInfo} from '../stack-creation-info';

export interface VpcStackProps {
    readonly stackCreationInfo: StackCreationInfo;
    readonly terminationProtection?: boolean;
}

export class VpcStack extends Stack {
    public readonly vpc: Vpc;

    constructor(scope: Construct, id: string, props: VpcStackProps) {
        super(scope, id, props);

        const {stackPrefix} = props.stackCreationInfo;

        this.vpc = new Vpc(this, `${stackPrefix}-Vpc`, {
            natGateways: 0,
            maxAzs: Stack.of(this).availabilityZones.length,
            subnetConfiguration: [
                {
                    cidrMask: 24,
                    subnetType: SubnetType.PUBLIC,
                    name: 'Public',
                },
                {
                    cidrMask: 24,
                    subnetType: SubnetType.PRIVATE_ISOLATED,
                    name: 'Isolated',
                },
            ],
        });
    }
}
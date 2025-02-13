import {Environment, StackProps, Stage} from 'aws-cdk-lib';
import {STAGE} from '../enum/stage';
import {VpcStack} from './vpc';
import {DnsStack} from './dns';
import {EcsServiceStack} from './ecs-service';
import {Construct} from 'constructs';
import {StackCreationInfo} from '../stack-creation-info';

export interface DeploymentStacksProps extends StackProps {
    readonly env: Environment;
    readonly stackCreationInfo: StackCreationInfo;
}

export class DeploymentStacks extends Stage {
    constructor(scope: Construct, id: string, props: DeploymentStacksProps) {
        super(scope, id, props);

        const stackCreationInfo = props.stackCreationInfo;
        const {stage, stackPrefix} = props.stackCreationInfo;

        const terminationProtection = stage !== STAGE.DEV; // Termination protection for non-DEV envs

        const vpc = new VpcStack(this, `${stackPrefix}-Vpc`, {
            stackCreationInfo,
            terminationProtection,
        });

        const dns = new DnsStack(this, `${stackPrefix}-Dns`, {
            stackCreationInfo,
            terminationProtection,
        });

        new EcsServiceStack(this, `${stackPrefix}-EcsService`, {
            vpc,
            dns,
            stackCreationInfo,
            terminationProtection,
        });

    }
}
import {Duration, Stack} from 'aws-cdk-lib';
import {Construct} from 'constructs';
import {AwsLogDriver, Cluster, ContainerImage, DeploymentControllerType} from 'aws-cdk-lib/aws-ecs';
import {SERVICE_NAME} from '../constant';
import {VpcStack} from './vpc';
import {DnsStack} from './dns';
import {StackCreationInfo} from '../stack-creation-info';
import {DockerImageAsset} from 'aws-cdk-lib/aws-ecr-assets';
import * as path from 'node:path';
import {ApplicationLoadBalancedFargateService} from 'aws-cdk-lib/aws-ecs-patterns';
import {LogGroup} from 'aws-cdk-lib/aws-logs';
import {ApplicationProtocol, Protocol} from 'aws-cdk-lib/aws-elasticloadbalancingv2';

export interface EcsServiceStackProps {
    readonly vpc: VpcStack;
    readonly dns: DnsStack;
    readonly stackCreationInfo: StackCreationInfo;
    readonly terminationProtection?: boolean;
}

export class EcsServiceStack extends Stack {
    constructor(scope: Construct, id: string, props: EcsServiceStackProps) {
        super(scope, id, props);

        const {stage, stackPrefix} = props.stackCreationInfo;

        const serviceHostedZone = props.dns.hostedZone;
        const INTERNAL_HTTP_PORT = 8050;
        const HTTPS_PORT = 443;
        const cpuUnits = 256;
        const memoryMiB = 512;
        const HEALTH_CHECK_PATH = '/';

        const cluster = new Cluster(this, `${stackPrefix}-Cluster`, {
            clusterName: `${stackPrefix}-Cluster`,
            vpc: props.vpc.vpc,
        });

        const asset = new DockerImageAsset(this, `${stackPrefix}-ServiceImage`, {
            directory: path.join(__dirname, '../../../'),
        });

        const service = new ApplicationLoadBalancedFargateService(this, `${stackPrefix}-Service`, {
            assignPublicIp: true,
            circuitBreaker: {rollback: true},
            cluster,
            cpu: cpuUnits,
            memoryLimitMiB: memoryMiB,
            deploymentController: {
                type: DeploymentControllerType.ECS,
            },
            desiredCount: 1,
            taskImageOptions: {
                containerName: SERVICE_NAME,
                image: ContainerImage.fromDockerImageAsset(asset),
                environment: {
                    STAGE: stage,
                },
                enableLogging: true,
                logDriver: new AwsLogDriver({
                    streamPrefix: `${SERVICE_NAME}`,
                    logGroup: new LogGroup(this, `${SERVICE_NAME}-application-log-group`),
                }),
                // taskRole: serviceExecutionRole,
                containerPort: INTERNAL_HTTP_PORT,
            },
            loadBalancerName: `${stackPrefix}-ALB`,
            maxHealthyPercent: 200,
            minHealthyPercent: 100,
            openListener: true,
            publicLoadBalancer: true,
            serviceName: `${stage}-${SERVICE_NAME}`,
            targetProtocol: ApplicationProtocol.HTTP, // ALB to server
            protocol: ApplicationProtocol.HTTPS,
            listenerPort: HTTPS_PORT,
            certificate: props.dns.certificate,
            domainName: serviceHostedZone.zoneName,
            domainZone: serviceHostedZone,
        });

        service.targetGroup.configureHealthCheck({
            path: HEALTH_CHECK_PATH,
            protocol: Protocol.HTTP,
            healthyHttpCodes: '200',
            interval: Duration.seconds(5),
            timeout: Duration.seconds(2),
            unhealthyThresholdCount: 2,
        });
    }
}

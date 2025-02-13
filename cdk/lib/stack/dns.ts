import {Stack} from 'aws-cdk-lib';
import {Construct} from 'constructs';
import {DOMAIN, SERVICE_NAME} from '../constant';
import {HostedZone, IHostedZone} from 'aws-cdk-lib/aws-route53';
import {Certificate, CertificateValidation} from 'aws-cdk-lib/aws-certificatemanager';
import {StackCreationInfo} from '../stack-creation-info';

export interface DnsStackProps {
    readonly stackCreationInfo: StackCreationInfo;
    readonly terminationProtection?: boolean;
}

export class DnsStack extends Stack {
    public readonly hostedZone: IHostedZone;
    public readonly certificate: Certificate;

    constructor(scope: Construct, id: string, props: DnsStackProps) {
        super(scope, id, props);

        const {stage, stackPrefix} = props.stackCreationInfo;

        this.hostedZone = HostedZone.fromLookup(this, `${stackPrefix}-HostedZone`, {domainName: DOMAIN});

        this.certificate = new Certificate(this, 'Certificate', {
            domainName: this.hostedZone.zoneName,
            certificateName: `${SERVICE_NAME}-${stage}-certificate`,
            validation: CertificateValidation.fromDns(this.hostedZone),
        });

    }
}
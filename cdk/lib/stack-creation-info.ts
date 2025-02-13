import {Environment} from 'aws-cdk-lib';
import {STAGE} from './enum/stage';
import {REGION} from './enum/region';

/**
 * Stack creation info is used in each stack creation
 **/
export class StackCreationInfo {
    account: string; // AWS Account ID
    region: REGION;
    stage: STAGE;
    organization: string; // Organization name
    stackPrefix: string;

    /**
     *
     * @param account - the AWS account ID
     * @param region - the AWS region that stacks should be deployed to.
     * @param stage - the deployment stage
     * @param organization - the organization that this stack belongs to.
     */
    constructor(
        region: REGION,
        stage: STAGE,
        organization: string,
        account: string = process.env.CDK_DEFAULT_ACCOUNT!,
    ) {
        this.account = account;
        this.region = region;
        this.stage = stage;
        this.organization = organization;
        this.stackPrefix = `${organization}-${region}-${stage}`;
    }

    getEnvironment(): Environment {
        return {
            account: this.account,
            region: this.region.toString(),
        };
    }
}
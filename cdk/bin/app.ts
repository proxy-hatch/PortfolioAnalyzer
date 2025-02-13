#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import {STAGE} from '../lib/enum/stage';
import {ORGANIZATION_NAME, SERVICE_NAME} from '../lib/constant';
import {StackCreationInfo} from '../lib/stack-creation-info';
import {REGION} from '../lib/enum/region';
import {DeploymentStacks} from '../lib/stack/deployment-stacks';

const app = new cdk.App();

const stackCreationInfo = new StackCreationInfo(
    REGION.USW2,
    STAGE.DEV,
    ORGANIZATION_NAME,
);

new DeploymentStacks(app, `${stackCreationInfo.stackPrefix}-DeploymentStacks`, {
    env: stackCreationInfo.getEnvironment(),
    stackCreationInfo,
});


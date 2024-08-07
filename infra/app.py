# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import boto3

from botocore.exceptions import ClientError
from aws_cdk import App, Environment
from aws_cdk import aws_ec2 as ec2

from lib.backend import BackendStack
from lib.frontend import FrontendStack

# Get path of current script's parent directory
current_dir = os.path.dirname(__file__)
# Parent Directory
parent_dir = os.path.dirname(current_dir)
# Source Directory
src_dir = os.path.join(parent_dir, "src")
# Frontend Directory
frontend_dir = os.path.join(src_dir, "frontend")
# Backend Directory
backend_dir = os.path.join(src_dir, "backend")


def get_backend_url(stack_name):
    cfn_client = boto3.client('cloudformation')
    try:
        response = cfn_client.describe_stacks(StackName=stack_name)
        outputs = response['Stacks'][0]['Outputs']
        for output in outputs:
            if output['OutputKey'] == 'BackendURL':
                return output['OutputValue']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            print("Backend stack not found. Running synthesis with assumed defaults..")
        else:
            print(f"An error occurred: {e}")
        return None


app = App()
env = Environment(account=os.environ.get("CDK_DEFAULT_ACCOUNT", None),
                  region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"))

# Deploy backend stack
backend = BackendStack(app, "BedrockDemo-BackendStack",
                       backend_dir=backend_dir,
                       env=env
                       )

backend_url = get_backend_url("BedrockDemo-BackendStack")
if not backend_url:
    backend_url = "http://localhost:5000"

# Deploy frontend stack
frontend = FrontendStack(app, "BedrockDemo-FrontendStack",
                         frontend_path=frontend_dir,
                         proxy_url=backend_url,
                         env=env
                         )

app.synth()

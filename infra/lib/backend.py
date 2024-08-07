# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Stack,
    aws_ecr_assets as ecr_assets,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct
import aws_cdk.aws_apprunner_alpha as apprunner_alpha

class BackendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, backend_dir: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Backend Docker image
        backend_image = ecr_assets.DockerImageAsset(
            self, "BackendDockerImage",
            directory=backend_dir,
            platform=ecr_assets.Platform.LINUX_AMD64,
        )

        # App Runner service using the alpha module
        app_runner_service = apprunner_alpha.Service(
            self, "CarPartsAssistantService",
            source=apprunner_alpha.Source.from_asset(
                asset=backend_image,
                image_configuration=apprunner_alpha.ImageConfiguration(
                    port=5000  # Assuming your backend still listens on port 5000
                )
            ),
            cpu=apprunner_alpha.Cpu.FOUR_VCPU,
            memory=apprunner_alpha.Memory.TWELVE_GB
        )

        app_runner_service.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"],
            )
        )

        # Outputs
        self.backend_url = CfnOutput(
            self,
            "BackendURL",
            value="https://"+app_runner_service.service_url,
            description="URL of the Bedrock React Demo Backend",
        )

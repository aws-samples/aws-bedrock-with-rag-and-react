# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    CfnOutput,
    RemovalPolicy,
    BundlingOptions,
    DockerImage,
)
from constructs import Construct

class FrontendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, 
                 frontend_path: str, proxy_url: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Create a private S3 bucket to host the React app
        hosting_bucket = s3.Bucket(
            self, "ReactAppHostingBucket",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,  # Use with caution in production
            auto_delete_objects=True,  # Use with caution in production
        )

        # Update proxy.js with the provided proxy_url or a placeholder
        proxy_file_content = f"""
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

const proxy_url = "{proxy_url}";

export default proxy_url;
"""

        # Deploy the React app build to S3
        s3deploy.BucketDeployment(
            self, "DeployReactApp",
            sources=[s3deploy.Source.asset(
                frontend_path,
                bundling=BundlingOptions(
                    image=DockerImage.from_registry("public.ecr.aws/docker/library/node:lts-slim"),
                    command=[
                        "bash", "-c",
                        f'''
                        npm install
                        echo '{proxy_file_content}' > src/proxy.js
                        npm run build
                        cp -r build/* /asset-output/
                        '''
                    ],
                    user="root"
                )
            )],
            destination_bucket=hosting_bucket,
            prune=False,
        )

        # CloudFront Origin Access Identity
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, "OriginAccessIdentity",
            comment=f"OAI for {construct_id}"
        )

        # Grant read permissions to CloudFront
        hosting_bucket.add_to_resource_policy(iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[hosting_bucket.arn_for_objects("*")],
            principals=[iam.CanonicalUserPrincipal(
                origin_access_identity.cloud_front_origin_access_identity_s3_canonical_user_id
            )]
        ))

        # Create a CloudFront distribution
        self.distribution = cloudfront.Distribution(
            self, "ReactAppDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    hosting_bucket,
                    origin_access_identity=origin_access_identity
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
            ],
        )

        # Output the CloudFront distribution URL
        CfnOutput(
            self, "FrontendURL",
            value=f"https://{self.distribution.distribution_domain_name}",
            description="Frontend Application URL",
        )
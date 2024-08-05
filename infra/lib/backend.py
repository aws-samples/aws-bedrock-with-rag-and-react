from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr_assets as ecr_assets,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
    CfnOutput,
)
from constructs import Construct

class BackendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, backend_dir: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Get the parent domain from CDK context
        parent_domain = self.node.try_get_context("parent_domain")
        if not parent_domain:
            raise ValueError("parent_domain must be provided in CDK context")

        # Construct the full domain name (you can adjust this as needed)
        domain_name = f"api.{parent_domain}"

        # VPC
        vpc = ec2.Vpc(self, "CarPartsAssistantVPC", max_azs=2)

        # ECS Cluster
        cluster = ecs.Cluster(self, "CarPartsAssistantCluster", vpc=vpc)

        # Backend Docker image
        backend_image = ecs.ContainerImage.from_asset(
            directory=backend_dir,
            platform=ecr_assets.Platform.LINUX_AMD64,
        )

        # Look up the hosted zone
        hosted_zone = route53.HostedZone.from_lookup(
            self, "Zone", domain_name=parent_domain
        )

        # Create an SSL certificate
        certificate = acm.Certificate(
            self, "Certificate",
            domain_name=domain_name,
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )

        # Fargate service with HTTPS
        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "CarPartsAssistantService",
            cluster=cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=backend_image,
                container_port=5000,
            ),
            public_load_balancer=True,
            certificate=certificate,
            protocol=elbv2.ApplicationProtocol.HTTPS,
            redirect_http=True,
        )

        # Create A record for the backend URL
        route53.ARecord(
            self, "BackendARecord",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(
                targets.LoadBalancerTarget(self.fargate_service.load_balancer)
            ),
            record_name=domain_name
        )

        # Grant permissions to invoke Bedrock
        self.fargate_service.task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"],
            )
        )

        # Modify Health Check
        self.fargate_service.target_group.configure_health_check(path="/health")

        # Outputs
        self.backend_url = CfnOutput(
            self,
            "BackendURL",
            value=f"https://{domain_name}",
            description="URL of the Bedrock React Demo Backend",
        )
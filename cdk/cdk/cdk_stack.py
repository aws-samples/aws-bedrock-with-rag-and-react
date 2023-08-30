from aws_cdk import (
    Stack,
    aws_cognito as _cognito,
    Aspects
)
import aws_cdk as _cdk_core
from constructs import Construct
import cdk_nag


class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ## userpool for api access
        demo_userpool = _cognito.UserPool(
            self, "DemoPool",
            advanced_security_mode=_cognito.AdvancedSecurityMode.ENFORCED,
            password_policy=_cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_digits=True,
                require_symbols=True,
                require_uppercase=True
            )
        )

        ## api pool client for registration
        api_pool_client = demo_userpool.add_client("app-client")


        ## output the ARN of our cognito client_id for user sign up
        _cdk_core.CfnOutput(
            self, 'cognito_userpool_client_id',
            value=demo_userpool.user_pool_id
        )

        ## output the ARN of our cognito client_id for user sign up
        _cdk_core.CfnOutput(
            self, 'cognito_app_client_id',
            value=api_pool_client.user_pool_client_id
        )

        Aspects.of(self).add(cdk_nag.AwsSolutionsChecks(verbose=True))
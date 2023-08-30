// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT.

/* eslint-disable */

const awsmobile = {
    // edit these four values using region & outputs from CDK
    "aws_project_region": "",
    "aws_cognito_region": "",
    "aws_user_pools_id": "",
    "aws_user_pools_web_client_id": "",


    
    "aws_cognito_username_attributes": [
        "EMAIL","USERNAME"
    ],
    "aws_cognito_password_protection_settings": {
        "passwordPolicyMinLength": 8,
        "passwordPolicyCharacters": []
    },
    "aws_cognito_verification_mechanisms": [
        "EMAIL"
    ]
};


export default awsmobile;
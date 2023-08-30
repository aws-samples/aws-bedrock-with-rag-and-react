# RAG with AWS Bedrock and React

Use this solution to quickly and inexpensively begin prototyping and vetting business use cases for GenAI using a custom corpus of knowledge with Retrieval Augmented Generation (RAG) in a low-code ReactJS application.

This solution contains a backend Flask application which uses LangChain to provide PDF data as embeddings to your choice of text-gen foundational model via Amazon Web Services (AWS) new, managed LLM-provider service, Amazon Bedrock and your choice of vector database with FAISS or a Kendra Index.

The only cost-generating AWS resources this solution uses are Amazon Cognito and Amazon Bedrock.


## What You'll Build

![Bedrock Demo Architecture](bedrock-demo-arch.png)

## Screenshots

![Bedrock Demo FrontEnd](bedrock_demo_mov.gif)


## Prerequisites

You'll need to install all prerequisites on your local operating machine.

    
For the Flask backend, you'll need to have:
1. [Python 3.8 or higher](https://www.python.org/downloads/macos/)
2. Set up the SDK for Python (Boto3) and AWS CLI
    - Boto3 & Botocore: `pip3 install ./backend/flask/boto3-1.26.162-py3-none-any.whl ./backend/flask/botocore-1.29.162-py3-none-any.whl`
    - AWS CLI: [Instructions Here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3. Install the requirements using the requirements file with `pip3 install -r ./backend/flask/requirements.txt`


For the React frontend, you'll need to install the following:
1. [Node.js & npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
2. Install the NPM dependencies with `npm install`
3. Deploy our Cognito UserPool with cdk. To do this:
    - `cd cdk`
    - Next, we should create and activate a python virtual envrionment. This allows us the ability to contain our python and python package version requirements without conflicting with other versions on our local system. 
        1. `python3 -m venv .venv`
        2. `source .venv/bin/activate`
    - Next, install the python dependencies with: `python3 -m pip install -r requirements.txt`
    - We can now bootstrap our environment with: `cdk bootstrap aws://<account number>/<region> --profile <profile>` (--profile flag is optional, remove if you want to use default aws cli credentials)

>If "No module named 'aws_cdk' error" on Step 4, or earlier:
>   Run `npm install -g aws-cdk@latest`

4. We can now deploy the CDK project with: `cdk deploy --profile <profile>` (--profile flag is optional, remove if you want to use default aws cli credentials)
5. CDK will print Outputs following deployment of the resources therein. You'll need to update a few commands and variables found in `./src/aws-exports.js` using the output values:
    - Use the value of `CdkStack.cognitoappclientid` to update the value for `aws_user_pools_web_client_id`
    - Use the value of `CdkStack.cognitouserpoolclientid` to update the value for `aws_user_pools_id`
    - Be sure to update any values for region that do not match the region you deployed the CDK app in.
6. The CDK deployment does not handle creating a user in the user-pool. To do this, head into the AWS Cognito Console, click the userpool you created `DemoPoolxxxxxxxxxxxxx`, and click `Create user`. ***Important: The username field must be a full email address and not just an alias.


## IAM Permission

Your flask backend will need permissions to call the Bedrock API. More specifically, it should have least privileged access to Invoke foundational models in Bedrock. To do this, you'll need to create an IAM user with the appropriate permissions, then generate access keys (cli credentials). Complete documentation of Bedrock IAM Reference configurations [found here.](https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonbedrock.html)

1. From the IAM console, perform the following steps:
2. Select the IAM Group associated with your user.
3. Click on "Add Permissions" and choose "Create Inline Policies" from the dropdown list.
4. Create a new inline policy and include the following permissions:
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "*"
    }
  ]
}
```

6. Create programmatic access keys/CLI credentials.
7. Run `aws configure --profile <name_of_profile>'
7. On line 62 of `backend/flask/app.py`, include the name of your AWS CLI Profile you configured.


## How to Run

1. In one terminal session, cd into `./backend/flask` and execute `flask run`
2. In another terminal session, make sure your terminal cursor is anywhere inside of this repository's directory and execute `npm start`. The app will run in development mode and made available at http://localhost:3000/


## How to Use

Once you confirm that the app(s) are running, you can begin prototyping. 


### Add Your Own Corpus for RAG Embeddings 

PDF data is read from `./backend/flask/output` and stored in an in-memory vector database using FAISS when the Flask app is started. If you add or remove PDF data from the `./backend/flask/output` directory, you'll need to restart the Flask application for the changes to take effect.

Alternatively, you can use the database button in the lower right corner of the application to add or remove PDF documents manually or from S3 and subsequently reinstantiate the in-memory vector database, or instantiate a connection to a Kendra index. 


### Prompt Engineering with LangChain

Use the </> button just above the database button to update the Prompt Template: explicit instructions for how a text-gen model should respond.

Foundational Models are trained in specific ways to interact with prompts. Check out the [Claude Documentation Page](https://docs.anthropic.com/claude/docs) to learn best practices and find examples of pre-engineered prompts.


## License

This library is licensed under the MIT-0 License. See the LICENSE file.
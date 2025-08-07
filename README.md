# RAG with AWS Bedrock and React

Use this solution to quickly and inexpensively begin prototyping and vetting business use cases for GenAI using a custom corpus of knowledge with Retrieval Augmented Generation (RAG) in a low-code ReactJS application.

This solution contains a backend Flask application which uses LangChain to provide PDF data as embeddings to your choice of text-gen foundational model via Amazon Web Services (AWS) new, managed LLM-provider service, Amazon Bedrock and your choice of vector database with FAISS or a Kendra Index.

## What You'll Build

![Bedrock Demo Architecture](bedrock-demo-arch.png)

## Screenshots

![Bedrock Demo FrontEnd](bedrock_demo_mov.gif)

## Prerequisites

1. [Docker](https://www.docker.com/) or compatible software such as [Colima](https://github.com/abiosoft/colima?tab=readme-ov-file#features)
1. [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) including bootstrap and setting `CDK_DEFAULT_ACCOUNT`
2. [Node.js & npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
3. [Python 3.8 or higher](https://www.python.org/downloads/macos/)
4. AWS CLI configured with appropriate permissions

## How to Deploy

1. Clone the repository and navigate to the project directory.

2. Install the Python dependencies for the CDK Deployment:

    ```
    pip install -r requirements.txt
    ```

3. Bootstrap CDK (if not already done):
   If this is your first time using CDK in this AWS account and region, you need to bootstrap CDK. This command deploys a CDK toolkit stack to your account that helps with asset management:
   ```
   cdk bootstrap aws://YOUR_ACCOUNT_NUMBER/YOUR_REGION
   ```
   Replace `YOUR_ACCOUNT_NUMBER` with your AWS account number and `YOUR_REGION` with your desired AWS region.


4. Deploy the Backend CDK stack. 

    ``` 
    cdk deploy BedrockDemo-BackendStack
    ```

4. Redeploy the frontend stack to update the proxy URL:

    ```
    cdk deploy BedrockDemo-FrontendStack
    ```

Your application should now be accessible at the frontend URL provided by the CDK output.

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

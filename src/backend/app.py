# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from flask import Flask, render_template, request, jsonify
import requests
import json
import os
import boto3
from langchain.chains import ConversationalRetrievalChain
from langchain.schema import BaseMessage
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.llms.bedrock import Bedrock
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.schema import BaseMessage
from langchain.llms.bedrock import Bedrock
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.indexes import VectorstoreIndexCreator
from langchain.document_loaders.pdf import (
    PyPDFDirectoryLoader
)
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import concurrent.futures
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import time
import base64
from urllib.parse import urljoin
from urllib.parse import urlparse
from flask_cors import CORS
from langchain_community.retrievers import AmazonKendraRetriever
from opensearchpy import OpenSearch
from opensearchpy.connection import RequestsHttpConnection
from threading import Lock
from argparse import ArgumentTypeError

app = Flask(__name__)
# Enable CORS for all routes and all origins
CORS(app, resources={r"/*": {"origins": "*"}})

aws_region = 'us-west-2'
aws_service = 'bedrock'
chathistory = []
chathistory1 = []

aws_cli_profile_name = ''
session = boto3.Session()
bedrock_client = session.client(service_name='bedrock-runtime', region_name=aws_region)
pdf_directory = './output'

# We are also providing a different chat history retriever which outputs the history as a Claude chat (ie including the \n\n)
_ROLE_MAP = {"human": "\n\nHuman: ", "ai": "\n\nAssistant: "}
def _get_chat_history(chat_history):
    buffer = ""
    for dialogue_turn in chat_history:
        if isinstance(dialogue_turn, BaseMessage):
            role_prefix = _ROLE_MAP.get(dialogue_turn.type, f"{dialogue_turn.type}: ")
            buffer += f"\n{role_prefix}{dialogue_turn.content}"
        elif isinstance(dialogue_turn, tuple):
            human = "\n\nHuman: " + dialogue_turn[0]
            ai = "\n\nAssistant: " + dialogue_turn[1]
            buffer += "\n" + "\n".join([human, ai])
        else:
            raise ValueError(
                f"Unsupported chat history format: {type(dialogue_turn)}."
                f" Full chat history: {chat_history} "
            )
    return buffer

_template_new = """
Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.
Chat History:
{chat_history}
Follow Up Input: {question}

"""

CONDENSE_QUESTION_PROMPT1 = PromptTemplate.from_template(_template_new)

memory_chain = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

def input_validation(input_str):
    pattern = r'^[a-zA-Z0-9\s\-!@#$%^&*(),.?":{}|<>]{1,1000}'
    if re.match(pattern, input_str):
        return True
    else:
        return False

app.config['UPLOAD_FOLDER'] = 'output'
lock = Lock()
vectordatabase_intialized = False


class VectorDatabase:
    def __init__(self):
        self.br_embeddings = None
        self.vectorstore_faiss_aws = None
        self.kendra_client = None
        self.kendra_retriever = None
        self.vector_initialized = False
        self.prompt_template = "Use the context to answer the question at the end. If you don't know the answer from the context, do not answer from your knowledge and be precise. Dont fake the answer."

    def update_prompt_template(self, template):
        self.prompt_template = template
        return True

    def destroy_vector_db(self):
        self.vectorstore_faiss_aws = None
        self.vector_initialized = False

    def initialize_vector_db(self, pdf_directory):
        # # Initialize Bedrock embeddings
        self.br_embeddings = BedrockEmbeddings(client=bedrock_client, model_id='amazon.titan-embed-text-v1')
        print(f"br_embeddings: {self.br_embeddings}")

        # Create the local download folder if it doesn't exist
        if not os.path.exists(pdf_directory):
            os.makedirs(pdf_directory)

        
        loader = PyPDFDirectoryLoader(pdf_directory)
        documents = loader.load()
        
        if not documents:
            print("No documents found. Skipping vector database initialization.")
            return ("No documents found. Skipping vector database initialization.")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap  = 100,
            separators = ["\n\n", "\n", " ", "",',']
        )
        docs = text_splitter.split_documents(documents)
        print(f"Number of documents after split and chunking={len(docs)}")
        self.vectorstore_faiss_aws = FAISS.from_documents(
            documents=docs,
            embedding=self.br_embeddings
        )
        self.vector_initialized = True
        print(f"vectorstore_faiss_aws: number of elements in the index={self.vectorstore_faiss_aws.index.ntotal}::")


    

    def instantiate_kendra(self, profile_name, index_id):
        try:
            session = boto3.Session(profile_name=profile_name)
            self.kendra_client = session.client(service_name='kendra', region_name=aws_region)
            self.kendra_retriever = AmazonKendraRetriever(client=self.kendra_client, index_id=index_id)
            return True
        except Exception as e:
            return e

    def download_files_s3(self, profile, location):
        print('starting s3 download')
        s3_session = boto3.Session(
            profile_name=profile
        )
        print(profile)
        print(location)
        s3_client = s3_session.client('s3')
        bucket_name = location.split('/')[2]
        prefix = '/'.join(location.split('/')[3:])
        if prefix.endswith('/'):
            prefix = prefix.split('/')[0]
        
        objects = s3_client.list_objects(Bucket=bucket_name, Prefix=prefix)

        # Create the local download folder if it doesn't exist
        if not os.path.exists(pdf_directory):
            os.makedirs(pdf_directory)

        # Download each object from the bucket
        for obj in objects['Contents']:
            file_key = obj['Key']
            file_name = file_key.split('/')[-1]
            local_filename = os.path.join(pdf_directory, file_name)
            s3_client.download_file(bucket_name, file_key, local_filename)
            print(f"Downloaded: {file_key} -> {local_filename}")
        
        download_count = len(objects['Contents'])
        return download_count

vector_database = VectorDatabase()
vector_database.initialize_vector_db(pdf_directory)

### claude
@app.route('/api/conversation/predict-claude', methods=['POST','PUT'])
def predict_conversation1():
    vectorstore_faiss_aws = vector_database.vectorstore_faiss_aws
    payload = request.get_json()
    cl_llm = Bedrock(model_id="anthropic.claude-sonnet-4", client=bedrock_client, model_kwargs={"max_tokens_to_sample": 4000}) # Updated to Claude Sonnet 4.0
    print(payload)
    body = json.loads(payload['body'])
    question = body.get('prompt', '')
    if input_validation(question):
        print("question:",question)
        #memory_chain.chat_memory.add_user_message(question)
        qa = ConversationalRetrievalChain.from_llm(
            llm=cl_llm,
            retriever=vectorstore_faiss_aws.as_retriever(),
            memory=memory_chain,
            #get_chat_history=_get_chat_history,
            verbose = True,
            condense_question_prompt=CONDENSE_QUESTION_PROMPT1,
            chain_type='stuff',
        )
        # the LLMChain prompt to get the answer. the ConversationalRetrievalChange does not expose this parameter in the constructor
        qa.combine_docs_chain.llm_chain.prompt = PromptTemplate.from_template("""
        {context}
        %s
        <q>{question}</q>
        """ % (
            vector_database.prompt_template
        ))
        trychat = chathistory1
        chat_history = trychat
        print("chat_history:",chat_history)
        trychat.append((question, ''))
        print(CONDENSE_QUESTION_PROMPT1.template)
        prediction = qa.run(question=question)
        print("prediction:",prediction)
        #memory_chain.chat_memory.add_ai_message(prediction)
        return jsonify(prediction)

### claude
@app.route('/api/conversation/predict-claude-kendra', methods=['POST','PUT'])
def predict_conversation_kendra():
     # Get the input from the request payload
    #print the langchain version
    payload = request.get_json()

    # Updated to Claude Sonnet 4.0
    cl_llm = Bedrock(model_id="anthropic.claude-sonnet-4", client=bedrock_client, model_kwargs={"max_tokens_to_sample": 4000})
    memory_chain = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    qa = ConversationalRetrievalChain.from_llm(
        llm=cl_llm,
        retriever=vector_database.kendra_retriever,
        memory=memory_chain,
        get_chat_history=_get_chat_history,
        verbose = True,
        condense_question_prompt=CONDENSE_QUESTION_PROMPT1,
        chain_type='stuff',
    )

    # the LLMChain prompt to get the answer. the ConversationalRetrievalChange does not expose this parameter in the constructor
    qa.combine_docs_chain.llm_chain.prompt = PromptTemplate.from_template("""

    {context}

    Human: %s
    <q>{question}</q>


    Assistant:""" % (
        vector_database.prompt_template
    ))

    print(payload)
    # Get the input text from the payload
    body = json.loads(payload['body'])
    question = body.get('prompt', '')
    print("question:",question)
    if input_validation(question):
        #question = payload['question']

        trychat = chathistory1
        chat_history = trychat 
        print("chat_history:",chat_history)
        
        # Append the new question to the chat history
        trychat.append((question, ''))
        # Generate the prediction from the Conversational Retrieval Chain
        print(CONDENSE_QUESTION_PROMPT1.template)
        prediction = qa.run(question=question)
        print("prediction:",prediction)
        
        # Return the prediction as a JSON response
        return jsonify(prediction)

@app.route('/api/build-vector', methods=['POST','PUT'])
def crawl_build_vector():
    payload = request.json
    print(payload)
    try:
        # Force reinitialization of the vector database
        print("Reinitializing vector database...")
        vector_database.destroy_vector_db()  # Clear any existing database
        result = vector_database.initialize_vector_db('./output')
        
        # Check if initialization was successful
        if vector_database.vector_initialized:
            print("Vector database successfully initialized")
            if vector_database.vectorstore_faiss_aws:
                doc_count = vector_database.vectorstore_faiss_aws.index.ntotal
                print(f"Vector database contains {doc_count} documents")
            response = {
                'response_text': f'Vector database initialized successfully with {doc_count} documents.'
            }
        else:
            print("Vector database initialization failed")
            response = {
                'response_text': 'Vector database initialization failed. ' + str(result)
            }
    except Exception as e:
        print(f"Error initializing vector database: {e}")
        response = {
            'response_text': f'Error initializing vector database: {str(e)}'
        }
    
    return jsonify(response)

@app.route('/api/check-vector', methods=['GET'])
def check_vector():
    """
    Check if the vector database is initialized
    """
    is_initialized = vector_database.vector_initialized
    print(f"DEBUG: Vector database initialization status: {is_initialized}")
    
    # Check if FAISS index exists and has documents
    has_documents = False
    doc_count = 0
    if vector_database.vectorstore_faiss_aws is not None:
        try:
            doc_count = vector_database.vectorstore_faiss_aws.index.ntotal
            has_documents = doc_count > 0
            print(f"DEBUG: FAISS index has {doc_count} documents")
            
            # If we have documents but vector_initialized is False, fix it
            if has_documents and not is_initialized:
                vector_database.vector_initialized = True
                is_initialized = True
                print("DEBUG: Fixed vector_initialized flag based on document count")
        except Exception as e:
            print(f"DEBUG: Error checking FAISS index: {e}")
    
    response = {
        'vector_initialized': str(is_initialized),
        'has_documents': str(has_documents),
        'document_count': doc_count
    }
    return jsonify(response)

@app.route('/api/force-initialize-vector', methods=['GET', 'POST'])
def force_initialize_vector():
    """
    Force reinitialization of the vector database
    """
    try:
        print("Force reinitializing vector database...")
        # First check if there are PDF files in the output directory
        if not os.path.exists(pdf_directory):
            os.makedirs(pdf_directory)
            
        pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
        pdf_count = len(pdf_files)
        
        if pdf_count == 0:
            return jsonify({
                'success': False,
                'message': 'No PDF files found in the output directory. Please upload PDFs first.'
            })
        
        # Clear any existing database
        vector_database.destroy_vector_db()
        
        # Reinitialize with existing PDFs
        vector_database.initialize_vector_db(pdf_directory)
        
        if vector_database.vector_initialized and vector_database.vectorstore_faiss_aws:
            doc_count = vector_database.vectorstore_faiss_aws.index.ntotal
            return jsonify({
                'success': True,
                'message': f'Vector database successfully initialized with {doc_count} documents from {pdf_count} PDF files.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Vector database initialization failed.'
            })
    except Exception as e:
        print(f"Error in force_initialize_vector: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

if __name__ == "__main__":
    print("Starting Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)

### Agent capabilities
@app.route('/api/agent/execute', methods=['POST'])
def execute_agent_action():
    """
    Execute agent actions like web search, browser control, etc.
    """
    payload = request.get_json()
    action_type = payload.get('action_type')
    action_params = payload.get('params', {})
    
    response = {
        'success': False,
        'data': None,
        'message': 'Unknown action type'
    }
    
    try:
        if action_type == 'web_search':
            # Perform a web search using a search API
            query = action_params.get('query', '')
            if not query:
                response['message'] = 'Search query is required'
                return jsonify(response)
                
            # This would typically use a search API like Google Custom Search
            # For demo purposes, we'll return a mock response
            search_results = [
                {'title': f'Result for {query} 1', 'link': f'https://example.com/1?q={query}', 'snippet': f'This is a sample result for {query}...'},
                {'title': f'Result for {query} 2', 'link': f'https://example.com/2?q={query}', 'snippet': f'Another sample result for {query}...'},
            ]
            
            response['success'] = True
            response['data'] = search_results
            response['message'] = f'Found {len(search_results)} results for "{query}"'
            
        elif action_type == 'open_browser':
            # In a real implementation, this would use a browser automation library
            # For demo purposes, we'll just return success
            url = action_params.get('url', 'https://www.google.com')
            
            # In production, you would use something like Selenium to control a browser
            # driver = webdriver.Chrome()
            # driver.get(url)
            
            response['success'] = True
            response['message'] = f'Browser opened with URL: {url}'
            
        elif action_type == 'read_webpage':
            url = action_params.get('url', '')
            if not url:
                response['message'] = 'URL is required'
                return jsonify(response)
                
            try:
                # In production, you would handle this more robustly
                page_content = requests.get(url).text
                soup = BeautifulSoup(page_content, 'html.parser')
                
                # Extract text content
                text = soup.get_text(separator='\n', strip=True)
                
                response['success'] = True
                response['data'] = {'text': text[:5000]}  # Limit text size
                response['message'] = f'Successfully read content from {url}'
            except Exception as e:
                response['message'] = f'Error reading webpage: {str(e)}'
        
        else:
            response['message'] = f'Unsupported action type: {action_type}'
    
    except Exception as e:
        response['message'] = f'Error executing agent action: {str(e)}'
    
    return jsonify(response)
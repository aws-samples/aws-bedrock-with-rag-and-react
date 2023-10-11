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
from langchain import PromptTemplate
from langchain.llms.bedrock import Bedrock
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
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
from langchain.retrievers import AmazonKendraRetriever
from opensearchpy import OpenSearch
from opensearchpy.connection import RequestsHttpConnection
from threading import Lock
from argparse import ArgumentTypeError

app = Flask(__name__)
CORS(app)

aws_region = 'us-west-2'
aws_service = 'bedrock'
chathistory = []

aws_cli_profile_name = ''
session = boto3.Session(profile_name=aws_cli_profile_name)
# session = boto3.Session()
bedrock_client = session.client(service_name='bedrock', region_name=aws_region, endpoint_url='https://bedrock-runtime.'+aws_region+'.amazonaws.com')
pdf_directory = './output'

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

# Helper Functions
def delete_files_in_directory_older_than_7days(directory_path, days_old=7):
    try:
        # Get the current time
        current_time = time.time()

        # Get a list of all files in the directory
        files = os.listdir(directory_path)

        # Loop through the files
        for file_name in files:
            file_path = os.path.join(directory_path, file_name)

            # Check if it's a file and if it's older than 7 days
            if os.path.isfile(file_path) and (current_time - os.path.getmtime(file_path)) > days_old * 86400:
                os.remove(file_path)

        print(f"Files older than {days_old} days in the directory have been deleted.")
    except Exception as e:
        print(f"Error: {e}")

def input_validation(input_str):
    pattern = r'^[a-zA-Z0-9\s\-!@#$%^&*(),.?":{}|<>]{1,1000}$'

    if re.match(pattern, input_str):
        return True
    else:
        return False

def parse_url_from_str(arg):
    url = urlparse(arg)
    if all((url.scheme, url.netloc)):  # possibly other sections?
        return arg  # return url in case you need the parsed object
    raise ArgumentTypeError('Invalid URL')

def remove_unwanted_content(driver, pdf_data):
    # Execute JavaScript to hide specific elements before saving as PDF
    # You can add more JavaScript code here to hide different elements as needed
    hide_elements_js = """
        // Hide elements with specific tags
        var tagsToHide = ['img', 'script', 'style', 'video', 'svg', 'iframe', 'code'];
        tagsToHide.forEach(function(tag) {
            var elements = document.getElementsByTagName(tag);
            for (var i = 0; i < elements.length; i++) {
                elements[i].style.display = 'none';
            }
        });
    """

    ex =  '''      
        // Hide elements with specific class names
        var classNamesToHide = ['advertisement', 'sidebar', 'header'];
        classNamesToHide.forEach(function(className) {
            var elements = document.getElementsByClassName(className);
            for (var i = 0; i < elements.length; i++) {
                elements[i].style.display = 'none';
            }
        });
        '''

    # Execute the JavaScript code in the context of the current page
    driver.execute_script(hide_elements_js)

    # Generate the updated PDF data
    result = send_devtools(driver, "Page.printToPDF", {})
    if (result is not None):
        return base64.b64decode(result['data'])
    else:
        return pdf_data
    
def send_devtools(driver, cmd, params={}):
    resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
    url = driver.command_executor._url + resource
    body = json.dumps({'cmd': cmd, 'params': params})
    response = driver.command_executor._request('POST', url, body)
    if (response.get('value') is not None):
        return response.get('value')
    else:
        return None

def save_as_pdf(driver, path, options={}):
    result = send_devtools(driver, "Page.printToPDF", options)
    if (result is not None):
        with open(path, 'wb') as file:
            pdf_data = base64.b64decode(result['data'])

            pdf_data = remove_unwanted_content(driver, pdf_data)

            file.write(pdf_data)
        return True
    else:
        return False

def delete_files_in_directory(directory_path):
    try:
        files = os.listdir(directory_path)

        for file_name in files:
            file_path = os.path.join(directory_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

        print("All files in the PDF output directory have been deleted.")
    except Exception as e:
        print(f"Error: {e}")

def get_title_from_page(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    return soup.title.string

def collect_links_from_page(url, page_content, prefix):
    soup = BeautifulSoup(page_content, 'html.parser')
    links_set = set()
    for a in soup.find_all('a', href=True):
        if 'href' in a.attrs:
            link = a['href']
            norm_link = url_normalizer(url, link)
            if norm_link is not None:
                if 'login' not in norm_link and is_social_networking_url(norm_link) == False:
                    print(f"Found link: {norm_link}")
                    if prefix.strip() == "" or ((len(prefix.strip()) > 0) and norm_link.startswith(prefix.strip())):
                        links_set.add(norm_link)

    return links_set

# Convert relative links to absolute urls
def url_normalizer(parent_url, link):
    # comparator = 

    if link.startswith('#') or link.startswith('../'):
        link = urljoin(parent_url, link)
    elif link.startswith('/'):
        ## TODO: clean up the hack below. It is incorrect.
        link = urljoin(parent_url, link[1:])
    elif link.startswith('./'):
        link = urljoin(parent_url, link[2:])
    else:
        try:
            parse_url_from_str(link)
        except Exception as e:
            link = urljoin(parent_url, link)

    # Validate that link is a valid URL
    try:
        parse_url_from_str(link)
    except Exception as e:
        print(f'Error normalizing {link} - {e}')
        return
    return link 

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

def is_social_networking_url(url):
    social_networks = ["facebook", "twitter", "instagram", "linkedin", "youtube", "google", "apple"]
    # print('checking url for social network')
    for network in social_networks:
        if re.search(r'\b' + re.escape(network) + r'\b', url, re.IGNORECASE):
            # print('url had social media or otherwise. it should not be included')
            return True
    return False

@app.route('/')
def index():
    return render_template('index.html')

chathistory1 = []


_template_new = """
Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.
Chat History:
{chat_history}
Follow Up Input: {question}

"""

CONDENSE_QUESTION_PROMPT1 = PromptTemplate.from_template(_template_new)


memory_chain = ConversationBufferMemory()

### claude options middleware
@app.route('/api/conversation/claude-middleware', methods=['POST','PUT'])
def claude_middleware():
    # Get the input from the request payload
    #print the langchain version
    payload = request.get_json()    
    body = json.loads(payload['body'])
    vector = body.get('vector')
    if vector == 'faiss':
        print('using faiss vector')
        response = predict_conversation1()
        return response
    if vector == 'kendra':
        print('using kendra vector')
        response = predict_conversation_kendra()
        return response
    
### titan options middleware
@app.route('/api/conversation/titan-middleware', methods=['POST','PUT'])
def titan_middleware():
    # Get the input from the request payload
    #print the langchain version
    payload = request.get_json()    
    body = json.loads(payload['body'])
    vector = body.get('vector')
    if vector == 'faiss':
        print('using faiss vector')
        response = predict_titan()
        return response
    if vector == 'kendra':
        print('using kendra vector')
        response = predict_titan_kendra()
        return response
    
### ai21 options middleware
@app.route('/api/conversation/ai21-middleware', methods=['POST','PUT'])
def ai21_middleware():
    # Get the input from the request payload
    #print the langchain version
    payload = request.get_json()    
    body = json.loads(payload['body'])
    vector = body.get('vector')
    if vector == 'faiss':
        print('using faiss vector')
        response = predict_ai21()
        return response
    if vector == 'kendra':
        print('using kendra vector')
        response = predict_ai21_kendra()
        return response

memory_chain = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

### claude
@app.route('/api/conversation/predict-claude', methods=['POST','PUT'])
def predict_conversation1():
    vectorstore_faiss_aws = vector_database.vectorstore_faiss_aws
    payload = request.get_json()
    cl_llm = Bedrock(model_id="anthropic.claude-v2", client=bedrock_client, model_kwargs={"max_tokens_to_sample": 1000}) # change model_id here
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

    # cl_llm = Bedrock(model_id="anthropic.claude-v1", client=bedrock_client, model_kwargs={"max_tokens_to_sample": 500}) # change model_id here
    cl_llm = Bedrock(model_id="anthropic.claude-v2", client=bedrock_client, model_kwargs={"max_tokens_to_sample": 500}) # change model_id here
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


def extract_text_after_keyword(input_string, keyword):
    start_index = input_string.find(keyword)
    
    if start_index != -1:
        text_after_keyword = input_string[start_index + len(keyword):].strip()
        return text_after_keyword
    else:
        return None


### ai21
@app.route('/api/conversation/predict-ai21', methods=['POST','PUT'])
def predict_ai21():
    vectorstore_faiss_aws = vector_database.vectorstore_faiss_aws
    cl_llm = Bedrock(model_id="ai21.j2-grande-instruct", client=bedrock_client, model_kwargs={"maxTokens": 200, "temperature": 0.5, "topP": 0.5, "stopSequences": [], "countPenalty": {"scale": 0}, "presencePenalty": {"scale": 0}, "frequencyPenalty": {"scale": 0}}) # change model_id here
    
    body = request.json
    question = body['prompt']
    if input_validation(question):
        qa = ConversationalRetrievalChain.from_llm(
            llm=cl_llm,
            retriever=vectorstore_faiss_aws.as_retriever(),
            memory=memory_chain,
            get_chat_history=_get_chat_history,
            verbose = True,
            condense_question_prompt=CONDENSE_QUESTION_PROMPT1,
            chain_type='stuff',
        )
        qa.combine_docs_chain.llm_chain.prompt = PromptTemplate.from_template("""
        {context}

        Human: %s
        <q>{question}</q>

        Assistant:""" % (
            vector_database.prompt_template
        ))

        trychat = chathistory1
        chat_history = trychat 
        print("chat_history:",chat_history)
        
        trychat.append((question, ''))
        print(CONDENSE_QUESTION_PROMPT1.template)
        prediction = qa.run(question=question)
        print('prediction')
        print(prediction)
        # prediction = extract_text_after_keyword(prediction, 'Assistant:')

        print("prediction:",prediction)
        # memory_chain.chat_memory.add_ai_message(prediction)
        return jsonify(prediction)

### ai21 kendra
@app.route('/api/conversation/predict-ai21-kendra', methods=['POST','PUT'])
def predict_ai21_kendra():
    cl_llm = Bedrock(model_id="ai21.j2-grande-instruct", client=bedrock_client, model_kwargs={"maxTokens": 200, "temperature": 0.5, "topP": 0.5, "stopSequences": [], "countPenalty": {"scale": 0}, "presencePenalty": {"scale": 0}, "frequencyPenalty": {"scale": 0}}) # change model_id here
    
    body = request.json
    print(type(body))
    question = body['prompt']
    if input_validation(question):
        print(question)
        memory_chain.chat_memory.add_user_message(question)

        qa = ConversationalRetrievalChain.from_llm(
            llm=cl_llm,
            retriever=vector_database.kendra_retriever,
            memory=memory_chain,
            get_chat_history=_get_chat_history,
            verbose = True,
            condense_question_prompt=CONDENSE_QUESTION_PROMPT1,
            chain_type='stuff',
        )
        qa.combine_docs_chain.llm_chain.prompt = PromptTemplate.from_template("""
        {context}

        Human: %s
        <q>{question}</q>

        Assistant:""" % (
            vector_database.prompt_template
        ))

        trychat = chathistory1
        chat_history = trychat 
        print("chat_history:",chat_history)
        
        trychat.append((question, ''))
        print(CONDENSE_QUESTION_PROMPT1.template)
        prediction = qa.run(question=question)
        # prediction = extract_text_after_keyword(prediction, 'Assistant:')
        print("prediction:",prediction)
        memory_chain.chat_memory.add_ai_message(prediction)
        return jsonify(prediction)

### titan
@app.route('/api/conversation/predict-titan', methods=['POST','PUT'])
def predict_titan():
    vectorstore_faiss_aws = vector_database.vectorstore_faiss_aws
    
    body = request.json
    print(type(body))
    print(body)
    question = body['inputText']
    print(question)
    if input_validation(question):
        cl_llm = Bedrock(model_id='amazon.titan-tg1-large', client=bedrock_client) # change model_id here

        memory_chain.chat_memory.add_user_message(question)

        qa = ConversationalRetrievalChain.from_llm(
            llm=cl_llm,
            retriever=vectorstore_faiss_aws.as_retriever(),
            memory=memory_chain,
            get_chat_history=_get_chat_history,
            verbose = True,
            condense_question_prompt=CONDENSE_QUESTION_PROMPT1,
            chain_type='stuff',
        )
        qa.combine_docs_chain.llm_chain.prompt = PromptTemplate.from_template("""
        {context}

        Human: %s
        <q>{question}</q>

        Assistant:""" % (
            vector_database.prompt_template
        ))

        trychat = chathistory1
        chat_history = trychat 
        print("chat_history:",chat_history)
        
        trychat.append((question, ''))
        print(CONDENSE_QUESTION_PROMPT1.template)
        prediction = qa.run(question=question)
        print("prediction:",prediction)
        memory_chain.chat_memory.add_ai_message(prediction)

        resres = {
            'output_text': prediction
        }
        return resres

### titan kendra
@app.route('/api/conversation/predict-titan-kendra', methods=['POST','PUT'])
def predict_titan_kendra():
    body = request.json
    print(type(body))
    print(body)
    question = body['inputText']
    if input_validation(question):
        print(question)
        cl_llm = Bedrock(model_id='amazon.titan-tg1-large', client=bedrock_client) # change model_id here

        memory_chain.chat_memory.add_user_message(question)

        qa = ConversationalRetrievalChain.from_llm(
            llm=cl_llm,
            retriever=vector_database.kendra_retriever,
            memory=memory_chain,
            get_chat_history=_get_chat_history,
            verbose = True,
            condense_question_prompt=CONDENSE_QUESTION_PROMPT1,
            chain_type='stuff',
        )
        qa.combine_docs_chain.llm_chain.prompt = PromptTemplate.from_template("""
        {context}

        Human: %s
        <q>{question}</q>

        Assistant:""" % (
            vector_database.prompt_template
        ))

        trychat = chathistory1
        chat_history = trychat 
        print("chat_history:",chat_history)
        
        trychat.append((question, ''))
        print(CONDENSE_QUESTION_PROMPT1.template)
        prediction = qa.run(question=question)
        print("prediction:",prediction)
        memory_chain.chat_memory.add_ai_message(prediction)

        resres = {
            'output_text': prediction
        }
        return resres

### stable diffusion
@app.route('/api/call-stablediffusion', methods=['POST','PUT'])
def call_stable_diffusion():
    payload = request.json
    print('stab')
    modelId = 'stability.stable-diffusion-xl'
    accept = 'application/json'
    contentType = 'application/json'
    print(request)
    print(payload['body'])
    print(json.loads(payload['body'])['text_prompts'][0]['text'])
    if input_validation(json.loads(payload['body'])['text_prompts'][0]['text']):
        response = bedrock_client.invoke_model(
            body=payload['body'], 
            modelId=modelId, 
            accept=accept,
            contentType=contentType
        )
        response_body = json.loads(response.get('body').read())
        return response_body

@app.route('/api/crawl', methods=['POST','PUT'])
def crawl_save_pdf():
    OUTPUT_DATA_DIR = './output'
    MAX_WORKERS = 3
    PAGE_LOAD_TIMEOUT = 10 # seconds
    SLEEP_DELAY = 5 # seconds to avoid rate limiting in certain sites
    crawled_pg_cnt = 0
    payload = request.json
    # print(payload)
    delete_files_in_directory_older_than_7days('./output',7)
    crawled = set()
    all_data = []
    content = json.loads(payload.get('prompt'))['prompt']
    allLinks = re.findall(r"https?://[^\s]+", content)
    # Print the URLs for debugging
    # print("Links:")
    print(allLinks)
    good_links = []
    for link in allLinks:
        if re.search("\/$", link):
            url=link
            good_links.append(url)
        else:
            url=link + "/"
            good_links.append(url)

    # Create the "crawledData" folder in the current directory if it doesn't exist
    if not os.path.exists("output"):
        os.makedirs("output")

    ## helper function for crawling
    def crawl(url, max_depth=3, current_depth=1, current_pg_cnt=0, element_id='', prefix=''):
        if url in crawled or current_depth > max_depth:
            return
        crawled.add(url)
        time.sleep(SLEEP_DELAY)
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.headless = True
            # chrome_options.add_argument('--disable-gpu')
            # chrome_options.add_argument("--no-sandbox")

            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(PAGE_LOAD_TIMEOUT)
            driver.get(url)

            # If an element_id was specified as a cmd line argument, wait for it to appear in the DOM before proceeding
            # else, just look for the <BODY> HTML tag
            try:
                if element_id is None or (not isinstance(element_id, str)) or element_id.strip() == "":
                    element_present = EC.presence_of_element_located((By.TAG_NAME, 'body'))
                else:
                    element_present = EC.presence_of_element_located((By.ID, element_id))

                # Source: https://stackoverflow.com/questions/26566799/wait-until-page-is-loaded-with-selenium-webdriver-for-python
                WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(element_present)
            except TimeoutException:
                print(f"Timed out waiting for page to load - {url}")
                return

            current_pg_cnt += 1
            page_source = driver.page_source
            page_title = get_title_from_page(page_source)
            if page_title is None:
                page_title = ''
            page_timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S.%f')[:-3] # millisecond precision
            page_filename = str(current_pg_cnt) + "-" + page_title.strip().replace(" ", "_") + '.' + page_timestamp + '.pdf'
            page_filepath = os.path.join(OUTPUT_DATA_DIR, page_filename)

            save_as_pdf(driver, page_filepath, { 'landscape': False, 'displayHeaderFooter': True })

            if current_depth < max_depth:
                links = collect_links_from_page(url, page_source, prefix)
                ## remove any links before continuing according to patterns seen for failed links
                # Use multithreading to crawl sublinks in parallel
                # filter urls so that it's not crawling a url that's already been crawled
                filtered_links = [url for url in links if url not in crawled]

                with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    future_to_url = {executor.submit(crawl, link, max_depth, current_depth + 1, current_pg_cnt, element_id, prefix): link for link in filtered_links}
                    for future in concurrent.futures.as_completed(future_to_url):
                        sublink = future_to_url[future]
                        # Do nothing, the crawling is already handled in the function.
            print(f'Crawling page {url} -- COMPLETED')
            driver.quit()
        except Exception as e:
            print(f'Error crawling {url} - {e}')
            return

    for link in good_links:
        crawl(link)

    # Print the total number of data sources crawled
    print(f"Total data sources: {len(crawled)}")

    response = {
        'response_text': 'Successfully crawled and saved %s data sources. Reinitializing vector database (this may take some time)...' % ( str(len(crawled)) )
    }
    return response


@app.route('/api/build-vector', methods=['POST','PUT'])
def crawl_build_vector():
    payload = request.json
    print(payload)
    vector_database.initialize_vector_db('./output')
    response = {
        'response_text': 'Vector Database initialized successfully.'
    }
    return response

@app.route('/api/call-rekognition-api', methods=['POST','PUT'])
def call_rekognition_api():
    # Get the image file from the request
    image_file = request.files['imageUpload']
    print("I am printing image file",image_file)
    # Read the image file as bytes
    image_bytes = image_file.read()
    # Create a client for Amazon Rekognition
    rekognition_client = session.client('rekognition',region_name=aws_region)
    # Call Amazon Rekognition API to detect labels
    response = rekognition_client.detect_labels(
        Image={'Bytes': image_bytes},
        MaxLabels=10
    )
    # Extract and return the labels from the response
    labels = [label['Name'] for label in response['Labels']]
    # Return the labels as the API response
    return {'labels': labels}   


@app.route('/api/upload-pdfs', methods=['POST','PUT'])
def upload_pdfs():
    if 'pdfFiles' not in request.files:
        return jsonify({'error': 'No PDF files uploaded'}), 400
    pdf_files = request.files.getlist('pdfFiles')
    if not pdf_files:
        return jsonify({'error': 'No selected files'}), 400
    saved_files = []
    
    # Get the directory path from app.config['UPLOAD_FOLDER']
    upload_folder = app.config['UPLOAD_FOLDER']
    
    # Create the directory if it doesn't exist
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    for pdf_file in pdf_files:
        if pdf_file.filename == '':
            continue
        pdf_path = os.path.join(upload_folder, pdf_file.filename)
        pdf_file.save(pdf_path)
        saved_files.append(pdf_file.filename)
    
    if saved_files:
        return jsonify({'response_text': f'{len(saved_files)} PDF files uploaded and saved. Reinitializing in-memory vector database (this may take some time)...', 'files': saved_files}), 200
    else:
        return jsonify({'error': 'No valid PDF files uploaded'}), 400
    

@app.route('/api/download-s3', methods=['POST','PUT'])
def download_s3():
    payload = request.json
    profile_name = payload['profile_name']
    location = payload['location']
    saved_files = vector_database.download_files_s3(profile_name, location)
    print(saved_files)
    return jsonify({'response_text': f'{saved_files} PDF files downloaded and saved. Reinitializing in-memory vector database (this may take some time)...'}), 200


@app.route('/api/instantiate-kendra', methods=['POST','PUT'])
def instantiate_kendra():
    payload = request.json
    profile_name = payload['profile_name']
    index_id = payload['index_id']
    response = vector_database.instantiate_kendra(profile_name, index_id)
    print('kendra connection was: '+str(response))
    return jsonify({'response_text': f'Amazon Kendra Index successfully connected.'}), 200

def contains_table(text):
    # Check if the text contains a table by looking for table delimiter lines
    return '|-' in text

def text_to_html_table(input_text):
    if contains_table(input_text):
        lines = input_text.strip().split('\n')
        initial_text = []
        table_lines = []
        trailing_text = []
        section = 'initial'
        
        for line in lines:
            if line.startswith('|'):
                section = 'table'
            elif line.strip() == '':
                section = 'trailing'
            
            if section == 'initial':
                initial_text.append(line)
            elif section == 'table':
                table_lines.append(line)
            elif section == 'trailing':
                trailing_text.append(line)
        
        initial_text = '\n'.join(initial_text)
        trailing_text = '\n'.join(trailing_text)
        
        html_table = '<table>\n'
        
        # Process header
        header = table_lines[0].split('|')
        html_table += '<tr>\n'
        for cell in header[1:-1]:  # Skipping the first and last empty cells
            cell_content = cell.strip()
            if cell_content != "-":
                html_table += f'<th>{cell_content}</th>\n'
        html_table += '</tr>\n'
        
        # Process data rows
        for line in table_lines[1:]:
            cells = line.split('|')
            html_table += '<tr>\n'
            for cell in cells[1:-1]:  # Skipping the first and last empty cells
                cell_content = cell.strip()
                if cell_content != "-":
                    html_table += f'<td>{cell_content}</td>\n'
            html_table += '</tr>\n'
        
        html_table += '</table>'
        
        return f"{initial_text}\n{html_table}\n{trailing_text}"
    else:
        return input_text
    
def create_bar_graph_html(input_text):
    # Find the starting index of the table
    start_index = input_text.find("|Issue|")

    # Extract the table part of the input text
    table_text = input_text[start_index:]

    # Split the table rows
    rows = table_text.strip().split('\n')

    # Parse the table rows to extract data
    headers = [header.strip() for header in rows[1].split('|') if header.strip()]
    data = []
    for row in rows[3:]:
        columns = [column.strip() for column in row.split('|') if column.strip()]
        data.append(columns)

    # Generate the bar graph HTML
    bar_graph_html = ''
    for item in data:
        issue = item[0]
        count = int(item[-1])
        bar_width = count * 20  # Adjust this factor to control bar width

        bar_graph_html += f'''
        <div class="bar-graph">
            <div class="bar-label">{count}</div>
            <div class="bar" style="width: {bar_width}px;"></div>
            <div class="issue-label">{issue}</div>
        </div>
        '''

    return bar_graph_html


@app.route('/api/deletefiles', methods=['GET'])
def delete_files_in_directory():
    try:
        # Get a list of all files in the directory
        directory_path = pdf_directory
        files = os.listdir(directory_path)

        # Loop through the files and delete each one
        for file_name in files:
            file_path = os.path.join(directory_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

        print("All files in the PDF output directory have been deleted.")
        vector_database.destroy_vector_db()
        return jsonify({'response_text': "All files in the PDF output directory have been deleted."}), 200
    except Exception as e:
        print(f"Error: {e}")

@app.route('/api/configure-opensearch', methods=['GET'])
def configure_opensearch():
    global opensearch_client
    try:
        # OpenSearch configuration
        auth = ('', '')
        opensearch_client = OpenSearch(
            hosts=[{'host': '', 'port': 443}],
            http_auth=auth,
            timeout=300,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

        opensearch_info = {
            "status": "success",
            "message": "OpenSearch configured successfully",
            "opensearch_config": {
                "hosts": opensearch_client.transport.hosts,
                "http_auth": auth
            }
        }
        return jsonify(opensearch_info), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/insert-documents', methods=['POST'])
def insert_documents():
    global opensearch_client
    try:
    
        # Get user input from the request body
        user_input = request.json  # Assuming JSON input
        print("userinput", user_input)
        response = requests.get(user_input["data_url"]).json()
        print("response", response)
        os_documents = []

        for r in response["rows"]:
            os_documents.append({"index": {"_index": "vectorindex"}})
            os_documents.append(r["row"])

        bulk_response = opensearch_client.bulk(body=os_documents)
        print("bulkresponse", bulk_response)
        print(bulk_response)
        
        return jsonify({"status": "success", "message": "Documents inserted successfully", "response": bulk_response}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/api/opensearch-search-documents', methods=['POST'])
def search_documents():
    global opensearch_client
    try:
        user_input = request.json  # Assuming JSON input

        vector_range = user_input["vector_range"]  # Extract vector range from user input

        search_query = {
            "size": user_input.get("limit", 2),
            "_source": ["title", "id", "url"],
            "query": {
                "range": {
                    "emb": {
                        "gte": vector_range[0],  # Minimum value in the vector range
                        "lte": vector_range[1]  # Maximum value in the vector range
                    }
                }
            }
        }

        search_response = opensearch_client.search(index='vectorindex', body=search_query)
        
        return jsonify({"status": "success", "message": "Search results", "response": search_response}), 200
        # Process and return search_response as needed
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
   
@app.route('/api/check-vector', methods=['GET'])
def check_vector():
    return jsonify({'vector_initialized': str(vector_database.vector_initialized)}), 200

@app.route('/api/update-prompt-template', methods=['POST','PUT'])
def update_prompt_template():
    user_input = request.json  # Assuming JSON input

    prompt_template = user_input["prompt_template"]  # Extract vector range from user input
    vector_database.update_prompt_template(prompt_template)
    return jsonify({'response_text': 'Prompt Template was updated.'}), 200

if __name__ == '__main__':
    app.run()


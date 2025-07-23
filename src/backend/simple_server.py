#!/usr/bin/env python3
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import os
import json
import traceback
import sys
import re

print("Python version:", sys.version)
print("Python path:", sys.executable)

# Try to import PyPDF2 for PDF text extraction
try:
    import PyPDF2
    print("PyPDF2 imported successfully")
except ImportError:
    print("PyPDF2 not available. Please install it with: pip install PyPDF2")
    sys.exit(1)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Directory to store uploaded PDFs
UPLOAD_FOLDER = './output'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Storage for PDF contents
pdf_contents = {}  # filename -> text content
vector_initialized = False

# Add a route to handle OPTIONS requests (preflight)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using PyPDF2"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page_text = reader.pages[page_num].extract_text()
                if page_text:  # Only add if text was extracted
                    text += page_text + "\n\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        traceback.print_exc()
        return ""

def process_pdfs():
    """Process all PDFs in the output directory"""
    global pdf_contents, vector_initialized
    
    # Clear existing content
    pdf_contents = {}
    
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith('.pdf')]
    print(f"Found {len(pdf_files)} PDF files in {UPLOAD_FOLDER}")
    
    # Process each PDF
    for pdf_file in pdf_files:
        file_path = os.path.join(UPLOAD_FOLDER, pdf_file)
        print(f"Processing {file_path}...")
        
        # Extract text
        text = extract_text_from_pdf(file_path)
        
        if text:
            print(f"Extracted {len(text)} characters from {pdf_file}")
            pdf_contents[pdf_file] = text
        else:
            print(f"No text extracted from {pdf_file}")
    
    # Set vector_initialized if we have content
    if pdf_contents:
        vector_initialized = True
        print(f"Successfully processed {len(pdf_contents)} PDF files")
        return True
    else:
        vector_initialized = False
        print("No text could be extracted from any PDF files")
        return False

def find_relevant_content(question):
    """Find content relevant to the question"""
    print(f"Finding relevant content for question: '{question}'")
    
    if not pdf_contents:
        print("No PDF contents available")
        return []
    
    # Convert question to lowercase for case-insensitive matching
    question_lower = question.lower()
    question_words = question_lower.split()
    
    # Filter out common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'like', 'from', 'of', 'as', 'this', 
                 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their', 'what', 'which', 'who', 
                 'whom', 'whose', 'when', 'where', 'why', 'how'}
    
    important_words = [w for w in question_words if len(w) > 3 and w not in stop_words]
    print(f"Important words from question: {important_words}")
    
    # Special handling for specific topics
    special_topics = {
        'mcc': ['manufacturing customer community', 'mcc'],
        'matenet': ['matenet', 'mate-net', 'mate net'],
        'hsd': ['hsd', 'high speed data'],
        'hsl': ['hsl', 'high speed link'],
        'panoptic': ['panoptic']
    }
    
    # Check if question is about a special topic
    for topic, keywords in special_topics.items():
        if any(keyword in question_lower for keyword in keywords):
            # Look for content related to this topic
            topic_results = []
            for filename, content in pdf_contents.items():
                content_lower = content.lower()
                if any(keyword in content_lower for keyword in keywords):
                    # Split into paragraphs and find relevant ones
                    paragraphs = content.split('\n\n')
                    for para in paragraphs:
                        para_lower = para.lower()
                        if any(keyword in para_lower for keyword in keywords):
                            topic_results.append({
                                'filename': filename,
                                'paragraph': para,
                                'score': 10  # High score for direct topic matches
                            })
            
            if topic_results:
                print(f"Found {len(topic_results)} paragraphs specifically about {topic}")
                return topic_results[:5]  # Return top 5 topic-specific results
    
    # General search for other questions
    results = []
    for filename, content in pdf_contents.items():
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            para_lower = para.lower()
            score = 0
            matched_words = []
            
            # Score paragraph based on question words it contains
            for word in important_words:
                if word in para_lower:
                    score += 1
                    matched_words.append(word)
            
            # If paragraph contains at least one important word, add it to results
            if score > 0:
                print(f"Found match with score {score}, matched words: {matched_words}")
                results.append({
                    'filename': filename,
                    'paragraph': para,
                    'score': score
                })
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"Found {len(results)} relevant paragraphs")
    return results[:5]  # Return top 5 results

def create_prompt_for_claude(question, relevant_content):
    """Create a prompt for Claude based on the question and relevant content"""
    
    # Start with a system prompt that instructs Claude on how to respond
    prompt = """You are an assistant that answers questions based on provided documents.

DOCUMENTS:
"""
    
    # Add the relevant content from documents
    for i, item in enumerate(relevant_content, 1):
        prompt += f"Document {i} (from {item['filename']}):\n{item['paragraph']}\n\n"
    
    # Add the user's question
    prompt += f"""
USER QUESTION:
{question}

RESPONSE INSTRUCTIONS:

1. QUESTION ANALYSIS:
   - Identify the question type (definition, list, summary, comparison, translation, etc.)
   - Determine key entities and concepts mentioned
   - Assess the scope and depth required

2. DOCUMENT ANALYSIS:
   - Cross-reference information across all provided documents
   - Identify and resolve any contradictions or inconsistencies
   - Note the most relevant and authoritative sources
   - Extract specific data points requested in the question (names, dates, numbers, etc.)

3. RESPONSE FORMATTING:

For definitions ("what is"):
   - Start with a clear, concise definition (1-2 sentences)
   - Follow with key details and context
   - Highlight important points

For lists ("list", "who are", "what are", "name all", etc.):
   - ALWAYS use bullet points (•) for each item
   - Format as a clean, structured list with one item per line
   - Include names, titles, and other relevant details for each item
   - Group items by category if there are more than 5 items
   - For people lists, include their roles/titles if available
   - For "sponsors" or similar roles, clearly identify all individuals mentioned

For summaries:
   - Provide a concise overview (2-3 sentences)
   - Include key points and significant details
   - Maintain logical flow and coherence

For comparisons:
   - Use clear structure (tables/columns if appropriate)
   - Highlight key differences and similarities
   - Present balanced information from all sources

For processes ("how to"):
   - Present step-by-step instructions with numbered steps
   - Include any important prerequisites
   - Note any warnings or special considerations

4. QUALITY GUIDELINES:
   - Be extremely concise and direct
   - Use clear, professional language
   - Highlight key information where relevant
   - Include specific details from documents when necessary
   - State clearly if information is insufficient
   - NEVER include phrases like "Based on the documents" or "According to the information provided"
   - Adapt tone and complexity to match the question
   - Present information in a logical, organized manner
   - NEVER return raw document text - always process and format the information
   - For list questions, ensure ALL relevant items are extracted from the documents

5. SPECIAL INSTRUCTIONS FOR LIST QUESTIONS:
   - If the question asks to "list" anything, your response MUST be in bullet point format
   - Extract ALL relevant items from the documents, even if they appear in different sections
   - Format each item consistently
   - Include only the information requested - be precise and focused
   - For questions about people (sponsors, team members, etc.), list each person with their role/email if available

Now, please provide your response to the question above, following these guidelines and formatting instructions.
"""
    
    return prompt

@app.route('/api/check-vector', methods=['GET', 'OPTIONS'])
def check_vector():
    """Check if PDFs have been processed"""
    if request.method == 'OPTIONS':
        return make_response('', 200)
        
    global vector_initialized
    
    # Count PDF files in the output directory
    pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith('.pdf')]
    doc_count = len(pdf_files)
    
    # If we have PDFs but haven't processed them, do it now
    if doc_count > 0 and not vector_initialized:
        process_pdfs()
    
    response = {
        'vector_initialized': str(vector_initialized).lower(),
        'has_documents': str(doc_count > 0).lower(),
        'document_count': doc_count
    }
    return jsonify(response)

@app.route('/api/upload-pdf', methods=['POST', 'OPTIONS'])
def upload_pdf():
    """Handle PDF file uploads"""
    if request.method == 'OPTIONS':
        return make_response('', 200)
        
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': 'No files part in the request'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'success': False, 'message': 'No files selected'}), 400
    
    # Save each uploaded file
    saved_files = []
    for file in files:
        if file and file.filename.lower().endswith('.pdf'):
            filename = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filename)
            saved_files.append(file.filename)
    
    # Process the PDFs
    if saved_files:
        process_pdfs()
    
    return jsonify({
        'success': True, 
        'message': f'Successfully saved {len(saved_files)} PDF files',
        'files': saved_files
    })

@app.route('/api/build-vector', methods=['POST', 'PUT', 'OPTIONS'])
def build_vector():
    """Process all PDFs"""
    if request.method == 'OPTIONS':
        return make_response('', 200)
        
    success = process_pdfs()
    
    if success:
        return jsonify({
            'response_text': f'Successfully processed {len(pdf_contents)} PDF files.'
        })
    else:
        return jsonify({
            'response_text': 'Failed to process PDF files. Please check the logs.'
        })

@app.route('/api/force-initialize-vector', methods=['GET', 'POST', 'OPTIONS'])
def force_initialize_vector():
    """Force reprocessing of all PDFs"""
    if request.method == 'OPTIONS':
        return make_response('', 200)
        
    success = process_pdfs()
    
    if success:
        return jsonify({
            'success': True,
            'message': f'Successfully processed {len(pdf_contents)} PDF files.'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to process PDF files. Please check the logs.'
        })

@app.route('/api/deletefiles', methods=['GET', 'OPTIONS'])
def delete_files():
    """Delete all files in the output directory"""
    if request.method == 'OPTIONS':
        return make_response('', 200)
        
    global vector_initialized, pdf_contents
    
    # Delete all files in the output directory
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    
    # Reset state
    vector_initialized = False
    pdf_contents = {}
    
    return jsonify({
        'response_text': 'All files deleted and PDF processing reset.'
    })

@app.route('/api/conversation/predict-claude', methods=['POST', 'PUT', 'OPTIONS'])
def predict_conversation():
    """Handle question-answering based on uploaded documents"""
    if request.method == 'OPTIONS':
        return make_response('', 200)
        
    # Parse the request
    try:
        payload = request.get_json()
        print(f"Received payload: {payload}")
        
        if not payload or 'body' not in payload:
            return jsonify("Invalid request format"), 400
        
        body = json.loads(payload['body'])
        question = body.get('prompt', '')
        
        if not question:
            return jsonify("No question provided"), 400
        
        print(f"Received question: {question}")
        
        # Make sure PDFs are processed
        if not vector_initialized:
            process_pdfs()
        
        # If we still don't have any content, return an error
        if not pdf_contents:
            return jsonify("No PDF content available. Please upload PDF documents."), 400
        
        # Find relevant content
        relevant_content = find_relevant_content(question)
        
        if not relevant_content:
            return jsonify("I couldn't find any relevant information about that in the documents. Could you try asking a different question or uploading more relevant documents?")
        
        # Create a prompt for Claude
        prompt = create_prompt_for_claude(question, relevant_content)
        print(f"Created prompt for Claude of length {len(prompt)}")
        
        try:
            # Try to import the Anthropic client
            import anthropic
            
            # Check if ANTHROPIC_API_KEY is set in environment
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                print("Warning: ANTHROPIC_API_KEY environment variable not set. Using fallback response.")
                # Fallback to simple response if API key is not available
                response = f"Here's what I found about your question: '{question}'\n\n"
                for item in relevant_content:
                    response += f"From {item['filename']}:\n{item['paragraph']}\n\n"
            else:
                # Initialize the Anthropic client
                client = anthropic.Anthropic(api_key=api_key)
                
                # Send the prompt to Claude
                claude_response = client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    temperature=0.5,
                    system="You are a helpful assistant that answers questions based on provided documents.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract the response text
                response = claude_response.content[0].text
                print(f"Received response from Claude of length {len(response)}")
        except ImportError:
            print("Anthropic package not installed. Using fallback response.")
            # Fallback to simple response if Anthropic package is not installed
            response = f"Here's what I found about your question: '{question}'\n\n"
            for item in relevant_content:
                response += f"From {item['filename']}:\n{item['paragraph']}\n\n"
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            # Fallback to simple response if there's an error calling the API
            response = f"Here's what I found about your question: '{question}'\n\n"
            for item in relevant_content:
                response += f"From {item['filename']}:\n{item['paragraph']}\n\n"
        
        print(f"Returning answer of length {len(response)}")
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in predict_conversation: {e}")
        traceback.print_exc()
        return jsonify(f"Error processing your question: {str(e)}"), 500

@app.route('/api/conversation/predict-claude-kendra', methods=['POST', 'PUT', 'OPTIONS'])
def predict_conversation_kendra():
    """Alias for the predict-claude endpoint"""
    return predict_conversation()

@app.route('/api/conversation/claude-middleware', methods=['POST', 'PUT', 'OPTIONS'])
def claude_middleware():
    """Alias for the predict-claude endpoint"""
    return predict_conversation()

if __name__ == '__main__':
    print("Starting Flask server on port 8000...")
    print("API will be available at http://localhost:8000")
    
    # Process any existing PDFs on startup
    process_pdfs()
    
    print("Press Ctrl+C to stop the server")
    app.run(host='0.0.0.0', port=8000, debug=True)
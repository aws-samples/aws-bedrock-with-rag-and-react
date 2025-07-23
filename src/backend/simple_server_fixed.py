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

# Helper functions for question analysis
def is_who_question(question):
    """Check if the question is asking about people"""
    question_lower = question.lower()
    return question_lower.startswith("who") or "who are" in question_lower or "who is" in question_lower

def is_comparison_question(question):
    """Check if the question is asking for a comparison"""
    question_lower = question.lower()
    comparison_patterns = [
        r'(what|which) is (better|worse|faster|slower|more|less)',
        r'(what|which) (should|would|could) i (use|choose|select|pick)',
        r'(compare|comparison|versus|vs\.?|or)',
        r'difference between',
        r'when (to|should) (use|choose|select|pick)',
        r'where (to|should) (use|choose|select|pick)'
    ]
    
    for pattern in comparison_patterns:
        if re.search(pattern, question_lower):
            return True
    
    return False

def extract_topics_for_comparison(question):
    """Extract topics being compared in the question"""
    question_lower = question.lower()
    # Look for "X vs Y" pattern
    vs_match = re.search(r'([a-zA-Z0-9_\-]+)\s+(?:vs\.?|versus)\s+([a-zA-Z0-9_\-]+)', question_lower)
    if vs_match:
        return [vs_match.group(1), vs_match.group(2)]
    
    # Look for "X or Y" pattern
    or_match = re.search(r'([a-zA-Z0-9_\-]+)\s+or\s+([a-zA-Z0-9_\-]+)', question_lower)
    if or_match:
        return [or_match.group(1), or_match.group(2)]
    
    # Look for "between X and Y" pattern
    between_match = re.search(r'between\s+([a-zA-Z0-9_\-]+)\s+and\s+([a-zA-Z0-9_\-]+)', question_lower)
    if between_match:
        return [between_match.group(1), between_match.group(2)]
    
    return None

def analyze_question(question):
    """Analyze the question to determine its type and topic"""
    question_lower = question.lower()
    analysis = {
        'type': 'general',
        'main_topic': None
    }
    
    # Identify question type
    if question_lower.startswith('what is ') or question_lower.startswith('what are '):
        analysis['type'] = 'definition'
    elif is_who_question(question_lower):
        analysis['type'] = 'person'
    elif question_lower.startswith('list ') or 'list down' in question_lower:
        analysis['type'] = 'list'
    elif 'protocol' in question_lower:
        analysis['type'] = 'protocol'
    elif is_comparison_question(question_lower):
        analysis['type'] = 'comparison'
    
    # Extract main topic
    if question_lower.startswith('what is '):
        analysis['main_topic'] = question_lower.replace('what is ', '').strip()
    elif question_lower.startswith('what are '):
        analysis['main_topic'] = question_lower.replace('what are ', '').strip()
    elif question_lower.startswith('who '):
        analysis['main_topic'] = question_lower.replace('who ', '').strip()
        if analysis['main_topic'].startswith('are '):
            analysis['main_topic'] = analysis['main_topic'].replace('are ', '')
    elif question_lower.startswith('list '):
        analysis['main_topic'] = question_lower.replace('list ', '').strip()
    elif question_lower.startswith('where '):
        analysis['main_topic'] = question_lower.replace('where ', '').strip()
    else:
        # Try to extract a topic from the question
        words = question_lower.split()
        if len(words) > 2:
            analysis['main_topic'] = ' '.join(words[1:])
    
    return analysis

def find_relevant_content(question):
    """Find content relevant to the question"""
    print(f"Finding relevant content for question: '{question}'")
    
    if not pdf_contents:
        print("No PDF contents available")
        return []
    
    # Analyze the question
    analysis = analyze_question(question)
    main_topic = analysis['main_topic']
    question_type = analysis['type']
    
    print(f"Question analysis: type={question_type}, main_topic={main_topic}")
    
    # Special handling for MCC questions
    if main_topic and "mcc" in main_topic.lower():
        mcc_results = []
        for filename, content in pdf_contents.items():
            if "manufacturing customer community" in content.lower() or " mcc " in content.lower():
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    if "manufacturing customer community" in para.lower() or " mcc " in para.lower():
                        mcc_results.append({
                            'filename': filename,
                            'paragraph': para,
                            'score': 10
                        })
        
        if mcc_results:
            print(f"Found {len(mcc_results)} paragraphs specifically about MCC")
            return mcc_results[:3]
    
    # Special handling for protocol questions
    if "matenet" in question.lower() or "hsd" in question.lower() or "hsl" in question.lower():
        protocol_results = []
        for filename, content in pdf_contents.items():
            if "matenet" in content.lower() or "hsd" in content.lower() or "hsl" in content.lower():
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    if "matenet" in para.lower() or "hsd" in para.lower() or "hsl" in para.lower():
                        protocol_results.append({
                            'filename': filename,
                            'paragraph': para,
                            'score': 10
                        })
        
        if protocol_results:
            print(f"Found {len(protocol_results)} paragraphs about protocols")
            return protocol_results[:5]
    
    # General search for other questions
    results = []
    question_words = question.lower().split()
    
    # Filter out common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were'}
    important_words = [w for w in question_words if len(w) > 3 and w not in stop_words]
    
    for filename, content in pdf_contents.items():
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            score = 0
            for word in important_words:
                if word in para.lower():
                    score += 1
            
            if score > 0:
                results.append({
                    'filename': filename,
                    'paragraph': para,
                    'score': score
                })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results[:3]  # Return top 3 results

def extract_names(text):
    """Extract names from text"""
    # Look for patterns like "Name (email@domain.com)" or similar
    email_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+) \(([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\)'
    email_matches = re.findall(email_pattern, text)
    
    # Look for patterns like "Name Surname (username@)" 
    username_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+) \(([a-zA-Z0-9_-]+@)\)'
    username_matches = re.findall(username_pattern, text)
    
    # Combine results
    names = []
    for name, email in email_matches:
        names.append({"name": name, "contact": email})
    
    for name, username in username_matches:
        names.append({"name": name, "contact": username})
    
    return names

def extract_protocols(text, topic):
    """Extract protocols from text"""
    protocols = []
    
    # Define protocol-related keywords
    protocol_keywords = ['protocol', 'standard', 'interface', 'ethernet', 'usb', 'hdmi']
    
    # Split text into lines
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        # Check for protocol-related content
        if any(keyword in line.lower() for keyword in protocol_keywords):
            protocols.append(line)
        # Check for lines containing the topic
        elif topic and topic.lower() in line.lower():
            protocols.append(line)
    
    return protocols

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

3. RESPONSE FORMATTING:
For definitions ("what is"):
   - Start with a clear, concise definition
   - Follow with key details and context
   - Highlight important points

For lists ("who", "what are"):
   - Use bullet points or numbered lists
   - Organize by category if applicable
   - Include relevant details for each item

For summaries:
   - Provide a concise overview
   - Include key points and significant details
   - Maintain logical flow and coherence

For comparisons:
   - Use clear structure (tables/columns if appropriate)
   - Highlight key differences and similarities
   - Present balanced information from all sources

For processes ("how to"):
   - Present step-by-step instructions
   - Include any important prerequisites
   - Note any warnings or special considerations

For translations:
   - Maintain original meaning and context
   - Preserve technical terminology
   - Include original text if helpful

4. QUALITY GUIDELINES:
   - Be concise and direct
   - Use clear, professional language
   - Highlight key information where relevant
   - Include specific details from documents when necessary
   - State clearly if information is insufficient
   - Avoid meta-references to the documents
   - Adapt tone and complexity to match the question
   - Present information in a logical, organized manner

Now, please provide your response to the question above, following these guidelines and formatting instructions.
"""
    
    return prompt

def generate_response(question, relevant_content):
    """Generate a response based on the question and relevant content"""
    if not relevant_content:
        return "I don't have information about that in the documents."
    
    analysis = analyze_question(question)
    question_type = analysis['type']
    main_topic = analysis['main_topic']
    
    # Handle different question types
    if question_type == 'person':
        # Extract names from content
        all_names = []
        for item in relevant_content:
            names = extract_names(item['paragraph'])
            for name in names:
                if name not in all_names:
                    all_names.append(name)
        
        if all_names:
            response = f"Based on the documents, here are the people associated with {main_topic}:\n\n"
            for name_info in all_names:
                response += f"• {name_info['name']} ({name_info['contact']})\n"
            return response
    
    elif question_type == 'protocol':
        # Extract protocols from content
        all_protocols = []
        for item in relevant_content:
            protocols = extract_protocols(item['paragraph'], main_topic)
            for protocol in protocols:
                if protocol not in all_protocols:
                    all_protocols.append(protocol)
        
        if all_protocols:
            response = f"Based on the documents, here are the protocols for {main_topic}:\n\n"
            for i, protocol in enumerate(all_protocols[:10], 1):
                response += f"{i}. {protocol}\n"
            return response
    
    elif question_type == 'comparison':
        topics = extract_topics_for_comparison(question)
        if topics:
            response = f"Based on the documents, here's a comparison between {topics[0]} and {topics[1]}:\n\n"
            
            # Extract information about each topic
            for topic in topics:
                response += f"{topic.upper()}:\n"
                for item in relevant_content:
                    if topic.lower() in item['paragraph'].lower():
                        sentences = item['paragraph'].split('. ')
                        for sentence in sentences:
                            if topic.lower() in sentence.lower():
                                response += f"• {sentence.strip()}.\n"
                response += "\n"
            
            return response
    
    # Default response for other question types
    response = f"Based on the documents, here's what I found about {main_topic}:\n\n"
    
    for item in relevant_content:
        response += f"From {item['filename']}:\n{item['paragraph']}\n\n"
    
    return response

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
        
        # Generate a response
        answer = generate_response(question, relevant_content)
        
        print(f"Returning answer of length {len(answer)}")
        return jsonify(answer)
        
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
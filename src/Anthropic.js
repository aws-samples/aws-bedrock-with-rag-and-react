// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT.

import React, { useState, useEffect } from 'react';
import { Button, TextField } from '@aws-amplify/ui-react';
import proxy_url from './proxy'

const api_root_url = proxy_url

const Anthropic = (props) => {
    const [chatMessages, setChatMessages] = useState([]);
    const [userInput, setUserInput] = useState('');
    const [userInputCrawl, setUserInputCrawl] = useState('');
    const [isBuffering, setIsBuffering] = useState(false)
    const [isBufferingCrawl, setIsBufferingCrawl] = useState(false)
    const [isBufferingReindex, setIsBufferingReindex] = useState(false)
    const [apiMethod, setApiMethod] = useState('/api/conversation/claude-middleware')
    const [crawlMethod, setCrawlMethod] = useState('/api/crawl')
    const [reindexMethod, setReindexMethod] = useState('/api/build-vector')
    const [selectedModel, setSelectedModel] = useState('')
    const [crawlModal, setCrawlModal] = useState(false)
    const [crawlPrompt, setCrawlPrompt] = useState('');
    const [crawlResponse, setCrawlResponse] = useState('');
    const [crawlResponseRaw, setCrawlResponseRaw] = useState('');
    const [reindexResponse, setReindexResponse] = useState('');
    const [uploadSuccessMessage, setUploadSuccessMessage] = useState('');
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [vectorSelection, setVectorSelection] = useState(null)
    const [userInputProfile, setUserInputProfile] = useState('')
    const [userInputS3Path, setUserInputS3Path] = useState('')
    const [userInputKendraId, setUserInputKendraId] = useState('')
    const [currentVector, setCurrentVector] = useState('faiss')
    const [kendraInstantiated, setKendraInstantiated] = useState(false)
    const [opensearchInstantiated, setOpensearchInstantiated] = useState(false)
    const [vectorInitialized, setVectorInitialized] = useState('false')
    const [dataDeleted, setDataDeleted] = useState('')
    const [promptModal, setPromptModal] = useState(false)
    const [promptTemplate, setPromptTemplate] = useState("Use the context to answer the question at the end. If you don't know the answer from the context, do not answer from your knowledge and be precise. Don't fake the answer.")
    const [promptTemplateResponse, setPromptTemplateResponse] = useState('')

    useEffect(() => {
        // Code to run after component has mounted
        if (props.anthropicMessages.length === 0) {
            setChatMessages([
                { author: `${props.modelSelected.split(':')[1]} Bot`, message: `Welcome to the ${props.modelSelected} Chatbot!` }
            ])
        } else {
            setChatMessages(props.anthropicMessages)
        }

        setSelectedModel(props.modelSelected)

        checkVector();

        // Set up an interval to call the API every minute
        const interval = setInterval(checkVector, 10000); // 60000 milliseconds = 1 minute
        console.log(props.currentVector)

        // setCurrentVector(props.currentVector)
        setKendraInstantiated(props.kendraInstantiated)
        setPromptTemplate(props.promptTemplate)
        setCurrentVector(props.currentVector)

        // Clean up the interval when the component unmounts
        return () => clearInterval(interval);


    }, [props.modelSelected,
    props.anthropicMessages,
    props.setAnthropicMessages,
    props.currentVector,
    props.setCurrentVector,
    props.kendraInstantiated,
    props.setKendraInstantiated,
    props.promptTemplate,
    props.setPromptTemplate
    ]);

    const checkVector = () => {
        
        fetch(api_root_url + '/api/check-vector', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(response => response.json())
        .then(response => {
            console.log(response.vector_initialized.toLowerCase())
            setVectorInitialized(response.vector_initialized.toLowerCase())
        })
        .catch(error => {
            console.error('Error:', error);
        });
    };

    const deleteFiles = async () => {
        try {
            const response = await fetch(api_root_url + '/api/deletefiles');
            const jsonData = await response.json();
            //   console.log(jsonData.vector_initialized.toLowerCase())
            console.log(jsonData.response_text)
            setDataDeleted(jsonData.response_text)
            checkVector()
            setTimeout(function () {
                setDataDeleted('')
            }, 5000)
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };

    const sendMessage = () => {
        setIsBuffering(true);
        const messageElement = {
            author: 'You',
            message: userInput
        };

        setChatMessages(prevChatMessages => [...prevChatMessages, messageElement]);
        props.setAnthropicMessages(prevChatMessages => [...prevChatMessages, messageElement]);

        let payload = {
            modelId: 'anthropic.claude-instant-v1',
            contentType: 'application/json',
            accept: '*/*',
            body: JSON.stringify({
                prompt: userInput,
                max_tokens_to_sample: 300,
                temperature: 0.5,
                top_k: 250,
                top_p: 1,
                stop_sequences: ['\n\nHuman:'],
                vector: currentVector
            })
        };

        setUserInput('');
        fetch(api_root_url + apiMethod, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(response => {
                const botResponse = formatBotResponse(response);
                const botMessageElement = {
                    author: `${selectedModel.split(':')[1]} Bot`,
                    message: botResponse
                };
                setChatMessages(prevChatMessages => [...prevChatMessages, botMessageElement]);
                props.setAnthropicMessages(prevChatMessages => [...prevChatMessages, botMessageElement])
            })
            .catch(error => {
                console.error('Error:', error);
            }).finally(() => {
                setIsBuffering(false)
            });
    };

    const formatBotResponse = (response) => {
        const regexNumberedList = /^\d+\.\s/;
        const regexBulletedList = /^[\-\*\+\•]/;
        const regexURL = /\b(?:https?:\/\/|www\.)\S+\b/gi; // Improved URL regex
        const lines = response.trim().split('\n');

        let listType = '';
        let result = '';

        lines.forEach(line => {
            if (regexNumberedList.test(line)) {
                if (!listType) {
                    listType = 'ol';
                    result += `<ol>`;
                }
                line = `<li>${line.replace(regexNumberedList, '')}</li>`;
            } else if (regexBulletedList.test(line)) {
                if (!listType) {
                    listType = 'ul';
                    result += `<ul>`;
                }
                line = `<li>${line.replace(regexBulletedList, '')}</li>`;
            } else {
                if (listType) {
                    result += `</${listType}>`;
                    listType = '';
                }
            }

            line = line.replace(regexURL, '<a href="$&" target="_blank">$&</a>');
            result += `${line}\n`;
        });

        if (listType) {
            result += `</${listType}>`;
        }

        return result;
    };

    const clearChatHistory = () => {
        setChatMessages([
            { author: `${selectedModel.split(':')[1]} Bot`, message: `Welcome to the ${selectedModel} Chatbot!` }
        ])
        props.setAnthropicMessages([
            { author: `${selectedModel.split(':')[1]} Bot`, message: `Welcome to the ${selectedModel} Chatbot!` }
        ])
    }

    const clearChatHistoryCrawl = () => {
        setCrawlPrompt('')
        setCrawlResponse('')
    }

    const crawlReindex = async () => {
        try {
            setIsBufferingReindex(true);
            setCrawlPrompt('');
            setCrawlResponse('');
            setReindexResponse('Crawling data sources and Reindexing the Vector Database... This may take a moment...');

            let payload = {
                prompt: JSON.stringify({
                    prompt: userInputCrawl
                })
            };

            // Perform first API call
            const response1 = await fetch(api_root_url + crawlMethod, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const json1 = await response1.json();
            console.log(json1);
            setReindexResponse(json1.response_text);

            // Perform second API call
            const response2 = await fetch(api_root_url + reindexMethod, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const json2 = await response2.json();
            console.log(json2);
            setReindexResponse(json2.response_text);
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setIsBufferingReindex(false);
            checkVector()
            console.log(reindexResponse);
        }
    }

    const SelectedFilesMessage = ({ selectedFiles }) => (
        <p className="SelectedFilesMessage">{selectedFiles.length} files selected</p>
    );

    const NoFileMessage = ({ selectedFiles }) => (
        <p className="NoFileMessage">{selectedFiles.length === 0 ? 'No file chosen' : ''}</p>
    );

    const handleFileUpload = (event) => {
        const files = event.target.files;

        let payload = {
            prompt: JSON.stringify({
                prompt: 'ignore, dummy data'
            })
        }

        if (files.length > 0) {
            setIsBufferingReindex(true);
            setSelectedFiles(Array.from(files)); // Update selectedFiles state

            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('pdfFiles', files[i]);
            }

            fetch(api_root_url + '/api/upload-pdfs', {
                method: 'POST',
                body: formData,
            })
                .then(response => response.json())
                .then(response => {
                    // Handle the response, e.g., display a success message
                    console.log(response);
                    if (response.response_text) {
                        setReindexResponse(response.response_text);

                        // Clear the success message after 3 seconds
                        setTimeout(() => {
                            setUploadSuccessMessage('');
                        }, 3000);
                        setSelectedFiles([]);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                })
                .finally(() => {
                    fetch(api_root_url + reindexMethod, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    })
                        .then(response => response.json())
                        .then(response => {
                            console.log(response)
                            setReindexResponse(response.response_text)
                        })
                        .catch(error => {
                            console.error('Error:', error);
                        }).finally(() => {
                            setIsBufferingReindex(false)
                            checkVector()
                            console.log(reindexResponse)
                        });
                });
        }
    };

    const downloadS3 = (event) => {
        let payload = {
            profile_name: userInputProfile,
            location: userInputS3Path
        }

        setIsBufferingReindex(true);
        setReindexResponse('Downloading files from the S3 location. Depending on how many files are present, it may take a while...')

        fetch(api_root_url + '/api/download-s3', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(response => {
                // Handle the response, e.g., display a success message
                console.log(response);
                if (response.response_text) {
                    setReindexResponse(response.response_text);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            })
            .finally(() => {
                fetch(api_root_url + reindexMethod, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                })
                    .then(response => response.json())
                    .then(response => {
                        console.log(response)
                        setReindexResponse(response.response_text)
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    }).finally(() => {
                        setIsBufferingReindex(false)
                        checkVector()
                        console.log(reindexResponse)
                    });
            });
    }

    const handleVectorModalBack = (event) => {
        setVectorSelection(null)
        setReindexResponse('')
    }

    const waitTransition = (value) => {
        setTimeout(function() {
            return value
        }, 400)
    }

    const instantiateKendra = (event) => {
        console.log('connecting to kendra')
        setIsBufferingReindex(true)
        setCrawlPrompt('')
        setCrawlResponse('')
        setReindexResponse('Connecting to Kendra Index...')

        let payload = {
            profile_name: userInputProfile,
            index_id: userInputKendraId
        }

        fetch(api_root_url + '/api/instantiate-kendra', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(response => {
                console.log(response)
                setReindexResponse(response.response_text)
            })
            .catch(error => {
                console.error('Error:', error);
            }).finally(() => {
                console.log(reindexResponse)
                setIsBufferingReindex(false)
                checkVector()
                setKendraInstantiated(true)
                props.setKendraInstantiated(true)
            });
    }

    const updatePromptTemplate = () => {
        setIsBuffering(true);

        let payload = {
            prompt_template: promptTemplate
        };
        props.setPromptTemplate(promptTemplate)

        fetch(api_root_url + '/api/update-prompt-template', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(response => {
                setPromptTemplateResponse(response.response_text);
                
            })
            .catch(error => {
                console.error('Error:', error);
            }).finally(() => {
                setIsBuffering(false)
                
            });
    };

    const handleSetVector = (vector) => {
        console.log(vector)
        setCurrentVector(vector)
        syncVectorLocal(vector)
    }

    const syncVectorLocal = async (vector) => {
        props.setCurrentVector(vector)
    };

    return (
        <div className="chat-container">
            <div className="chat-messages" id="chatMessages">
                {chatMessages.map((message, index) => (
                    <p key={index} className={`${message.author}-message`}>
                        <span className="MessageText" dangerouslySetInnerHTML={{ __html: message.message }}></span>
                    </p>
                ))}
            </div>
            {isBuffering &&
                <div className="dots">
                    <div className="dot"></div>
                    <div className="dot"></div>
                    <div className="dot"></div>
                </div>
            }
            <div className="user-input">
                <Button type="Button" className="ClearHistory" onClick={clearChatHistory} disabled={chatMessages.length === 1 ? true : false}>Clear History</Button>
                <textarea
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="Type your message..."
                />
                <Button type="Button" className='PromptButton' onClick={sendMessage} disabled={isBuffering ? true : (currentVector === "faiss" ? (vectorInitialized === "false" ? true : false) : false)}>Send</Button>
            </div>
            <div className='PromptModal' style={{
                display: promptModal ? 'flex' : 'none'
            }} >
                <div className="CrawlPrompt">
                <div className="CrawlModalButtons" style={{ justifyContent: 'space-between' }}>
                        <p>Prompt Template Editing</p>
                        <div className="ModalButton" onClick={() => setPromptModal(!promptModal)}>
                            <svg className="closeModal" viewBox="0 0 24 24">
                                <path d="M14.578 8.016l1.406 1.406-2.578 2.578 2.578 2.578-1.406 1.406-2.578-2.578-2.578 2.578-1.406-1.406 2.578-2.578-2.578-2.578 1.406-1.406 2.578 2.578zM21 3q0.797 0 1.406 0.609t0.609 1.406v13.969q0 0.797-0.609 1.406t-1.406 0.609h-18q-0.797 0-1.406-0.609t-0.609-1.406v-13.969q0-0.797 0.609-1.406t1.406-0.609h18zM21 19.078v-14.063h-18v14.063h18z"></path>
                            </svg>
                        </div>
                </div>
                <span className="HundoContainer">
                    <div className="user-input">
                    <textarea
                        value={promptTemplate}
                        onChange={(e) => setPromptTemplate(e.target.value)}
                        placeholder="Provide specific instructions for how the model should respond."
                    />
                    <div className="CrawlModalButtons" style={{ justifyContent: 'space-between' }}>
                        <p>{promptTemplateResponse}</p>
                        <Button type="Button" className='PromptButton' onClick={updatePromptTemplate}>Update Prompt Template</Button>
                    </div>
                </div>
                </span>
                </div>
            </div>
            <div className='CrawlModal' style={{
                display: crawlModal ? 'flex' : 'none',
                opacity: crawlModal ?  1 : 0 
            }} >
                <div className="CrawlPrompt">
                    <div className="CrawlModalButtons" style={{ justifyContent: vectorSelection === null ? 'flex-end' : 'space-between' }}>
                        {vectorSelection !== null &&
                            <div className="ModalButtonBack" onClick={() => handleVectorModalBack()}>
                                <svg className="closeModal" viewBox="0 0 24 24">
                                    <path d="M21 11.016v1.969h-14.156l3.563 3.609-1.406 1.406-6-6 6-6 1.406 1.406-3.563 3.609h14.156z"></path>
                                </svg>
                            </div>
                        }
                        <div className="ModalButton" onClick={() => setCrawlModal(!crawlModal)}>
                            <svg className="closeModal" viewBox="0 0 24 24">
                                <path d="M14.578 8.016l1.406 1.406-2.578 2.578 2.578 2.578-1.406 1.406-2.578-2.578-2.578 2.578-1.406-1.406 2.578-2.578-2.578-2.578 1.406-1.406 2.578 2.578zM21 3q0.797 0 1.406 0.609t0.609 1.406v13.969q0 0.797-0.609 1.406t-1.406 0.609h-18q-0.797 0-1.406-0.609t-0.609-1.406v-13.969q0-0.797 0.609-1.406t1.406-0.609h18zM21 19.078v-14.063h-18v14.063h18z"></path>
                            </svg>
                        </div>
                    </div>
                    {vectorSelection === null &&
                        <span className="HundoContainer">
                            <p className="VectorSelection">Please select an option for vector database:</p>
                            <div className="VectorSelection">
                                <div className="VectorInnerSelection">
                                    <Button onClick={() => setVectorSelection('local')}>Local In-Memory Vector DB (FAISS)</Button>
                                    <Button className={currentVector === "faiss" ? "VectorUseButton Active" : "VectorUseButton"} onClick={() => handleSetVector('faiss')}>Use FAISS</Button>
                                </div>
                                <div className="VectorInnerSelection">
                                    <Button onClick={() => setVectorSelection('kendra')}>Amazon Kendra Index</Button>
                                    <Button className={currentVector === "kendra" ? "VectorUseButton Active" : "VectorUseButton"} disabled={!kendraInstantiated} onClick={() => handleSetVector('kendra')}>Use Kendra</Button>
                                </div>
                            </div>
                        </span>
                    }
                    {vectorSelection === 'local' &&
                        <span className="HundoContainer">
                            <p className="VectorSelection">Do you want to upload PDF files manually or crawl a seed url?</p>
                            <div className="VectorSelection">
                                <Button onClick={() => setVectorSelection('local_load')}>Upload PDFs Manually</Button>
                                <Button onClick={() => setVectorSelection('local_s3')}>Download from S3</Button>
                                <Button onClick={() => setVectorSelection('local_crawl')}>Crawl Seed URL</Button>
                                <Button disabled={vectorInitialized === "true" ? false : true} onClick={deleteFiles}>Delete All PDFs<br />Remove Vector</Button>
                            </div>
                            <span className="DeletedFilesMessage">
                                {dataDeleted}
                            </span>
                        </span>
                    }
                    {vectorSelection === 'local_s3' &&
                        <span className="HundoContainer">
                            <div className="chat-messages-crawl" id="chatMessages">
                                {crawlPrompt !== '' &&
                                    <p className={`You-message`}>
                                        <span className={`You-title`}><strong>Prompt:</strong></span>
                                        <span className="MessageText">{crawlPrompt}</span>
                                    </p>
                                }
                                {crawlResponse !== '' &&
                                    <p className={`Bot-message`}>
                                        <span className={`Bot-title`}><strong>Response:</strong></span>
                                        <span className="MessageText" dangerouslySetInnerHTML={{ __html: crawlResponse }}></span>
                                    </p>
                                }
                                {reindexResponse !== '' &&
                                    <p className={`Bot-message`}>
                                        <span className={`Bot-title`}><strong>Backend:</strong></span>
                                        <span className="MessageText">{reindexResponse}</span>
                                    </p>
                                }
                                {isBufferingCrawl &&
                                    <div className="dots">
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                    </div>
                                }
                                {isBufferingReindex &&
                                    <div className="dots">
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                    </div>
                                }
                            </div>
                            <p className="VectorSelection2">Input local AWS CLI Profile Name & Full S3 Path you are downloading from below. This will download recursively. This only works if you're hosting the backend on your local machine, or you have the profile defined where the backend is hosted.</p>
                            <div className="user-input-crawl-s3">
                                <TextField type="text"
                                    className="profile-input"
                                    value={userInputProfile}
                                    onChange={(e) => setUserInputProfile(e.target.value)}
                                    placeholder="Local AWS CLI Profile Name."
                                />
                                <TextField type="text"
                                    value={userInputS3Path}
                                    onChange={(e) => setUserInputS3Path(e.target.value)}
                                    placeholder="Full S3 path (e.g. s3://xyz/abc/de)."
                                />
                                <Button type="Button" onClick={downloadS3} disabled={isBufferingCrawl}>Go</Button>
                            </div>
                        </span>
                    }
                    {vectorSelection === 'kendra' &&
                        <span className="HundoContainer">
                            <div className="chat-messages-crawl" id="chatMessages">
                                {crawlPrompt !== '' &&
                                    <p className={`You-message`}>
                                        <span className={`You-title`}><strong>Prompt:</strong></span>
                                        <span className="MessageText">{crawlPrompt}</span>
                                    </p>
                                }
                                {crawlResponse !== '' &&
                                    <p className={`Bot-message`}>
                                        <span className={`Bot-title`}><strong>Response:</strong></span>
                                        <span className="MessageText" dangerouslySetInnerHTML={{ __html: crawlResponse }}></span>
                                    </p>
                                }
                                {reindexResponse !== '' &&
                                    <p className={`Bot-message`}>
                                        <span className={`Bot-title`}><strong>Backend:</strong></span>
                                        <span className="MessageText">{reindexResponse}</span>
                                    </p>
                                }
                                {isBufferingCrawl &&
                                    <div className="dots">
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                    </div>
                                }
                                {isBufferingReindex &&
                                    <div className="dots">
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                    </div>
                                }
                            </div>
                            <p className="VectorSelection2">Input local AWS CLI Profile Name & Kendra Index ID to instantiate connection to Kendra.</p>
                            <div className="user-input-crawl-s3">
                                <TextField type="text"
                                    className="profile-input"
                                    value={userInputProfile}
                                    onChange={(e) => setUserInputProfile(e.target.value)}
                                    placeholder="Local AWS CLI Profile Name."
                                />
                                <TextField type="text"
                                    value={userInputKendraId}
                                    onChange={(e) => setUserInputKendraId(e.target.value)}
                                    placeholder="Kendra Index ID"
                                />
                                <Button type="Button" onClick={instantiateKendra} disabled={isBufferingCrawl}>Go</Button>
                            </div>
                        </span>
                    }
                    {vectorSelection === 'local_crawl' &&
                        <span className="HundoContainer">
                            <div className="chat-messages-crawl" id="chatMessages">
                                {crawlPrompt !== '' &&
                                    <p className={`You-message`}>
                                        <span className={`You-title`}><strong>Prompt:</strong></span>
                                        <span className="MessageText">{crawlPrompt}</span>
                                    </p>
                                }
                                {crawlResponse !== '' &&
                                    <p className={`Bot-message`}>
                                        <span className={`Bot-title`}><strong>Response:</strong></span>
                                        <span className="MessageText" dangerouslySetInnerHTML={{ __html: crawlResponse }}></span>
                                    </p>
                                }
                                {reindexResponse !== '' &&
                                    <p className={`Bot-message`}>
                                        <span className={`Bot-title`}><strong>Backend:</strong></span>
                                        <span className="MessageText">{reindexResponse}</span>
                                    </p>
                                }
                                {isBufferingCrawl &&
                                    <div className="dots">
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                    </div>
                                }
                                {isBufferingReindex &&
                                    <div className="dots">
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                    </div>
                                }
                            </div>
                            <p className="VectorSelection2">Input any seed URL(s) to be crawled below. The database will instantiate automatically.</p>
                            <div className="user-input-crawl">
                                <textarea
                                    value={userInputCrawl}
                                    onChange={(e) => setUserInputCrawl(e.target.value)}
                                    placeholder="Input any seed URL(s) to be crawled, line separated or spaces between."
                                />
                                <Button type="Button" onClick={crawlReindex} disabled={isBufferingCrawl}>Crawl</Button>
                            </div>
                        </span>
                    }
                    {vectorSelection === 'local_load' &&
                        <span className="HundoContainer">
                            <div className="chat-messages-crawl" id="chatMessages">
                                {crawlPrompt !== '' &&
                                    <p className={`You-message`}>
                                        <span className={`You-title`}><strong>Prompt:</strong></span>
                                        <span className="MessageText">{crawlPrompt}</span>
                                    </p>
                                }
                                {crawlResponse !== '' &&
                                    <p className={`Bot-message`}>
                                        <span className={`Bot-title`}><strong>Response:</strong></span>
                                        <span className="MessageText" dangerouslySetInnerHTML={{ __html: crawlResponse }}></span>
                                    </p>
                                }
                                {reindexResponse !== '' &&
                                    <p className={`Bot-message`}>
                                        <span className={`Bot-title`}><strong>Backend:</strong></span>
                                        <span className="MessageText">{reindexResponse}</span>
                                    </p>
                                }
                                {isBufferingCrawl &&
                                    <div className="dots">
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                    </div>
                                }
                                {isBufferingReindex &&
                                    <div className="dots">
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                    </div>
                                }
                            </div>
                            <p className="VectorSelection2">Select which PDF files you want to index and load to in-memory database. The database will instantiate automatically.</p>
                            <div type="Button" className="file-upload-label">
                                <div className="file-input-container">
                                    <label htmlFor="pdfUpload" className="file-input-label">
                                        <input
                                            type="file"
                                            accept=".pdf"
                                            id="pdfUpload"
                                            onChange={handleFileUpload}
                                            multiple
                                            style={{ display: "none" }}
                                        />
                                        <div className="choose-file-Button">Choose PDF File(s)</div>
                                    </label>
                                </div>
                            </div>
                        </span>
                    }
                </div>
            </div>
            <Button type="Button" className="CrawlReindex" onClick={() => setCrawlModal(!crawlModal)}>
                <svg viewBox="0 0 32 32">
                    <path d="M16 0c-8.837 0-16 2.239-16 5v4c0 2.761 7.163 5 16 5s16-2.239 16-5v-4c0-2.761-7.163-5-16-5z"></path>
                    <path d="M16 17c-8.837 0-16-2.239-16-5v6c0 2.761 7.163 5 16 5s16-2.239 16-5v-6c0 2.761-7.163 5-16 5z"></path>
                    <path d="M16 26c-8.837 0-16-2.239-16-5v6c0 2.761 7.163 5 16 5s16-2.239 16-5v-6c0 2.761-7.163 5-16 5z"></path>
                </svg>
            </Button>
            <Button type="Button" className="PromptEditButton" onClick={() => setPromptModal(!promptModal)}>
                <svg viewBox="0 0 24 28">
                    <path d="M22.937 5.938c0.578 0.578 1.062 1.734 1.062 2.562v18c0 0.828-0.672 1.5-1.5 1.5h-21c-0.828 0-1.5-0.672-1.5-1.5v-25c0-0.828 0.672-1.5 1.5-1.5h14c0.828 0 1.984 0.484 2.562 1.062zM16 2.125v5.875h5.875c-0.094-0.266-0.234-0.531-0.344-0.641l-4.891-4.891c-0.109-0.109-0.375-0.25-0.641-0.344zM22 26v-16h-6.5c-0.828 0-1.5-0.672-1.5-1.5v-6.5h-12v24h20zM7.5 12c0.172-0.219 0.484-0.266 0.703-0.094l0.797 0.594c0.219 0.172 0.266 0.484 0.094 0.703l-2.844 3.797 2.844 3.797c0.172 0.219 0.125 0.531-0.094 0.703l-0.797 0.594c-0.219 0.172-0.531 0.125-0.703-0.094l-3.531-4.703c-0.125-0.172-0.125-0.422 0-0.594zM20.031 16.703c0.125 0.172 0.125 0.422 0 0.594l-3.531 4.703c-0.172 0.219-0.484 0.266-0.703 0.094l-0.797-0.594c-0.219-0.172-0.266-0.484-0.094-0.703l2.844-3.797-2.844-3.797c-0.172-0.219-0.125-0.531 0.094-0.703l0.797-0.594c0.219-0.172 0.531-0.125 0.703 0.094zM10.344 23.906c-0.281-0.047-0.453-0.313-0.406-0.578l2.156-12.984c0.047-0.281 0.313-0.453 0.578-0.406l0.984 0.156c0.281 0.047 0.453 0.313 0.406 0.578l-2.156 12.984c-0.047 0.281-0.313 0.453-0.578 0.406z"></path>
                </svg>
            </Button>
            <Button type="Button" className="IssueIndicator" onClick={() => setCrawlModal(!crawlModal)}
                style={{
                    display: currentVector === "faiss" ? (vectorInitialized === "false" ? 'flex' : 'none') : 'none'
                }}
            >
                <svg viewBox="0 0 32 32">
                    <path d="M16 2.899l13.409 26.726h-26.819l13.409-26.726zM16 0c-0.69 0-1.379 0.465-1.903 1.395l-13.659 27.222c-1.046 1.86-0.156 3.383 1.978 3.383h27.166c2.134 0 3.025-1.522 1.978-3.383h0l-13.659-27.222c-0.523-0.93-1.213-1.395-1.903-1.395v0z"></path>
                    <path d="M18 26c0 1.105-0.895 2-2 2s-2-0.895-2-2c0-1.105 0.895-2 2-2s2 0.895 2 2z"></path>
                    <path d="M16 22c-1.105 0-2-0.895-2-2v-6c0-1.105 0.895-2 2-2s2 0.895 2 2v6c0 1.105-0.895 2-2 2z"></path>
                </svg>
                <div className="bubble right">The Vector Database is not initialized. Click here or the database button below to upload files or connect to another Vector Database.</div>
            </Button>
        </div>
    );
};

export default Anthropic;

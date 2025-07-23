// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT.

import React, { useState } from 'react';
import { Button, TextField, Card, Heading, Flex, Text, View } from '@aws-amplify/ui-react';
import proxy_url from './proxy';

const api_root_url = proxy_url;

const AgentCapabilities = (props) => {
    const [userInput, setUserInput] = useState('');
    const [isExecuting, setIsExecuting] = useState(false);
    const [agentMessages, setAgentMessages] = useState([
        { author: 'Agent', message: 'I can help you perform actions like web searches, opening browsers, and reading web pages. What would you like me to do?' }
    ]);
    const [selectedAction, setSelectedAction] = useState(null);
    const [actionParams, setActionParams] = useState({});

    const handleActionSelect = (action) => {
        setSelectedAction(action);
        setActionParams({});
    };

    const handleParamChange = (paramName, value) => {
        setActionParams({
            ...actionParams,
            [paramName]: value
        });
    };

    const executeAction = () => {
        if (!selectedAction) {
            addMessage('Agent', 'Please select an action first.');
            return;
        }

        setIsExecuting(true);
        
        // Validate parameters
        if (selectedAction === 'web_search' && !actionParams.query) {
            addMessage('Agent', 'Please enter a search query.');
            setIsExecuting(false);
            return;
        }
        
        if (selectedAction === 'read_webpage' && !actionParams.url) {
            addMessage('Agent', 'Please enter a URL to read.');
            setIsExecuting(false);
            return;
        }

        // Add user message
        let userMessage = '';
        if (selectedAction === 'web_search') {
            userMessage = `Search for: ${actionParams.query}`;
        } else if (selectedAction === 'open_browser') {
            userMessage = `Open browser to: ${actionParams.url || 'Google'}`;
        } else if (selectedAction === 'read_webpage') {
            userMessage = `Read webpage: ${actionParams.url}`;
        }
        
        addMessage('You', userMessage);

        // Execute the action
        try {
            // Check if backend is running
            if (selectedAction === 'web_search') {
                // Mock response for web search
                setTimeout(() => {
                    const mockResults = [
                        {title: `Result for ${actionParams.query} 1`, link: `https://example.com/1?q=${actionParams.query}`, snippet: `This is a sample result for ${actionParams.query}...`},
                        {title: `Result for ${actionParams.query} 2`, link: `https://example.com/2?q=${actionParams.query}`, snippet: `Another sample result for ${actionParams.query}...`},
                    ];
                    
                    const results = mockResults.map(result => 
                        `- ${result.title}\n  ${result.link}\n  ${result.snippet}`
                    ).join('\n\n');
                    
                    addMessage('Agent', `Found ${mockResults.length} results for "${actionParams.query}"\n\n${results}`);
                    setIsExecuting(false);
                    setSelectedAction(null);
                    setActionParams({});
                }, 1000);
            } else if (selectedAction === 'open_browser') {
                // Mock response for open browser
                setTimeout(() => {
                    addMessage('Agent', `Browser opened with URL: ${actionParams.url || 'https://www.google.com'}`);
                    setIsExecuting(false);
                    setSelectedAction(null);
                    setActionParams({});
                }, 1000);
            } else if (selectedAction === 'read_webpage') {
                // Mock response for read webpage
                setTimeout(() => {
                    addMessage('Agent', `Successfully read content from ${actionParams.url}\n\nContent preview:\nThis is a sample content from the webpage. In a real implementation, this would contain actual content from the webpage. The content would be extracted using a web scraping library like BeautifulSoup in Python. For now, this is just a placeholder to demonstrate the functionality.`);
                    setIsExecuting(false);
                    setSelectedAction(null);
                    setActionParams({});
                }, 1000);
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage('Agent', `Error executing action: ${error.message}`);
            setIsExecuting(false);
            setSelectedAction(null);
            setActionParams({});
        }
    };

    const addMessage = (author, message) => {
        setAgentMessages(prevMessages => [...prevMessages, { author, message }]);
    };

    const formatMessage = (message) => {
        return message.split('\n').map((line, i) => (
            <React.Fragment key={i}>
                {line}
                <br />
            </React.Fragment>
        ));
    };

    return (
        <div className="chat-container" style={{ height: 'calc(100vh - 60px)', display: 'flex', flexDirection: 'column' }}>
            <div className="chat-messages" id="chatMessages" style={{ flex: 1, minHeight: '200px', overflow: 'auto' }}>
                {agentMessages.map((message, index) => (
                    <p key={index} className={`${message.author}-message`} style={{ fontSize: '12px', padding: '6px', marginBottom: '6px', borderRadius: '3px' }}>
                        <span className="MessageText" style={{ fontSize: '12px', lineHeight: '1.4' }}>
                            {formatMessage(message.message)}
                        </span>
                    </p>
                ))}
            </div>
            
            {isExecuting && (
                <div className="dots" style={{ margin: '6px 0' }}>
                    <div className="dot" style={{ width: '5px', height: '5px', margin: '0 2px' }}></div>
                    <div className="dot" style={{ width: '5px', height: '5px', margin: '0 2px' }}></div>
                    <div className="dot" style={{ width: '5px', height: '5px', margin: '0 2px' }}></div>
                </div>
            )}
            
            <div className="agent-actions" style={{ backgroundColor: '#f8f8f8', borderRadius: '4px', padding: '8px', marginBottom: '8px' }}>
                <Heading level={5} style={{ fontSize: '14px', marginBottom: '6px' }}>Available Actions</Heading>
                <Flex direction="row" gap="0.5rem" wrap="wrap">
                    <Button 
                        onClick={() => handleActionSelect('web_search')}
                        variation={selectedAction === 'web_search' ? 'primary' : 'default'}
                        size="small"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                    >
                        Web Search
                    </Button>
                    <Button 
                        onClick={() => handleActionSelect('open_browser')}
                        variation={selectedAction === 'open_browser' ? 'primary' : 'default'}
                        size="small"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                    >
                        Open Browser
                    </Button>
                    <Button 
                        onClick={() => handleActionSelect('read_webpage')}
                        variation={selectedAction === 'read_webpage' ? 'primary' : 'default'}
                        size="small"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                    >
                        Read Webpage
                    </Button>
                </Flex>
            </div>
            
            {selectedAction && (
                <Card variation="outlined" className="action-params" style={{ padding: '8px', marginBottom: '8px', boxShadow: '0 1px 2px rgba(0,0,0,0.1)' }}>
                    <Heading level={6} style={{ fontSize: '13px', marginBottom: '6px', fontWeight: '600' }}>
                        {selectedAction === 'web_search' ? 'Web Search' : 
                         selectedAction === 'open_browser' ? 'Open Browser' : 'Read Webpage'}
                    </Heading>
                    
                    {selectedAction === 'web_search' && (
                        <TextField
                            label="Search Query"
                            value={actionParams.query || ''}
                            onChange={(e) => handleParamChange('query', e.target.value)}
                            placeholder="Enter search query"
                            size="small"
                            labelHidden={false}
                            style={{ fontSize: '12px', marginBottom: '6px' }}
                        />
                    )}
                    
                    {(selectedAction === 'open_browser' || selectedAction === 'read_webpage') && (
                        <TextField
                            label="URL"
                            value={actionParams.url || ''}
                            onChange={(e) => handleParamChange('url', e.target.value)}
                            placeholder={selectedAction === 'open_browser' ? 'https://www.google.com (optional)' : 'Enter URL to read'}
                            size="small"
                            labelHidden={false}
                            style={{ fontSize: '12px', marginBottom: '6px' }}
                        />
                    )}
                    
                    <Button 
                        onClick={executeAction}
                        variation="primary"
                        isDisabled={isExecuting}
                        className="execute-button"
                        size="small"
                        style={{ fontSize: '12px', padding: '4px 8px', marginTop: '6px' }}
                    >
                        Execute Action
                    </Button>
                </Card>
            )}
            
            <div className="user-input">
                <Button 
                    type="Button" 
                    className="ClearHistory" 
                    onClick={() => setAgentMessages([{ author: 'Agent', message: 'I can help you perform actions like web searches, opening browsers, and reading web pages. What would you like me to do?' }])}
                    disabled={agentMessages.length === 1}
                >
                    Clear History
                </Button>
            </div>
        </div>
    );
};

export default AgentCapabilities;
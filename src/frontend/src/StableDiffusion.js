// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT.

import React, { useState, useEffect } from 'react';
import proxy_url from './proxy'

// const api_root_url = "http://bedrockchatbotalb-1278255413.us-east-1.elb.amazonaws.com"
const api_root_url = proxy_url

const StableDiffusion = (props) => {
    const [chatMessages, setChatMessages] = useState([]);
    const [userInput, setUserInput] = useState('');
    const [isBuffering, setIsBuffering] = useState(false)
    const [apiMethod, setApiMethod] = useState('/api/call-stablediffusion')
    const [selectedModel, setSelectedModel] = useState('')
    const [imageText, setImageText] = useState('');
    const [imageResponse, setImageResponse] = useState('');

    useEffect(() => {
        // Code to run after component has mounted

        setSelectedModel(props.modelSelected)
    }, [props.modelSelected
    ]);

    

    const handleSubmit = (event) => {
        event.preventDefault();
        setIsBuffering(true);
        const payload = {
          "modelId": "stability.stable-diffusion-xl",
          "contentType": "application/json",
          "accept": "application/json",
          "body": JSON.stringify({
            "text_prompts": [
              {"text": userInput}
            ],
            "cfg_scale": 10,
            "seed": 0,
            "steps": 50
          })
        };
    
        fetch(api_root_url+"/api/call-stablediffusion", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
          if (data.result === "success" && data.artifacts.length > 0) {
            const base64Data = data.artifacts[0].base64;
            const imageUrl = "data:image/jpeg;base64," + base64Data;
            setImageResponse(<img src={imageUrl} alt="Generated Image" />);
          } else {
            setImageResponse("Image API failed to generate the image.");
          }
        })
        .catch(() => {
          setImageResponse("Image API request failed.");
        }).finally(() => {
            setIsBuffering(false)
        });
      };


    return (
        <div className="chat-container">
            <div className="chat-messages" id="chatMessages">

            </div>
            <div id="imageResponse">{imageResponse}</div>
            {isBuffering &&
                <div className="dots">
                    <div className="dot"></div>
                    <div className="dot"></div>
                    <div className="dot"></div>
                </div>
            }
            <div className="user-input">
                <textarea
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="Type your message..."
                />
                <button type="button" onClick={handleSubmit} disabled={isBuffering}>Send</button>
            </div>
        </div>
    );
};

export default StableDiffusion;

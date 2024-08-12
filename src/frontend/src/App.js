// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT.

import './App.css';
import '@aws-amplify/ui-react/styles.css';
import React, { useState } from 'react';
import Anthropic from './Anthropic';
import Amazon from './Amazon';
import AI21 from './AI21'
import StableDiffusion from './StableDiffusion';
import { Button, Menu, MenuItem, MenuButton } from '@aws-amplify/ui-react';

const modelOptions = [
    'Anthropic: Claude',
    'Amazon: Titan',
    'AI21: Jurassic2',
    'Stability AI: Stable Diffusion'
]

const App = ({ signOut }) => {
    const [modelSelected, setModelSelected] = useState('Anthropic: Claude');
    const [anthropicMessages, setAnthropicMessages] = useState([]);
    const [amazonMessages, setAmazonMessages] = useState([]);
    const [ai21Messages, setAi21Messages] = useState([]);
    const [infoModal, setInfoModal] = useState(false)
    const [kendraInstantiated, setKendraInstantiated] = useState(false)
    const [currentVector, setCurrentVector] = useState('faiss')
    const [promptTemplate, setPromptTemplate] = useState("Use the context to answer the question at the end. If you don't know the answer from the context, do not answer from your knowledge and be precise. Don't fake the answer.")

    const middleSetVector = (input) => {
        console.log('input: '+ input)
        setCurrentVector(input)
    }

    const getModelComponent = () => {
        switch(modelSelected){
            case 'Anthropic: Claude':
                return (
                    <Anthropic modelSelected={modelSelected} 
                    anthropicMessages={anthropicMessages} 
                    setAnthropicMessages={setAnthropicMessages} 
                    currentVector={currentVector}
                    setCurrentVector={middleSetVector}
                    kendraInstantiated={kendraInstantiated}
                    setKendraInstantiated={setKendraInstantiated}
                    promptTemplate={promptTemplate}
                    setPromptTemplate={setPromptTemplate}
                    />
                );
            case 'Amazon: Titan':
                return (
                    <Amazon modelSelected={modelSelected} amazonMessages={amazonMessages} setAmazonMessages={setAmazonMessages} currentVector={currentVector}
                    setCurrentVector={middleSetVector}
                    kendraInstantiated={kendraInstantiated}
                    setKendraInstantiated={setKendraInstantiated}/>
                );
            case 'AI21: Jurassic2':
                return (
                    <AI21 modelSelected={modelSelected} ai21Messages={ai21Messages} setAi21Messages={setAi21Messages} currentVector={currentVector}
                    setCurrentVector={middleSetVector}
                    kendraInstantiated={kendraInstantiated}
                    setKendraInstantiated={setKendraInstantiated} />
                );
            case 'Stability AI: Stable Diffusion':
                return (
                    <StableDiffusion modelSelected={modelSelected} />
                );
            default:
                break;
      }
    }



    return (
        <div className="App">
            <div className="airwolf-header2">
                <svg className="bedrockDemo" viewBox="0 0 24 24" version="1.1" >
                    <title>Icon-Architecture/16/Arch_Amazon-Bedrock_16</title>
                    <defs>
                        <linearGradient x1="0%" y1="100%" x2="100%" y2="0%" id="linearGradient-1">
                            <stop  offset="0%"></stop>
                            <stop  offset="100%"></stop>
                        </linearGradient>
                    </defs>
                    <g id="Icon-Architecture/16/Arch_Amazon-Bedrock_16" >
                        <g id="Icon-Service/16/Amazon-Bedrock_16" transform="translate(4.000000, 4.000000)" fill="#FFFFFF">
                            <path d="M8,14.1397014 L5.574,14.9487014 L4.628,14.3177014 L5.658,13.9737014 L5.342,13.0257014 L3.574,13.6147014 L3,13.2327014 L3,10.4997014 C3,10.3107014 2.893,10.1377014 2.724,10.0527014 L1,9.19070136 L1,6.80870136 L2.5,6.05870136 L4,6.80870136 L4,8.49970136 C4,8.68970136 4.107,8.86270136 4.276,8.94770136 L6.276,9.94770136 L6.724,9.05270136 L5,8.19070136 L5,6.80870136 L6.724,5.94770136 C6.893,5.86270136 7,5.68970136 7,5.49970136 L7,3.99970136 L6,3.99970136 L6,5.19070136 L4.5,5.94070136 L3,5.19070136 L3,2.76770136 L4,2.10070136 L4,3.99970136 L5,3.99970136 L5,1.43470136 L5.574,1.05170136 L8,1.86070136 L8,14.1397014 Z M13.5,12.9997014 C13.775,12.9997014 14,13.2237014 14,13.4997014 C14,13.7757014 13.775,13.9997014 13.5,13.9997014 C13.225,13.9997014 13,13.7757014 13,13.4997014 C13,13.2237014 13.225,12.9997014 13.5,12.9997014 L13.5,12.9997014 Z M12.5,1.99970136 C12.775,1.99970136 13,2.22370136 13,2.49970136 C13,2.77570136 12.775,2.99970136 12.5,2.99970136 C12.225,2.99970136 12,2.77570136 12,2.49970136 C12,2.22370136 12.225,1.99970136 12.5,1.99970136 L12.5,1.99970136 Z M14.5,7.99970136 C14.775,7.99970136 15,8.22370136 15,8.49970136 C15,8.77570136 14.775,8.99970136 14.5,8.99970136 C14.225,8.99970136 14,8.77570136 14,8.49970136 C14,8.22370136 14.225,7.99970136 14.5,7.99970136 L14.5,7.99970136 Z M13.092,8.99970136 C13.299,9.58070136 13.849,9.99970136 14.5,9.99970136 C15.327,9.99970136 16,9.32770136 16,8.49970136 C16,7.67270136 15.327,6.99970136 14.5,6.99970136 C13.849,6.99970136 13.299,7.41970136 13.092,7.99970136 L9,7.99970136 L9,5.99970136 L12.5,5.99970136 C12.776,5.99970136 13,5.77670136 13,5.49970136 L13,3.90770136 C13.581,3.70070136 14,3.15070136 14,2.49970136 C14,1.67270136 13.327,0.999701362 12.5,0.999701362 C11.673,0.999701362 11,1.67270136 11,2.49970136 C11,3.15070136 11.419,3.70070136 12,3.90770136 L12,4.99970136 L9,4.99970136 L9,1.49970136 C9,1.28470136 8.862,1.09370136 8.658,1.02570136 L5.658,0.0257013622 C5.511,-0.0232986378 5.351,-0.00129863776 5.223,0.0837013622 L2.223,2.08370136 C2.084,2.17670136 2,2.33270136 2,2.49970136 L2,5.19070136 L0.276,6.05270136 C0.107,6.13770136 0,6.31070136 0,6.49970136 L0,9.49970136 C0,9.68970136 0.107,9.86270136 0.276,9.94770136 L2,10.8087014 L2,13.4997014 C2,13.6667014 2.084,13.8237014 2.223,13.9157014 L5.223,15.9157014 C5.306,15.9717014 5.402,15.9997014 5.5,15.9997014 C5.553,15.9997014 5.606,15.9917014 5.658,15.9737014 L8.658,14.9737014 C8.862,14.9067014 9,14.7157014 9,14.4997014 L9,11.9997014 L11.293,11.9997014 L12.146,12.8537014 L12.159,12.8407014 C12.061,13.0407014 12,13.2627014 12,13.4997014 C12,14.3267014 12.673,14.9997014 13.5,14.9997014 C14.327,14.9997014 15,14.3267014 15,13.4997014 C15,12.6727014 14.327,11.9997014 13.5,11.9997014 C13.262,11.9997014 13.04,12.0607014 12.841,12.1597014 L12.854,12.1467014 L11.854,11.1467014 C11.76,11.0527014 11.633,10.9997014 11.5,10.9997014 L9,10.9997014 L9,8.99970136 L13.092,8.99970136 Z" id="Fill-7"></path>
                        </g>
                    </g>
                    </svg>
                <div className="OtherModels">
                    <p>Model Selection: </p>
                    <Menu menuAlign="start" className="NavMenu"
                    trigger={
                        <MenuButton id="menuButtonMain" width="40%">
                          {modelSelected}
                        </MenuButton>
                      }>
                    {modelOptions.map((option) => (
                        <MenuItem
                            key={option}
                            className={`model-option ${modelSelected === option ? 'active' : ''}`}
                            onClick={() => setModelSelected(option)}
                        >
                            {option}
                        </MenuItem>
                        
                    ))}
                    </Menu>
                </div>
                {/* <Button className="signOut" onClick={signOut}>Sign out</Button> */}
            </div>

            <div id="ContentSection">
                { getModelComponent() }
            </div>
            <div className="InfoModal" style={{
                height: `100vh`,
                width: infoModal ? '940px': '40px',

            }}>
                <div className="InnerInfoModal" style={{ display: infoModal ? 'unset': 'none', opacity: infoModal ? 1 : 0 }}>
                    <h1>Amazon Bedrock</h1>
                    <p>This Demo was built with Amazon Bedrock.</p>

                    <p>Amazon Bedrock is a new service that makes FMs from Amazon and leading AI startups including AI21 Labs, Anthropic, and Stability AI accessible via an API. Bedrock is the easiest way for customers to build and scale generative AI-based applications using FMs, democratizing access for all builders.</p>
                    <div className="llm-section">
                        <h2>Amazon Titan By Amazon</h2>
                        <p>Amazon is a leader in applying ML to e-commerce, cloud computing, online advertising, and digital streaming services. The Amazon Titan models leverage Amazon’s 20+ years of ML experience.</p>
                    </div>
                    <div className="llm-section">
                        <h2>Claude By Anthropic</h2>
                        <p>Anthropic is an AI safety and research company offering the Claude family of large language models. These models are purpose-built for AI-based assistance use-cases such as obtaining customer service or comprehending documents.</p>
                    </div>
                    <div className="llm-section">
                        <h2>Stable Diffusion By Stability AI</h2>
                        <p>Stability AI is a generative AI company with a goal to inspire global creativity and innovation.</p>
                    </div>
                    <div className="llm-section">
                        <h2>Jurrasic 2 by AI21 Labs </h2>
                        <p>AI21 Labs enables businesses to build generative AI powered solutions by providing API access to our proprietary best-in-class language models, driving innovation, unlocking new capabilities, scaling businesses, and more.</p>
                    </div>
                    <br/>
                    <br/>
                </div>
                <div className="InfoModalButton" onClick={ () => setInfoModal(!infoModal) }>
                    { infoModal === false &&
                        <svg viewBox="0 0 32 32">
                            <path d="M14 9.5c0-0.825 0.675-1.5 1.5-1.5h1c0.825 0 1.5 0.675 1.5 1.5v1c0 0.825-0.675 1.5-1.5 1.5h-1c-0.825 0-1.5-0.675-1.5-1.5v-1z"></path>
                            <path d="M20 24h-8v-2h2v-6h-2v-2h6v8h2z"></path>
                            <path d="M16 0c-8.837 0-16 7.163-16 16s7.163 16 16 16 16-7.163 16-16-7.163-16-16-16zM16 29c-7.18 0-13-5.82-13-13s5.82-13 13-13 13 5.82 13 13-5.82 13-13 13z"></path>
                        </svg>
                    }
                    { infoModal &&
                        <svg className="closeModal" viewBox="0 0 24 24">
                        <path d="M14.578 8.016l1.406 1.406-2.578 2.578 2.578 2.578-1.406 1.406-2.578-2.578-2.578 2.578-1.406-1.406 2.578-2.578-2.578-2.578 1.406-1.406 2.578 2.578zM21 3q0.797 0 1.406 0.609t0.609 1.406v13.969q0 0.797-0.609 1.406t-1.406 0.609h-18q-0.797 0-1.406-0.609t-0.609-1.406v-13.969q0-0.797 0.609-1.406t1.406-0.609h18zM21 19.078v-14.063h-18v14.063h18z"></path>
                        </svg>
                    }
                </div>
            </div>
        </div>
    );
}


export default App;

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
import LogoComponent from './components/LogoComponent.js';
const modelOptions = [
    'Anthropic: Claude',
    'Amazon: Titan',
    'AI21: Jurassic2',
    'Stability AI: Stable Diffusion'
]

const App = ({ signOut }) => {
    document.title = 'TE TEL.me (BETA)';
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
            
              <LogoComponent /> 
            
               <span className ="site-title">TEL.me (Beta)</span>    
                    
                {/* <Button className="signOut" onClick={signOut}>Sign out</Button> */}
            </div>

            <div id="ContentSection">
                { getModelComponent() }
            </div>
           
        </div>
    );
}


export default App;

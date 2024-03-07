import React, { useEffect , useState} from 'react';

const KeyListener = ({initialBtnSettingClass,updateBtnSettingClass}) => {

  //const [initClassValue, setNewClassValue] = useState(initialBtnSettingClass);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.altKey && (event.key === 'H' || event.key === 'h' )) {
        handleAltH();
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };

    
  }, []); 

  const handleAltH = () => {

    console.info('Current value: ', initialBtnSettingClass);


    let changedValue = initialBtnSettingClass;

    if(changedValue === 'show-setting-btns'){
        changedValue = 'hide-setting-btns';
    } else {
        changedValue = 'show-setting-btns';
    }

    updateBtnSettingClass(changedValue);
  };

};

export default KeyListener;

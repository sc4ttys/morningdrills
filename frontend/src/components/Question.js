import React, { useState } from 'react';

function Question({ question, answer, subAnswers, handleInputChange }) {
  const [isOpen, setIsOpen] = useState(false);

  const togglePanel = (event) => {
    event.preventDefault();
    setIsOpen(!isOpen);
  };

  return (
    <div>
      <button
        className="accordion w-full text-left py-2 px-4 border rounded flex justify-between items-center toplevelquestion"
        onClick={togglePanel}
      >
        {question.text}
        <span>{isOpen ? '▲' : '▼'}</span>
      </button>
      {isOpen &&  question.subquestions.length < 1 && (
        <>
        <textarea rows="4" cols="50" className='w-full px-2 py-1 border rounded mb-2' value={answer} placeholder='Answer here' onChange={(event)=>handleInputChange(event,question.id)} ></textarea></>
      )
      }

      {isOpen && question.subquestions.length > 0 && (
        <>
        <div className='subquestions'>
        {question.subquestions.map((subquestion) => (
              <SubQuestion
              key={subquestion.id}
              subquestion={subquestion}
              parentId={question.id}
              subAnswer={subAnswers[`${question.id}.${subquestion.id}`] || ''}
              handleInputChange={handleInputChange}
            />
              ))}
        </div> 
        </>
      )
      }
    </div>
  );
}


function SubQuestion({ subquestion, parentId, subAnswer, handleInputChange }) {
  const [isSubOpen, setIsOpen] = useState(false);
  const uniqueId = `${parentId}.${subquestion.id}`;

  const togglePanel = (event) => {
    event.preventDefault();
    setIsOpen(!isSubOpen);
  };

  return (
    <div key={subquestion.id} className="ml-4">
      <button
        className="accordion w-full text-left py-2 px-4 border rounded flex justify-between items-center"
        onClick={togglePanel}
      >
        {subquestion.text}
        <span>{isSubOpen ? '▲' : '▼'}</span>
      </button>
      {isSubOpen && (
        <>
        <span className="block mt-2">{subquestion.id} Current Answer: {uniqueId}</span>
        <><textarea rows="4" 
            cols="50" 
            className='w-full px-2 py-1 border rounded mb-2' 
            value={subAnswer} placeholder='Answer here' 
            onChange={(event)=>handleInputChange(event,uniqueId)} ></textarea></>
        </>
      )}
    </div>
  );
}





export default Question;

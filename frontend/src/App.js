import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Question from './components/Question';
import Modal from './components/Modal';
import './components/Modal.css';
import Cookies from 'js-cookie'; 

function App() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [topicId, setTopicId] = useState(null);
  const [topicName, setTopicName] = useState("")
  const [isModalShowing, setIsModalShowing] = useState(false);
  const [modalContent, setModalContent] = useState(null);
  const [database, setDatabase] = useState(Cookies.get('selectedDatabase') || 'morningdrills');

  const fetchQuestions = () => {
    axios.get(`http://127.0.0.1:5000/api/questions?database=${database}`)
      .then(response => {
        const { topic_id, topic_name, questions } = response.data;
        console.log(response.data)
        setTopicId(topic_id);
        setTopicName(topic_name);
        setQuestions(questions);
      })
      .catch(error => {
        console.error('There was an error fetching the questions!', error);
      });
  };
  
  useEffect(() => {
    fetchQuestions();
  }, [database]);



  const handleDatabaseChange = (event) => {
    const selectedDatabase = event.target.value;
    setDatabase(selectedDatabase);
    Cookies.set('selectedDatabase', selectedDatabase); // Save selected database to cookies
  };

  const handleInputChange = (event, id) => {
    const { value } = event.target;
    setAnswers(prevAnswers => ({
      ...prevAnswers,
      [id]: value,
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    // Initialize answers with empty strings for all questions
    const allAnswers = {};
    questions.forEach(question => {
      allAnswers[question.id] = answers[question.id] || '';
      question.subquestions.forEach(subquestion => {
        allAnswers[subquestion.id] = answers[subquestion.id] || '';
      });
    });    

    axios.post('http://127.0.0.1:5000/api/submit', { topic_id: topicId, answers: allAnswers, database })
      .then(response => {
        const { percentage_correct, considered_success, questionMarks } = response.data;
        console.log(response.data);
        displayResults(percentage_correct, considered_success, questionMarks);
      })
      .catch(error => {
        console.error('There was an error submitting the answers!', error);
      });
  };

  const displayResults = (percentage_correct, considered_success, questionMarks) => {
    setModalContent(
      <div>
        <h2>Results</h2>
        <p><strong>Percentage Correct:</strong> {percentage_correct}%</p>
        <p><strong>Considered Success:</strong> {considered_success ? 'Yes' : 'No'}</p>
        <h3>Question Marks</h3>
        <ul>
          {Object.entries(questionMarks).map(([qid, [answer, verdict, correctAnswer]]) => (
            <li key={qid} class={verdict ? 'greenbox' : 'redbox'}>
              <strong>Question {qid}: {verdict ? 'Correct' : 'Incorrect'}</strong> <br />
              <h4>Your answer:</h4>
              {answer} <br />
              <h4>Expected answer:</h4>
              {correctAnswer}
              
            </li>
          ))}
        </ul>
        <button className="modal-close-button" onClick={closeModal}>
          Close
        </button>
      </div>
    );
    setIsModalShowing(true);
  };

  const closeModal = () => {
    setIsModalShowing(false);
  };

  const formatDate = (date) => {
    const options = { day: '2-digit', month: 'long', year: 'numeric' };
    return date.toLocaleDateString('en-GB', options);
  };

  const todayDate = formatDate(new Date());


  return (
    <div className="bg-gray-100 flex items-center justify-center min-h-screen">
      <div className="bg-white shadow-md rounded-lg p-6 w-full max-w-md">
      <div className="mb-4">
            <label htmlFor="database-select"><strong>Select type:</strong></label>
            <select id="database-select" value={database} onChange={handleDatabaseChange}>
              <option value="morningdrills">Network Drills</option>
              <option value="linuxdrills">Linux Drills</option>
              <option value="pythondrills">Python Drills</option>
            </select>
          </div>
        <h1 className="text-2xl font-bold text-center mb-4">Morning Drills</h1>
        <div className="mb-4">
            <p><strong>Date:</strong> { todayDate }</p> 
            <p><strong>Topic: </strong>{ topicName } </p>
        </div>
        <form onSubmit={handleSubmit}>
          {questions.map(question => (
            <Question 
              key={question.id} 
              question={question} 
              answer={answers[question.id] || ''} 
              subAnswers={answers}
              handleInputChange={handleInputChange} 
            />
          ))}
          <div className="mt-4 text-center">
            <button type="submit" className="bg-blue-500 text-white py-2 px-4 rounded">SUBMIT</button>
          </div>
        </form>
      </div>
      <Modal isShowing={isModalShowing} hide={closeModal}>
        {modalContent}
      </Modal>
    </div>
  );
}


export default App;

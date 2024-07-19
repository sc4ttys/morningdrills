from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from flask_cors import CORS, cross_origin
import logging, argparse, requests
from datetime import date
import json, os, pprint
from dotenv import load_dotenv
from collections import defaultdict
import requests
import random

# load env variables from .env file
load_dotenv() 
# Get environment variables
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')


## dev mode? 
DEVMODE = False

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
#CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:3000"}})
Session = sessionmaker()

app.config['SQLALCHEMY_BINDS'] = {
    'morningdrills': f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/morningdrills',
    'linuxdrills': f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/linuxdrills',
    'pythondrills': f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/pythondrills'
}
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,
    'max_overflow': 40,
    'pool_timeout': 30,
    'pool_recycle': 1800
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
currentQustionBank = defaultdict(int)

logging.basicConfig(level=logging.DEBUG)


class Topic(db.Model):
    __tablename__ = 'topics'
    __bind_key__ = 'morningdrills'

    topic_id = db.Column(db.Integer, primary_key=True, nullable=False)
    topic_name = db.Column(db.Text, nullable=True)
    frequency = db.Column(db.Integer, default=10)
    last_tried = db.Column(db.Date, nullable=True)
    last_success = db.Column(db.Date, nullable=True)

class Question(db.Model):
    __tablename__ = 'questionbank'
    __bind_key__ = 'morningdrills'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('topics.topic_id'), nullable=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.topic_id'), nullable=False)
    question = db.Column(db.Text, nullable=True)
    answer = db.Column(db.Text, nullable=True)

    parent = db.relationship('Topic', foreign_keys=[parent_id])
    topic = db.relationship('Topic', foreign_keys=[topic_id])


class AnswerLog(db.Model):
    __tablename__ = 'answers'
    __bind_key__ = 'morningdrills'

    answer_id = db.Column(db.Integer, primary_key=True, nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.topic_id'), nullable=False)
    success = db.Column(db.Boolean, nullable=False)
    answers = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=True)

    topic = db.relationship('Topic', foreign_keys=[topic_id])




@app.route('/api/questions', methods=['GET'])
@cross_origin()
def get_questions():
    database = request.args.get('database', 'morningdrills')
    engine = db.get_engine(app, bind=database)
    session = Session(bind=engine)
    db_name = database

    if not DEVMODE:
        randomnumbe = random.randint(0,10000)
        #topic = session.query(Topic).order_by(Topic.last_success.desc().nullsfirst()).first()
        if randomnumbe % 2 == 0:
            topic = session.query(Topic).filter_by(last_success=None).order_by(Topic.last_tried.asc()).first()
        else:
            topic = session.query(Topic).filter_by(last_success=None).order_by(Topic.last_tried.desc()).first()
    else:
        topic = session.query(Topic).filter_by(topic_id="5").first()
    if not topic:
        session.close()
        return jsonify({'message': 'No topics found'}), 404

    topic_id = topic.topic_id
    questions = session.query(Question).filter_by(topic_id=topic_id, parent_id=None).all()
    app.logger.debug(f'Selected topic: {topic}')
    data = []
    for question in questions:
        currentQustionBank[question.id] = question.question
        subquestions = session.query(Question).filter_by(parent_id=question.id).all()
        subquestions_data = [{'id': sub.id, 'text': sub.question} for sub in subquestions]
        data.append({'id': question.id, 'text': question.question, 'subquestions': subquestions_data})
    session.close()

    app.logger.debug(f'Returning data: {data}')
    pprint.pprint(currentQustionBank)
    return jsonify({'topic_id': topic.topic_id, 'topic_name': topic.topic_name, 'questions': data})


@app.route('/api/submit', methods=['POST'])
@cross_origin()
def submit_answers():
    answers = request.json.get('answers')
    topic_id = request.json.get('topic_id')
    database = request.json.get('database', 'morningdrills')
    db_name = database

    if not answers or not topic_id:
        return jsonify({'message': 'Invalid request'}), 400
    
    engine = db.get_engine(app, bind=database)
    session = Session(bind=engine)
    
    # Evaluate if answers are correct 
    total = len(answers)
    print("total answers: " + str(total))
    correct = 0
    questionMarks = defaultdict(int)
    for qid,answer in answers.items(): 
        correctAnswer = session.query(Question).filter_by(id=qid).first()
        if correctAnswer:
            correctAnswer = correctAnswer.answer
        verdict = eval_answer(qid, answer)
        if verdict: 
            correct += 1            
        questionMarks[qid] = [answer,verdict,correctAnswer]
    pprint.pprint(questionMarks) 

    if total > 0:
        percentage_correct = (correct / total) * 100
    else:
        percentage_correct = 0 

    if percentage_correct > 75: 
        considerCorrect = True
    else:
        considerCorrect = False

    # Convert answers dictionary to JSON string
    answers_json = json.dumps(answers)

    if not DEVMODE: # only update database if in production mode 
        # Create a single AnswerLog entry to push answer to the db
        new_answer_log = AnswerLog(
            topic_id=topic_id,
            success=considerCorrect,
            answers=answers_json,
            date=date.today()
        )
        session.add(new_answer_log)
        # update topics last success if successfull 
        if considerCorrect:
            session.query(Topic).filter_by(topic_id=topic_id).update({"last_success": date.today()})
        else: 
            session.query(Topic).filter_by(topic_id=topic_id).update({"last_tried":date.today()})
        session.commit()
        session.close()


    session.close()
    return jsonify({'message': 'Answers submitted successfully!','percentage_correct':percentage_correct, 'considered_success':considerCorrect, 'questionMarks':questionMarks})



# Constants for ai values
DEFAULT_MODEL = "llama3"
SERVER_IP = "192.168.0.47"
PORT = 11435

def send_request(model, query):
    url = f"http://{SERVER_IP}:{PORT}/api/generate"
    payload = {
        "model": model,
        "prompt": query,
        "stream": False
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get('response', 'No response received from the server.')
    else:
        return f"Error: {response.status_code} - {response.text}"


def eval_answer(qid, answer):
    if answer == "": 
        return False
    og_question = currentQustionBank[int(qid)]
    match  db_name:
        case "morningdrills":
            prompt_intro = "Act like a network engineering tutor for university students. You will be validating student answer to a question. Validate the question as correct if it's at least 75 percent correct. Otherwise, validate it as incorrect. I will provide you with the set question and student's answer. You will provide only single word response, either 'correct' or 'incorrect'"
        case "linuxdrills":
            prompt_intro = "Act like a tutor for a student who is preparing for the LPIC1 and LPIC2 Linux Exams. You will be validating student answer to a question. Validate the question as correct if it's at least 90 percent correct. Otherwise, validate it as incorrect. I will provide you with the set question and student's answer. You will provide only single word response, either 'correct' or 'incorrect'"
        case "pythondrills":
            prompt_intro = "Act like a tutor for a student who is learning Python3 for their job. You will be validating student answer to a question. Validate the question as correct if it's at least 90 percent correct. Otherwise, validate it as incorrect. I will provide you with the set question and student's answer. You will provide only single word response, either 'correct' or 'incorrect'"
    
    prompt_q = " * This is the set question: " + str(og_question)
    prompt_a = " * This is the set answer: " + answer 
    prompt_full = prompt_intro + prompt_q + prompt_a
    pprint.pprint(prompt_full)
    response = send_request("llama3", prompt_full)
    pprint.pprint(response)
    if response == "Correct":
        return True
    elif response == "Incorrect":
        return False 





if __name__ == '__main__':
    #db.create_all()
    app.run(debug=True)


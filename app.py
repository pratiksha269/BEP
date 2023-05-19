from duckduckgo_search import ddg
from sklearn.metrics.pairwise import cosine_similarity
from joblib import load
import numpy as np
import pandas as pd
import re
import msgConstant as msgCons
import random
from flask import jsonify
import secrets
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, session
from flask_sqlalchemy import SQLAlchemy

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = "m4xpl0it"


def make_token():
    """
    Creates a cryptographically-secure, URL-safe string
    """
    return secrets.token_urlsafe(16)


class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))


@app.route("/")
def index():
    return render_template("index.html")


userSession = {}


@app.route("/user")
def index_auth():
    my_id = make_token()
    userSession[my_id] = -1
    return render_template("index_auth.html", sessionId=my_id)


@app.route("/instruct")
def instruct():
    return render_template("instructions.html")


@app.route("/upload")
def bmi():
    return render_template("bmi.html")


@app.route('/pred_page')
def pred_page():
    pred = session.get('pred_label', None)
    f_name = session.get('filename', None)
    return render_template('pred.html', pred=pred, f_name=f_name)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form["uname"]
        passw = request.form["passw"]

        login = user.query.filter_by(username=uname, password=passw).first()
        if login is not None:
            return redirect(url_for("index_auth"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form['uname']
        mail = request.form['mail']
        passw = request.form['passw']

        register = user(username=uname, email=mail, password=passw)
        db.session.add(register)
        db.session.commit()

        return redirect(url_for("login"))
    return render_template("register.html")


all_result = {
    'name': '',
    'age': 0,
    'gender': ''
}

user_input = {
    'Logical quotient rating': '',
    'hackathons': 0,
    'coding skills rating': '',
    'public speaking points': '',
    'self-learning capability?': '',
    'reading and writing skills': '',
    'memory capability score': '',
    'interested career area': '',
    'Type of company want to settle in?': '',
    'Management or Technical': '',
    'hard/smart worker': ''
}


import pickle

# Load the saved model from file
with open('model/nn.pkl', 'rb') as f:
    model = pickle.load(f)

def predict_job_role(input_list):

    inverse_mapping = {
    'Suggested Job Role': {0: 'AERO SPACE', 1: 'Agriculture', 2: 'Artificial Intelligence', 3: 'Bio Medical', 4: 'CHEMICAL', 5: 'CIVIL', 6: 'Computer IT', 7: 'DS', 8: 'ELECTRICAL', 9: 'ELECTRONICS', 10: 'FOOD TECH', 11: 'MECHANICAL'}
    }   

    # Make a prediction using the trained model and the user inputs
    prediction = model.predict([input_list])[0]

    # Convert the prediction back to the original label using the inverse mapping
    predicted_job_role = inverse_mapping['Suggested Job Role'][prediction]

    print(f"The suggested job role is: {predicted_job_role}")

    details = getDiseaseInfo(predicted_job_role)

    return f"<b>{predicted_job_role}</b><br>{details}", predicted_job_role


def getDiseaseInfo(keywords):
    try:
        results = ddg(keywords, region='wt-wt', safesearch='Off', time='y')
        return results[0]['body']
    except Exception as e:return ''



global input_list
input_list = []

@app.route('/ask', methods=['GET', 'POST'])
def chat_msg():

    user_message = request.args["message"].lower()
    sessionId = request.args["sessionId"]

    rand_num = random.randint(0, 4)
    response = []
    if request.args["message"] == "undefined":

        response.append(msgCons.WELCOME_GREET[rand_num])
        response.append("What is your good name?")
        input_list.clear()
        return jsonify({'status': 'OK', 'answer': response})
    else:

        currentState = userSession.get(sessionId)

        if currentState == -1:
            response.append(
                "Hi "+user_message+", To predict your Engineering branch based on skills, we need some information about you. Is that okay with you? y/n")
            userSession[sessionId] = userSession.get(sessionId) + 1
            all_result['name'] = str(user_message).capitalize()

        if currentState == 0:
            username = all_result['name']
            response.append(username+", what is you age?")
            userSession[sessionId] = userSession.get(sessionId) + 1

        if currentState == 1:
            pattern = r'\d+'
            result = re.findall(pattern, user_message)
            if len(result) == 0:
                response.append("Invalid input please provide valid age.")
            else:
                all_result['age'] = float(result[0])
                username = all_result['name']
                response.append(username+", Your gender ?")
                response.append("M - Male")
                response.append("F - Female")
                userSession[sessionId] = userSession.get(sessionId) + 1

        if currentState == 2:

            if 'fe' in user_message.lower():
                all_result['gender'] = 'f'
            else:
                all_result['gender'] = 'm'

            username = all_result['name']
            response.append(username+", Which activity u do at weekend?")
            response.append('<b>1. Dismantle/Build house hold appliance</b>')
            response.append('<b>2. Gaming</b>')
            response.append('<b>3. Gardening</b>')
            response.append('<b>4. Try new food</b>')

            userSession[sessionId] = userSession.get(sessionId) + 1

        if currentState == 3:

            if '1' in  user_message or 'house' in user_message:
                input_list.append(0)

            elif '2' in  user_message or 'gaming' in user_message:
                input_list.append(1)

            elif '3' in  user_message or 'gardening' in user_message:
                input_list.append(2)

            elif '4' in  user_message or 'food' in user_message:
                input_list.append(3)

            else:
                response.append('<b>Invalid Choice please select valid option.</b>')
                return jsonify({'status': 'OK', 'answer': response})
        
            print(input_list)

            username = all_result['name']
            response.append(username+", which one you prefer Indoor/Outdoor?")
            response.append('<b>1. Indoor</b>')
            response.append('<b>2. Outdoor</b>')


            userSession[sessionId] = userSession.get(sessionId) + 1


        if currentState == 4:


            if '1' in  user_message or 'in' in user_message:
                input_list.append(0)

            elif '2' in  user_message or 'out' in user_message:
                input_list.append(1)

            else:
                response.append('<b>Invalid Choice please select valid option.</b>')
                return jsonify({'status': 'OK', 'answer': response})
            
        
            print(input_list)

            username = all_result['name']
            response.append(username+", select your favourite school subject.")
            response.append('<b>1. Biology</b>')
            response.append('<b>2. Chemistry</b>')
            response.append('<b>3. Comp/IT</b>')
            response.append('<b>4. Electronics</b>')
            response.append('<b>5. Languages</b>')
            response.append('<b>6. Maths</b>')
            response.append('<b>7. Physics</b>')
            response.append('<b>8. Social Science</b>')

            userSession[sessionId] = userSession.get(sessionId) + 1

        if currentState == 5:

            if '1' in  user_message or 'biology' in user_message:
                input_list.append(0)

            elif '2' in  user_message or 'chemistry' in user_message:
                input_list.append(1)

            elif '3' in  user_message or 'comp' in user_message:
                input_list.append(2)

            elif '4' in  user_message or 'electronics' in user_message:
                input_list.append(3)

            elif '5' in  user_message or 'languages' in user_message:
                input_list.append(4)

            elif '6' in  user_message or 'maths' in user_message:
                input_list.append(5)

            elif '7' in  user_message or 'physics' in user_message:
                input_list.append(6)

            elif '8' in  user_message or 'social' in user_message:
                input_list.append(7)

            else:
                response.append('<b>Invalid Choice please select valid option.</b>')
                return jsonify({'status': 'OK', 'answer': response})
        
            print(input_list)
            
            username = all_result['name']
            response.append(username+", What hobbies or interests do you prefer engaging in?")
            response.append('<b>1. Build Lego</b>')
            response.append('<b>2. Flying drone</b>')
            response.append('<b>3. Repair electronics</b>')
            response.append('<b>4. Surf website</b>')

            userSession[sessionId] = userSession.get(sessionId) + 1

        if currentState == 6:

            if '1' in  user_message or 'build' in user_message:
                input_list.append(0)

            elif '2' in  user_message or 'flying' in user_message:
                input_list.append(1)

            elif '3' in  user_message or 'repair' in user_message:
                input_list.append(2)

            elif '4' in  user_message or 'website' in user_message:
                input_list.append(3)

            else:
                response.append('<b>Invalid Choice please select valid option.</b>')
                return jsonify({'status': 'OK', 'answer': response})
        
            print(input_list)
            
            username = all_result['name']
            response.append(username+", What interests you the most?")
            response.append('<b>1. Experimentation</b>')
            response.append('<b>2. Robots</b>')
            response.append('<b>3. Solving problem</b>')
            response.append('<b>4. Spaceships</b>')

            userSession[sessionId] = userSession.get(sessionId) + 1

        if currentState == 7:


            if '1' in  user_message or 'experimentation' in user_message:
                input_list.append(0)

            elif '2' in  user_message or 'robots' in user_message:
                input_list.append(1)

            elif '3' in  user_message or 'solving' in user_message:
                input_list.append(2)

            elif '4' in  user_message or 'spaceships' in user_message:
                input_list.append(3)

            else:
                response.append('<b>Invalid Choice please select valid option.</b>')
                return jsonify({'status': 'OK', 'answer': response})
        
            print(input_list)

            username = all_result['name']
            response.append(
                username+", Which type of work you prefer?")
            response.append('<b>1. Logical</b>')
            response.append('<b>2. Physical</b>')

            userSession[sessionId] = userSession.get(sessionId) + 1

        if currentState == 8:

            if '1' in  user_message or 'logi' in user_message:
                input_list.append(0)

            elif '2' in  user_message or 'phys' in user_message:
                input_list.append(1)

            else:
                response.append('<b>Invalid Choice please select valid option.</b>')
                return jsonify({'status': 'OK', 'answer': response})
        
            print(input_list)
            
            username = all_result['name']
            response.append(
                username+", Are you good at drawing?")
            response.append('<b>1. Yes</b>')
            response.append('<b>2. No</b>')

            userSession[sessionId] = userSession.get(sessionId) + 1

        if currentState == 9:

            if '1' in  user_message or 'yes' in user_message:
                input_list.append(0)

            elif '2' in  user_message or 'no' in user_message:
                input_list.append(1)

            else:
                response.append('<b>Invalid Choice please select valid option.</b>')
                return jsonify({'status': 'OK', 'answer': response})
        
            print(input_list)
            
            username = all_result['name']
            response.append(username+", Which club u would join?")
            response.append('<b>1. Arts</b>')
            response.append('<b>2. Coding</b>')
            response.append('<b>3. Cooking</b>')
            response.append('<b>4. Cultural</b>')
            response.append('<b>5. Environment/NGO</b>')
            response.append('<b>6. Gaming</b>')
            response.append('<b>7. Photography</b>')

            userSession[sessionId] = userSession.get(sessionId) + 1

        if currentState == 10:

            if '1' in  user_message or 'arts' in user_message:
                input_list.append(0)

            elif '2' in  user_message or 'coding' in user_message:
                input_list.append(1)

            elif '3' in  user_message or 'cooking' in user_message:
                input_list.append(2)

            elif '4' in  user_message or 'cultural' in user_message:
                input_list.append(3)

            elif '5' in  user_message or 'ngo' in user_message:
                input_list.append(4)

            elif '6' in  user_message or 'gaming' in user_message:
                input_list.append(5)

            elif '7' in  user_message or 'photography' in user_message:
                input_list.append(6)

            else:
                response.append('<b>Invalid Choice please select valid option.</b>')
                return jsonify({'status': 'OK', 'answer': response})
        
            print(input_list)


            username = all_result['name']
            response.append(
                username+", Have you ever participated in any hackethons or competitions?")
            response.append('<b>1. Yes</b>')
            response.append('<b>2. No</b>')

            userSession[sessionId] = userSession.get(sessionId) + 1

        if currentState == 11:

            if '1' in  user_message or 'yes' in user_message:
                input_list.append(0)

            elif '2' in  user_message or 'no' in user_message:
                input_list.append(1)
            else:
                response.append('<b>Invalid Choice please select valid option.</b>')
                return jsonify({'status': 'OK', 'answer': response})
        
            print(input_list)



            username = all_result['name']
            response.append(
                username+", How about you memory capability score?")
            response.append('<b>1. Poor</b>')
            response.append('<b>2. Medium</b>')
            response.append('<b>3. Excellent</b>')

            userSession[sessionId] = userSession.get(sessionId) + 1

        if currentState == 12:

            
            if '1' in  user_message or 'poo' in user_message:
                input_list.append(0)

            elif '2' in  user_message or 'med' in user_message:
                input_list.append(1)

            elif '3' in  user_message or 'exe' in user_message:
                input_list.append(2)

            else:
                response.append('<b>Invalid Choice please select valid option.</b>')
                return jsonify({'status': 'OK', 'answer': response})
        

            print(input_list)

            job, type = predict_job_role(input_list)
            response.append(all_result['name']+", "
                "As per your mentioned skills following Engineering branch will be recommended.")
            response.append(job)
            response.append(
                f'<a href="https://www.google.com/search?q={type} collegs near me" target="_blank">View Colleges</a>')
            userSession[sessionId] = 100


        return jsonify({'status': 'OK', 'answer': response})


if __name__ == "__main__":

    db.create_all()
    app.run(debug=False, port=3000)

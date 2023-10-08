from flask import Flask, render_template, jsonify, send_file
import json
from datetime import datetime
import requests
import pandas as pd
import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    # You can read the JSON data and return it as JSON
    with open('blackhole.json', 'r') as json_file:
        data = json.load(json_file)
    return jsonify(data)

@app.route('/image')
def get_image():
    # Return the test.jpg image file
    return send_file('test.jpg', mimetype='image/jpeg')


UID = "u-s4t2ud-bd8c3b57f05ac6f234a7fe621d4ce5640c69677562fd8522c527f0cd1684cab7"
SECRET = "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"

# RESQUESTING ACCESS_TOKEN TO VALHALLA USING SECRETS
headers = {'Content-type':'application/json'}
r = requests.post(f"https://api.intra.42.fr/oauth/token?grant_type=client_credentials&client_id={UID}&client_secret={SECRET}", headers=headers)
access_token = r.json()['access_token']

def get_all_users():

    # print("\033[0;33mREQUESTING FOR ALL USERS\033[0m")
    if (os.path.exists('cadets.json')):
        # print('\033[0;33mFinished fetching\033[0m')
        return

    i = 1
    tol = 100
    full_list = []
    while tol == 100:
        url = f"https://api.intra.42.fr/v2/campus/34/users?per_page=100&page={i}&access_token={access_token}"
        response = requests.get(url)
        full_list += response.json()
        tol = len(response.json())
        i += 1
    # output results to "user_42kl.json"
    with open("user_42kl.json","w") as f:
        f.write(json.dumps(full_list))
    # print("\033[0;33mREQUEST COMPLETED\033[0m")

def get_keys_by_type(dictionaries, key):
    # Initialize an empty list to store the keys
    keys = []
    # Iterate over the dictionaries
    for dictionary in dictionaries:
        # Iterate over the keys in the dictionary
        if key in dictionary.keys():
            keys.append(dictionary[key])
    # Return the list of keys
    return keys

def filter_cadets():
    # print("\033[0;33mFILTERING CADETS FROM PISCINERS\033[0m")
    try:
        with open("user_42kl.json", "r") as f:
            users_42kl = json.loads(f.read())
        with open("cadets.json", "r") as f:
            passed_users = json.loads(f.read())
        with open("dumpster.json", "r") as f:
            non_passed_users = json.loads(f.read())
    except:
        with open("user_42kl.json", "r") as f:
            users_42kl = json.loads(f.read())
            passed_users = []
            non_passed_users = []

    passed_user_logins = get_keys_by_type(passed_users, "login")
    non_passed_user_logins = get_keys_by_type(non_passed_users, "login")
    for user in users_42kl:
        if (user['login'] not in non_passed_user_logins and user['login'] not in passed_user_logins):
            response = requests.get(f'https://api.intra.42.fr/v2/users/{user["login"]}?access_token={access_token}')
            try:
                if len(response.json()['cursus_users']) > 1 and response.json()['cursus_users'][1]['grade'] in ["Member","Learner"]:
                    passed_users.append(response.json())
                    # print(f"{response.json()['login']} passed the piscine")
            except Exception as err:
                print(f"Error occured: {err}")
        else:
            print(user['login'], "discovered before")
    with open("cadets.json", "w") as f:
        f.write(json.dumps(passed_users))
    with open("dumpster.json", "w") as f:
        f.write(json.dumps(non_passed_users))
    # print("\033[0;33mCADETS FILTERED\033[0m")

def generate_sheet() -> list:
    dangerous_students = []

    # print(f"\033[0;33mGENERATING EXCEL SHEET\033[0m")
    with open("cadets.json", "r") as f:
        cadets = json.loads(f.read())
    current_datetime = datetime.utcnow()
    for cadet in cadets:
        dangerous_data = {}
        try:
            target_datetime = datetime.strptime(cadet['cursus_users'][1]['blackholed_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
            time_difference = target_datetime - current_datetime
            days_until_target = time_difference.days
            if days_until_target < 90 and days_until_target >= 0:
                dangerous_data['blackhole'] = days_until_target + 1
                dangerous_data['fullname'] = cadet['usual_full_name']
                dangerous_data['login'] = cadet['login']
                dangerous_data['intra_link'] = "https://profile.intra.42.fr/users/" + cadet['login']
                dangerous_data['image'] = cadet['image']['link']
                dangerous_data['active'] = cadet['active?']
                dangerous_data['level'] = "{:.2f}".format(cadet['cursus_users'][1]['level'])
                dangerous_data['project_name'] = cadet['projects_users'][0]['project']['name']
                if (cadet['projects_users'][0]['status'] == 'finished'):
                    dangerous_data['marked_at'] = (cadet['projects_users'][0]['marked_at'])[0:10]
                else:
                    dangerous_data['marked_at'] = 'in progress'
                dangerous_students.append(dangerous_data)
        except TypeError:
            pass
    dangerous_students = sorted(dangerous_students, key=lambda x: x['blackhole'])
    return dangerous_students


def export(bh_students: list):
    pd.DataFrame(bh_students).to_csv('blackhole.csv', index=False)


@app.route('/call_function')
def my_function():
    try:
        # Read JSON data from the input JSON file
        with open("blackhole.json", 'r') as json_file:
            data = json.load(json_file)

        # Write the formatted data to a text file
        count_dict = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
        name_dict = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}
        for item in data:
            level = float(item['level'])
            name = item['fullname']
            login = item['login']
            full_str = f"- Cadet with LOGIN : {login} - {name}"
            if level >= 8.00:
                level = 8.00
            level_as_int = int(level)  # Convert to int if needed
            if level_as_int not in count_dict:
                count_dict[level_as_int] = 0
            count_dict[level_as_int] += 1
            name_dict[level_as_int].append(full_str)
        

        pdf_file = "final_report.pdf"
        doc = SimpleDocTemplate(pdf_file, pagesize=letter)

        # Define a list to hold the elements of the PDF (title, text, image, etc.)
        elements = []

        # Define a custom style for the title
        title_style = ParagraphStyle(name='TitleStyle', fontSize=18, alignment=0)

        image_path = "42.png"  # Replace with the path to your image
        img = Image(image_path, width=5 * inch, height=1.1 * inch)
        elements.append(img)
        elements.append(Spacer(1, 1 * inch))

        # Create a title
        title = Paragraph("Cadets BlackHole Days Report", title_style)
        elements.append(title)

        # Add space after the title
        elements.append(Spacer(1, 0.8 * inch))

        # Define the body text style
        body_style = getSampleStyleSheet()['Normal']
        custom_style = ParagraphStyle(name='CustomStyle', parent=body_style)
        custom_style.leftIndent = 20  # Adjust the indentation in points (1 inch = 72 points)

        # Add paragraphs of text to the report
        text = ""
        for key, val in count_dict.items():
            text  += f"Cadet(s) on level {key} has {int(val)}(s) that are getting absorbed by the blackhole.\n"
            paragraphs = Paragraph(text, body_style)
            elements.append(paragraphs)
            elements.append(Spacer(1, 0.2 * inch))
            text = ""
            if key in name_dict:
                for value in name_dict[key]:
                    # Create paragraphs based on name_dict content
                    text = f"{value}"
                    paragraph = Paragraph(text, custom_style)
                    elements.append(paragraph)
                    text = ""
            elements.append(Spacer(1, 0.2 * inch))


        # Build the PDF document
        doc.build(elements)

        return "True"
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "False"
    

if __name__ == '__main__':
    get_all_users()
    res = generate_sheet()
    with open("blackhole.json","w") as f:
        f.write(json.dumps(res))
    app.run(debug=True)
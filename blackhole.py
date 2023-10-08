from datetime import datetime
import requests
import json
import pandas as pd
import os

UID = "u-s4t2ud-bd8c3b57f05ac6f234a7fe621d4ce5640c69677562fd8522c527f0cd1684cab7"
SECRET = "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"

# RESQUESTING ACCESS_TOKEN TO VALHALLA USING SECRETS
headers = {'Content-type':'application/json'}
r = requests.post(f"https://api.intra.42.fr/oauth/token?grant_type=client_credentials&client_id={UID}&client_secret={SECRET}", headers=headers)
access_token = r.json()['access_token']

# Gets all users that are linked to 42KL Campus
# 42KL Campus id number is '34' if you wish to change to your campus please change this number in 'url'
# Each call on api gives us a list of 100 users
# To get the next 100 users we change the page number
# The loop will loop till theres less than 100 users in a page
# That means we have reach the end.
def get_all_users():

    print("\033[0;33mREQUESTING FOR ALL USERS\033[0m")
    if (os.path.exists('cadets.json')):
        print('\033[0;33mFinished fetching\033[0m')
        return

    # 'i' represent the page
    # 'tol' represents the number of results in a page 100 by default
    # 'full_list' stores all the results of the users in a json array.
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
    print("\033[0;33mREQUEST COMPLETED\033[0m")

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

# Seperating all Users into 2 groups, one for those that are 'Cadets' into 'cadets.json'
# Another into those that are not cadets 'dumpster.json'
# We will only be using 'cadets.json' in future since thats the data that we want.
def filter_cadets():
    print("\033[0;33mFILTERING CADETS FROM PISCINERS\033[0m")
    # if .json folder already exist then use back existing ones. this is when users decide to only update the list
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
    # we loop through each user to look for those that are cadets or not
    # if user pass the cadet check then we get api call for for that specific user for more info
    # The way we check if a user is a cadet or not is by checking the number of objects in ["cursus_users"]
    # The other thing we check for is if a user is a 'Member' which is a cadet that has pass the core program
    for user in users_42kl:
        if (user['login'] not in non_passed_user_logins and user['login'] not in passed_user_logins):
            response = requests.get(f'https://api.intra.42.fr/v2/users/{user["login"]}?access_token={access_token}')
            try:
                if len(response.json()['cursus_users']) > 1 and response.json()['cursus_users'][1]['grade'] in ["Member","Learner"]:
                    passed_users.append(response.json())
                    print(f"{response.json()['login']} passed the piscine")
            except Exception as err:
                print(f"Error occured: {err}")
        else:
            print(user['login'], "discovered before")
    # After we have seperated which user is a cadet and which is not
    # Write them out to 'cadets.json' & 'dumpster.json'
    with open("cadets.json", "w") as f:
        f.write(json.dumps(passed_users))
    with open("dumpster.json", "w") as f:
        f.write(json.dumps(non_passed_users))
    print("\033[0;33mCADETS FILTERED\033[0m")

# Now that we have all of the cadets data that we need
# We loop through all the cadets to get the info that we need
# name = name of cadet, period_from = Cadets start date, level = Cadet level,
# status = 'DROPPED OUT', 'CORE PROG', 'SPECIALISATION', blackhole = Date of cadet being absorbed by blackhole
def generate_sheet() -> list:
    dangerous_students = []

    print(f"\033[0;33mGENERATING EXCEL SHEET\033[0m")
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


if __name__ == "__main__":
    get_all_users()
    res = generate_sheet()
    with open("blackhole.json","w") as f:
        f.write(json.dumps(res))
    # export(res)
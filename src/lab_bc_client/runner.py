import requests
import shutil
import time
import datetime
import os
import zipfile
import time
import json
import sys
import configparser

#yuck but maybe:
requests.packages.urllib3.disable_warnings()

user_config_path = os.path.expanduser("~") + "/.config/lab-bc"
user_config_file = user_config_path + "/config.ini"

def create_config():
    config = configparser.ConfigParser()
    kerberos = input("Enter your kerberos:").lower().strip()
    mitid = int(input("Enter your MIT ID number (nine digits):").strip())
    config['Auth'] = {'kerberos': kerberos, 'mitid': mitid}
    # Write the configuration to a file
    os.makedirs(user_config_path, exist_ok=True)
    with open(user_config_file, 'w') as configfile:
        config.write(configfile)
    print("Configuration file written to:")
    print(user_config_file)

def get_config():
    config = configparser.ConfigParser()
    config.read(user_config_file)
    kerberos = config.get('Auth', 'kerberos')
    mitid = config.get('Auth', 'mitid')
    return [kerberos, mitid]

def main():
    HISTORY_ARCHIVE = '_history'
    OUTPUT_DIR = 'obj'
    SIM = 'sim'
    MODEL = 'model'
    IGNORES = [OUTPUT_DIR,HISTORY_ARCHIVE,SIM,MODEL]
    USER = None
    ID = None
    #MAIN_SERVER = "http://127.0.0.1:8000"
    MAIN_SERVER = "https://fpga3.mit.edu/lab-bc"
    SUBENDPT = "/submit_work" #api endpoint to submit work
    CHECKENDPT = "/check_work" #api endpoint to check and retrieve work
    FINISHENDPT = "/finish_work" #api endpoint to check and retrieve work
    ARCHIVE = "_submissions" #directory where tar files are stored

    TARGET_FILE = None
    RESULT_NAME = None
    command = sys.argv[1]
    if command == "configure":
        create_config()
        return
    elif command == "run":
        result = get_config()
        USER = result[0]
        ID = result[1]
        TARGET_FILE = sys.argv[2]
        RESULT_NAME = sys.argv[3]
    else:
        print(f'Command {command} is invalid.  Try either "configure" or "run")')
        return

    TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    SUBMIT_URL = MAIN_SERVER + SUBENDPT
    CHECK_URL = MAIN_SERVER + CHECKENDPT
    FINISH_URL = MAIN_SERVER + FINISHENDPT
    if TARGET_FILE == None or RESULT_NAME == None:
        print('Failure.')
    comp_file = f"{TIMESTAMP}_sub.zip"
    res_file = f"{TIMESTAMP}_res.zip"
    zf = zipfile.ZipFile(comp_file, "w")
    for dirname, subdirs, files in os.walk(TARGET_FILE):
      #print(f"{dirname}, {subdirs}, {files}")
        for dir in IGNORES:
            if dir in subdirs:
                subdirs.remove(dir)
        zf.write(dirname)
        for filename in files:
            if ".zip" not in filename:
                print(f"...zipping up: {dirname}/{filename}")
                zf.write(os.path.join(dirname, filename))
    zf.close()
    os.makedirs(f"{TARGET_FILE}/{HISTORY_ARCHIVE}", exist_ok=True)
    sub_location = f"{TARGET_FILE}/{HISTORY_ARCHIVE}/{comp_file}"
    shutil.move(comp_file, sub_location)
    print("---------------------------\n\n")
    files = [('file', open(sub_location,'rb'))]
    headers = {'Content-Transfer-Encoding': 'application/gzip'}
    params={"user":USER, "id":ID, "foldername":TARGET_FILE, "resultname":RESULT_NAME}
    #user is user
    #id is id (these two will be cross-checked)
    #foldername is the name of the project zipped
    #resultname is the name of the folder with foldername to zip and return
    response = requests.request("POST", SUBMIT_URL, params=params, headers=headers, data ={}, files = files, verify = False)
    #print(response.text)
    thing = json.loads(response.text)
    status = thing['meta']
    print(status)
    if status=="0":
        print(thing['message'])
        print("aborting task...")
        return
    job_id = thing['message']
    print(f"Job ID is :{job_id}. Job in Queue.")
    def getResult(jobid: str):
        #print("checking...")
        params={"user":USER, "id":ID, "jobid":jobid}
        response = requests.request("GET", CHECK_URL, params=params)
        if response.headers['content-type']=='application/json' or response.headers['content-type']=='text/plain; charset=utf-8':
            try:
                stuff = json.loads(response.text)
                if stuff['meta']=="1":
                    print(stuff['message'])
            except Exception as e:
                print(f"ERROR: {e}")
            #print(f'No File: "{response.text}"')
            return False
        else:
            result_location = f"{TARGET_FILE}/{HISTORY_ARCHIVE}/{res_file}"
            with open(result_location, "wb") as f:
                f.write(response.content)
            final_spot = f'{TARGET_FILE}/{RESULT_NAME}'
            if os.path.isdir(final_spot):
                shutil.rmtree(final_spot)
            os.mkdir(final_spot)
            print(f"going to unzip {result_location} into {final_spot}")
            with zipfile.ZipFile(result_location, 'r') as zip_ref:
                zip_ref.extractall(final_spot)
            response = requests.request("POST", FINISH_URL, params=params, verify = False)
            print(response.text)
            return True

    while not getResult(job_id):
        time.sleep(1)




if __name__ == "__main__":
    main()

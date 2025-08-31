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
import logging

#yuck but maybe:
requests.packages.urllib3.disable_warnings()

user_config_path = os.path.expanduser("~") + "/.config/lab-bc"
user_config_file = user_config_path + "/config.ini"

#used in configuration setup
SERVER_CHECK_ENDPOINT = '/config_test'
SERVER_CHECK_MESSAGE_GOOD = 'lab-bc service present!'
SERVER_CHECK_MESSAGE_KINDA_GOOD = 'lab-bc service present but invalid credentials!'

SUBENDPT = "/submit_work" #api endpoint to submit work
CHECKENDPT = "/check_work" #api endpoint to check and retrieve work
FINISHENDPT = "/finish_work" #final end step of handshake
ARCHIVE = "_submissions" #directory where tar files are stored

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'  # Resets text color and style to default

def create_config():
    config = configparser.ConfigParser()
    kerberos = input("Enter your kerberos:").lower().strip()
    mitid = int(input("Enter your MIT ID number (nine digits):").strip())
    server_endpoint = input("Enter the Lab-bc endpoint (for example fpga2.mit.edu/lab-bc):").lower().strip()
    server_endpoint_orig = server_endpoint
    server_endpoint = "https://"+server_endpoint
    #checking server endpoint and credentials while setting up:
    params={"user":kerberos, "id":mitid}
    try:
      response = requests.request("GET", server_endpoint + SERVER_CHECK_ENDPOINT, params=params)
    except Exception as e:
      print(f"Issue accessing lab-bc server: {server_endpoint}")
      print(f"Exiting. Configuration failed.")
      logging.error(f" {e}")
    if response.headers['content-type']=='application/json' :
      try:
        stuff = json.loads(response.text)
        print(stuff['message'])
        if stuff['message'] == SERVER_CHECK_MESSAGE_GOOD:
          config['Auth'] = {'kerberos': kerberos, 'mitid': mitid, 'server':server_endpoint,'additional_allows':[]}
          # Write the configuration to a file
          os.makedirs(user_config_path, exist_ok=True)
          with open(user_config_file, 'w') as configfile:
            config.write(configfile)
          print("Configuration file written to:")
          print(user_config_file)
        if stuff['message']== SERVER_CHECK_MESSAGE_KINDA_GOOD:
          print(f"Issue with your credentials! Contact Administrator of {server_endpoint_orig}")
      except Exception as e:
        print("Something went wrong!")
        print('\a')
        print(f"{e}")
        logging.error(f" {e}")

def get_config():
    config = configparser.ConfigParser()
    config.read(user_config_file)
    kerberos = config.get('Auth', 'kerberos')
    mitid = config.get('Auth', 'mitid')
    server = config.get('Auth', 'server')
    additional_allows = config.get('Auth', 'additional_allows')
    return [kerberos, mitid, server,additional_allows]

def colorizeMessage(message):
  new_message = ""
  for line in message.splitlines():
    if 'ERROR' in line:
      line = line.replace("ERROR","\033[1m\033[31mERROR\033[0m")
    elif 'CRITICAL WARNING' in line:
      line = line.replace("CRITICAL WARNING","\033[1m\033[33mCRITICAL WARNING\033[0m")
    elif 'WARNING' in line:
      line = line.replace("WARNING","\033[1m\033[93mWARNING\033[0m")
    elif 'INFO' in line:
      line = line.replace("INFO","\033[1m\033[34mINFO\033[0m")
    elif 'write_bitstream completed successfully' in line:
      line = f"\033[1m\033[92m{line}\033[0m"
    elif 'EARLY TERMINATION' in line:
      line = f"\033[1m\033[31m{line}\033[0m"
    print(f"{line}")

def main():
    HISTORY_ARCHIVE = '_history'
    OUTPUT_DIR = 'obj'
    SIM = 'sim'
    MODEL = 'model'
    CONTROL = 'ctrl'
    ALLOWS = ['xdc', 'sim','hdl','data','ip']
    IGNORES = [OUTPUT_DIR,HISTORY_ARCHIVE,SIM,MODEL,CONTROL,'.git','.DS_Store','util','sim_build','ctrl']
    USER = None
    ID = None
    #MAIN_SERVER = "http://127.0.0.1:8000"
    MAIN_SERVER = None #"https://fpga3.mit.edu/lab-bc2"
    ADD_ALLOWS = []
    TARGET_FOLDER = None
    RUN_FILE = None
    RESULT_NAME = 'obj' #override (no need to put here anymore)
    TYPE = None
    TARGET_MACHINE = "None"
    command = sys.argv[1]
    if command == "configure":
        create_config()
        return
    elif command == "build":
        result = get_config()
        USER = result[0]
        ID = result[1]
        MAIN_SERVER = result[2]
        ADD_ALLOWS = eval(result[3])
        TARGET_FOLDER = sys.argv[2]
        RUN_FILE = sys.argv[3]
        if RUN_FILE[-4:] != '.tcl':
          print(f'\033[1m\033[31mBuild file needs to be a .tcl script!\033[0m')
          return
        RESULT_NAME = 'obj'
        TYPE = "build"
        if (len(sys.argv)==5):
            TARGET_MACHINE = sys.argv[4]
    elif command == "simulate":
        result = get_config()
        USER = result[0]
        ID = result[1]
        MAIN_SERVER = result[2]
        ADD_ALLOWS = eval(result[3])
        TARGET_FOLDER = sys.argv[2]
        RUN_FILE = sys.argv[3]
        if RUN_FILE[-3:] != '.py':
          print(f'\033[1m\033[31mSimulation file needs to be a .py file running cocotb!\033[0m')
        RESULT_NAME = 'sim_build'
        TYPE = "simulate"
        if (len(sys.argv)==5):
            TARGET_MACHINE = sys.argv[4]
    else:
        print(f'\033[1m\033[31mCommand "{command}" is invalid.  Try "configure", "build", or "simulate"\033[0m')
        return

    TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    SUBMIT_URL = MAIN_SERVER + SUBENDPT
    CHECK_URL = MAIN_SERVER + CHECKENDPT
    FINISH_URL = MAIN_SERVER + FINISHENDPT
    if TARGET_FOLDER == None or RESULT_NAME == None:
        print('Failure.')
        return
    comp_file = f"{TIMESTAMP}_sub.zip"
    res_file = f"{TIMESTAMP}_res.zip"
    zf = zipfile.ZipFile(comp_file, "w")
    print("Zipping folders. Remember if the size of your total zip is >5MB, the server may reject it!")
    for dirname, subdirs, files in os.walk(TARGET_FOLDER):
      subdirs_copy = subdirs.copy()
      print(f"{os.path.abspath(dirname)} vs {os.path.abspath(TARGET_FOLDER)}")
      if os.path.abspath(dirname) == os.path.abspath(TARGET_FOLDER):
        for dir in subdirs_copy:
          if dir not in ALLOWS + ADD_ALLOWS:
            print(f"Ignoring {dir}")
            subdirs.remove(dir)
      #print(f"{dirname}, {subdirs}, {files}")
        #for dir in IGNORES:
        #    if dir in subdirs:
        #        subdirs.remove(dir)
      zf.write(dirname)
      for filename in files:
        if ".zip" not in filename and ".fst" not in filename and ".vcd" not in filename:
            print(f"...zipping up: {dirname}/{filename}")
            zf.write(os.path.join(dirname, filename))
    zf.close()
    os.makedirs(f"{TARGET_FOLDER}/{HISTORY_ARCHIVE}", exist_ok=True)
    sub_location = f"{TARGET_FOLDER}/{HISTORY_ARCHIVE}/{comp_file}"
    shutil.move(comp_file, sub_location)
    print("---------------------------\n\n")
    files = [('file', open(sub_location,'rb'))]
    headers = {'Content-Transfer-Encoding': 'application/gzip'}
    params={"user":USER, "id":ID, "foldername":TARGET_FOLDER, "resultname":RESULT_NAME,"runfile":RUN_FILE,'jobtype':TYPE,'requestedmachine':TARGET_MACHINE}
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
        print('\a')
        return
    job_id = thing['message']
    print(f"Job ID is :{job_id}. Job in Queue.")
    def getResult(jobid: str):
        params={"user":USER, "id":ID, "jobid":jobid}
        response = requests.request("GET", CHECK_URL, params=params)
        if response.headers['content-type']=='application/json' or response.headers['content-type']=='text/plain; charset=utf-8':
            try:
                stuff = json.loads(response.text)
                if stuff['meta']=="1":
                    colorizeMessage(stuff['message'])
            except Exception as e:
                logging.error(f" {e}")
                print('\a')
            return False
        else:
            result_location = f"{TARGET_FOLDER}/{HISTORY_ARCHIVE}/{res_file}"
            with open(result_location, "wb") as f:
                f.write(response.content)
            final_spot = f'{TARGET_FOLDER}/{RESULT_NAME}'
            if os.path.isdir(final_spot):
                shutil.rmtree(final_spot)
            os.mkdir(final_spot)
            print(f"going to unzip {result_location} into {final_spot}")
            with zipfile.ZipFile(result_location, 'r') as zip_ref:
                zip_ref.extractall(final_spot)
            response = requests.request("POST", FINISH_URL, params=params, verify = False)
            try:
                stuff = json.loads(response.text)
                if stuff['meta']=="1":
                    print(stuff['message'])
            except Exception as e:
                logging.error(f" {e}")
                print(f"\033[1m\033[31mERROR!: {e}\033[0m")
                print('\a')
                print('\a')
            print('\a') #make a ding!
            return True

    while not getResult(job_id):
        time.sleep(1)




if __name__ == "__main__":
    main()

import os
import csv
import datetime as dt
import ftplib
import smtplib, ssl
import json
from cryptography.fernet import Fernet
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

_KEY_ = b'_Eb-ez6gdiB8bU89Y8cwl9LlGFC_0Mbv1CbLS8qNVio='
email_text = email_subject = ""
repertory = os.getcwd()
file_send = file_no_send = 0


#######################################################
####################  DATE NOW  #######################
#######################################################
def date_now_config(month, year, day_shift):
    global date_now
    bissex = False
    fev = 29 if bissex else 28
    bissex = True if year % 4 == 0 else False

    if day_shift <= 0:
        if month == 3:
            month -= 1
            day_shift += fev

        elif month in [2, 4, 6, 8, 9, 11]:
            month -= 1
            day_shift += 31

        elif month in [5, 7, 10, 12]:
            month -= 1
            day_shift += 30

        else:
            month = 12
            year -= 1
            day_shift += 31

        if day_shift <= 0:
            return date_now_config(month, year, day_shift)

    day_shift = '0' + str(day_shift) if day_shift < 10 else str(day_shift)
    month = '0' + str(month) if month < 10 else str(month)

    return str(year) + '-' + str(month) + '-' + day_shift

#######################################################
##################  FICHIER LOG  ######################
#######################################################
def write_in_log(message):
    global repertory
    log_file = open(os.path.join(repertory, "log/log_test.txt"), "a")
    try:
        log_file.write(message)
    except Exception as e:
        print("ERROR:{},... {} Doesn't write in file log!!!!\n".format(e, message))
    log_file.close()

#######################################################
#################### SEND EMAIL #######################
#######################################################
def send_email(sender, recipient, subject, text_body, password):
    date_h_now = dt.datetime.now().strftime('%Y-%m-%d')

    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = subject

    message.attach(MIMEText(text_body, 'plain'))
    msg = message.as_string()
    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.connect('smtp.office365.com', 587)
        server.starttls(context=context)
        server.login(sender, password)
        server.sendmail(sender, recipient.split(','), msg)
        print("{} NOTE: Email sent succesfully!!!".format(date_h_now))
        write_in_log("{} NOTE: Email sent succesfully!!!".format(date_h_now))
        server.quit()
    except Exception as e:
        print("{} ERROR: SMTP server error, {}".format(date_h_now, e))
        write_in_log("{} ERROR: SMTP server error, {}".format(date_h_now, e))

#######################################################
########  NORMALISATIONS DES NOMS DE FICHIERS  ########
#######################################################
def normalisation_caractere(caractere):
    regex = ["!",".",","," ",";","§","ù","%","*","µ","¨","$","£","¤",
             "&","é","~","#","'","{","(","[","-","è","`","ç","^",
             "à","@",")","]","=","+","}","â","ä","ã","ô","ö","õ","ê",
             "ë","ï","î","û","ü","°","²","Â","Ä","Ã","Ô","Ö","Õ","Ê",
             "Ë","Î","Ï","Û","Ü"
            ]
    c = caractere
    for elt in regex:
        c = c.replace(elt, "")

    return c

#######################################################
############### LOADER LE FICHIER JSON ################
#######################################################
def load_json():
    global repertory
    loaded = False
    CONFIG_JSON = None
    date_now = dt.datetime.now().strftime('%Y-%m-%d')
    try:
        with open(os.path.join(repertory, "config.json"), encoding = "utf-8") as file_json:
            CONFIG_JSON = json.load(file_json)
            loaded = True
            print("{} NOTE: Json load successfully!!!!!".format(date_now))
            write_in_log("{} NOTE: Json load successfully!!!!! \n".format(date_now))

    except Exception as e:
        print("{} ERROR: Failed, {}!!!!!!!".format(date_now, e))
        write_in_log("{} ERROR: Failed, {}!!!!!!! \n".format(date_now, e))

    return CONFIG_JSON, loaded

#######################################################
########### CONNECTION AVEC LE SERVEUR FTP ############
#######################################################
def connect(host, user, mdp, port, time_out):
    date_h_now = dt.datetime.now().strftime('%Y-%m-%d')
    state = False
    session = None
    try:
        session = ftplib.FTP(host, user, mdp, timeout=time_out)
        state = True
        print("{} NOTE: Connection to server FTP succesfully done!!!!!".format(date_h_now))
        write_in_log("{} NOTE: Connection to server FTP succesfully done!!!!!!\n".format(date_h_now))
    except Exception as e:
        print("{} ERROR: Connection failed, {}!!!!".format(date_h_now, e))
        write_in_log("{} ERROR: Connection failed, {}!!!!\n".format(date_h_now, e))
    return state, session


#######################################################
################# FETCHING BACKUP LIST  ###############
#######################################################
def fetch_backup_list(chemin_principal, date_now, password, config_json):
    global email_text
    global email_subject
    date_h_now = ""
    state = False
    session = None
    date_h_now = dt.datetime.now().strftime('%Y-%m-%d')
    for elt in os.listdir(chemin_principal):
        if os.path.isdir(os.path.join(chemin_principal, elt)):
            fetch_backup_list(chemin_principal, date_now, password, config_json)
        else:
            file_time = dt.datetime.fromtimestamp(os.path.getctime(os.path.join(chemin_principal, elt))).strftime('%Y-%m-%d')
            if file_time == date_h_now:
                state, session = connect(config_json['ftp']['host'],
                                     config_json['ftp']['username'],
                                     password,
                                     config_json['ftp']['port'],
                                     config_json['timeout']
                )
                if state:
                    session.cwd(config_json['destination'])
                    filename = os.path.join(chemin_principal, elt)
                    file = open( filename, 'rb')
                    try:
                        print("{} NOTE: Sending file {} !!!".format(date_h_now, os.path.join(chemin_principal, elt)))
                        session.storbinary("STOR " + elt, file)
                        write_in_log("{} DONE: File {} uploaded successfully!!\n".format(date_h_now, elt))
                        email_text +=  "{} DONE: File \" {} \" uploaded successfully!!\n      ".format(date_h_now, elt)
                        print("{} DONE: File {} uploaded successfully!!".format(date_h_now, elt))
                    except Exception as e:
                        print("{} ERROR: {}!!! File not uploaded !!!!".format(date_h_now, e))
                        write_in_log("{} ERROR: {}!!! File not uploaded !!!!\n".format(date_h_now, e))
                        email_text +=  "{} FAILED: File \" {} \" failed to upload!!\n      ".format(date_h_now, elt)
                    file.close()
                    session.quit()
    print("{} DONE: Deconnect from FTP !!\n".format(date_h_now))
    write_in_log("{} DONE: Deconnect from FTP !!\n".format(date_h_now))
#######################################################
################# LISTING BACKUP CLIENT ###############
#######################################################
def list_backup():
    global email_text
    global email_subject
    state = False
    session = None
    config_json, loaded = load_json()
    date_now = ""

    day = month = year = 0
    day = int(dt.datetime.now().strftime('%d')) - config_json['day_shift']
    month = int(dt.datetime.now().strftime('%m'))
    year = int(dt.datetime.now().strftime('%Y'))
    
    date_now = date_now_config(month, year, day)
    date_h_now = dt.datetime.now().strftime('%Y-%m-%d')
    for elt in os.listdir(config_json['source']):
        file_time = dt.datetime.fromtimestamp(os.path.getctime(os.path.join(config_json['source'], elt))).strftime('%Y-%m-%d')
        if file_time == date_h_now:
            email_text += "Status des backup du {} : \n\n      ".format(date_now)
            email_subject += "{} - Backup FTP".format(config_json['client'])
            break
        else:
            if email_text==email_subject:
                email_text += "Il n'y a pas de backup {} !\n\n      ".format(date_now)
                email_subject += "{} - Backup FTP".format(config_json['client'])
                break
            elif file_time==0:
                email_text += "Il n'y a pas de backup le {} : \n\n      ".format(date_now)
                email_subject += "{} - Backup FTP".format(config_json['client'])
                break
        
    password_decrypt = False
    password_mail_decrypt = False
    if loaded:
        chemin_principal = config_json['source']
        fernet = Fernet(_KEY_)
        date_h_now = dt.datetime.now().strftime('%Y-%m-%d')
        try:
            password = fernet.decrypt(bytes(config_json['ftp']['password'], 'utf-8'))
            password = password.decode('utf-8')
            password_decrypt = True
            print("{} NOTE: Password successfully decrypt!!".format(date_h_now))
            write_in_log("{} NOTE: Password successfully decrypt!!\n".format(date_h_now))

        except Exception as e:
            print("{} ERROR: {}!!!!!!, Password failed to decrypt!!\n".format(date_h_now, e))
            write_in_log("{} ERROR: {}!!!!!!, Password failed to decrypt!!\n".format(date_h_now, e))

        date_h_now = dt.datetime.now().strftime('%Y-%m-%d')
        try:
            password_mail = fernet.decrypt(bytes(config_json['mail']['password'], 'utf-8'))
            password_mail = password_mail.decode('utf-8')
            password_mail_decrypt = True
            print("{} NOTE: Password for mail user successfully decrypt!!\n".format(date_h_now))
            write_in_log("{} NOTE: Password for mail user successfully decrypt!!\n".format(date_h_now))

        except Exception as e:
            print("{} ERROR: {}!!!!!!, Password for mail user failed to decrypt!!\n".format(date_h_now, e))
            write_in_log("{} ERROR: {}!!!!!!, Password for mail user failed to decrypt!!\n".format(date_h_now, e))

        if password_decrypt and password_mail_decrypt:
            fetch_backup_list(chemin_principal, date_now, password, config_json)                          
            send_email(config_json['mail']['username'], config_json['mail']['recipient'], email_subject, email_text, password_mail)

#######################################################
################# SCRIPT PRINCIPAL ####################
#######################################################
if __name__ == '__main__':
    list_backup()
    write_in_log("\n")

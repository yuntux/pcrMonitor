#!/usr/bin/env python
# -*- coding: utf-8 -*-


from urllib.parse import urlparse, parse_qs
import smtplib

from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import csv
import datetime
import os,time
os.environ['TZ'] = 'Europe/Paris'
time.tzset()

import config


date = datetime.date.today()-datetime.timedelta(1)
date = date.strftime('%Y-%m-%d')
print("=======================", date)

logPath = config.LOG_DIR
fileName = date+'_portailproLog.csv'
filePath = logPath+fileName



##################################### INIT MESSAGE

msg = MIMEMultipart("alternative")
msg["From"] = config.EMAIL_SENDER
msg["To"] = ','.join(config.EMAIL_TO_LIST)

##################################### COMPUTE STATISTICS
nbTotalLignes = 0
codeHTTPErreur = 0
infosNonNul = 0

paths = {}

with open(filePath, newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=config.LOG_CSV_SEPARATOR)
    for row in spamreader:
        path = urlparse(row[2]).path
        if "/pcr-habilitations/v1/habilitations" in path:
            path = "/pcr-habilitations/v1/habilitations"
        if "/pcr-roles/v1/roles/utilisateur" in path:
            path = "/pcr-roles/v1/roles/utilisateur"

        if path not in paths.keys():
            paths[path] = {'nbLignes':0,'codeHTTPErreur':0,'infosNonNul':0}

        paths[path]['nbLignes'] += 1
        nbTotalLignes = nbTotalLignes + 1

        codeHTTP=row[3]
        if codeHTTP[0] in ['4', '5']:
            codeHTTPErreur += 1
            paths[path]['codeHTTPErreur'] += 1

        infos=row[4]
        if infos not in ['None', '[]']:
            infosNonNul += 1
            paths[path]['infosNonNul'] += 1

##################################### FORMAT TEXT MESSAGE

table = ""
print(paths)
for path, p in paths.items():
    table += "<tr><td>"+path+"</td><td>"+str(p["nbLignes"])+"</td><td>"+str(p["codeHTTPErreur"])+"</td><td>"+str(p["infosNonNul"])+"</td></tr>\n"

content = """
<html>
    <body>
        Bonjour,<br>
<br>
        Voici les statistiques cumulées du """+date+""" : <br>
        <ul>
            <li>Nombre total de requêtes logguées : """+str(nbTotalLignes)+""" </li>
            <li> ... dont : Nombre total de requêtes avec un code retour HTTP en erreur (4xx ou 5xx) : """+str(codeHTTPErreur)+""" </li>
            <li>... dont : Nombre total de requêtes dont la balise info est valorisée (API TdB uniquement) : """+str(infosNonNul)+""" </li>
        </ul>
<br>
        <table border="1">
            <thead>
                <tr>
                    <th>Ressource</th>
                    <th>NbLignes</th>
                    <th>Nb erreurs HTTP</th>
                    <th>Nb balise info valorisée</th>
                </tr>
            </thead>
            <tbody>
            """+table+"""
            </tbody>
        </table>

<br>
<br>
        Le détail des requêtes logguées ce jour est en PJ.<br>
<br>
        Par ailleurs, le fichier quotidien est téléchargeable en cours de journée à l'adresse : https://www.dumaine.me/portailproLog/AAAA-MM-JJ_portailproLog.csv<br>
        En remplaçant AAAA-MM-JJ par la date du jour.<br>
<br>
        Cordialement.<br>
        Aurélien DUMAINE
    </body>
</html>
"""
print(content)
html = MIMEText(content, 'html')
msg.attach(html)


msg["Subject"] = "portailproMonitor du "+date+" - "+str(nbTotalLignes)+" requetes - "+str(codeHTTPErreur)+" erreur(s) HTTP - "+str(infosNonNul)+" erreur(s) API"

##################################### JOIN LOG FILE
with open(filePath, 'rb') as fp:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(fp.read())
    encoders.encode_base64(part)
    part.add_header(
            "Content-Disposition",
            "attachment", filename= fileName
    )
    msg.attach(part)

s = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
s.starttls()
s.ehlo()
s.login(config.SMTP_LOGIN, config.SMTP_PASSWORD)
string = msg.as_string()
s.sendmail(config.EMAIL_SENDER, config.EMAIL_TO_LIST, string)
s.quit()


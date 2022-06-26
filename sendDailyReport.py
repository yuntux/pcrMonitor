#!/usr/bin/env python
# -*- coding: utf-8 -*-


import smtplib
from email.message import EmailMessage
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

msg = EmailMessage()
msg["From"] = config.EMAIL_SENDER
msg["To"] = config.EMAIL_TO_LIST

##################################### COMPUTE STATISTICS
nbTotalLignes = 0
codeHTTPErreur = 0
infosNonNul = 0

paths = {}

with open(filePath, newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=config.LOG_CSV_SEPARATOR)
    for row in spamreader:
        path = urlparse(row[2]).path
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
for p in paths:
    table += "<tr><td>"+str(p["nbLignes"])+"</td><td>"+str(p["codeHTTPErreur"])+"</td><td>"+str(p["infosNonNul"])+"</td></tr>\n"

content = """
Bonjour,

Voici les statistiques cumulées du """+date+""" : 
    * Nombre total de requêtes logguées : """+str(nbTotalLignes)+"""
    * ... dont : Nombre total de requêtes avec un code retour HTTP en erreur (4xx ou 5xx) : """+str(codeHTTPErreur)+"""
    * ... dont : Nombre total de requêtes dont la balise info est valorisée (API TdB uniquement) : """+str(infosNonNul)+"""

<table>
    <thead>
        <tr>
            <th>Ressource</th>
            <th>NbLignes</th>
            <th>Nb code retour HTTP en erreur</th>
            <th>Nb balise info valorisée</th>
        </tr>
    </thead>
    <tbody>
    """+table+"""
    </tbody>
</table>


Le détail des requêtes logguées ce jour est en PJ.

Par ailleurs, le fichier quotidien est téléchargeable en cours de journée à l'adresse : https://www.dumaine.me/portailproLog/AAAA-MM-JJ_portailproLog.csv
En remplaçant AAAA-MM-JJ par la date du jour.

Cordialement.
Aurélien DUMAINE
"""
print(content)
msg.set_content(content)


msg["Subject"] = "portailproMonitor du "+date+" - "+str(nbTotalLignes)+" requetes - "+str(codeHTTPErreur)+" erreur(s) HTTP - "+str(infosNonNul)+" erreur(s) API"

##################################### JOIN LOG FILE
with open(filePath, 'rb') as fp:
    data = fp.read()
    msg.add_attachment(data, maintype='application', subtype='csv', filename=fileName)



s = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
s.starttls()
s.ehlo()
s.login(config.SMTP_LOGIN, config.SMTP_PASSWORD)
s.send_message(msg)
s.quit()


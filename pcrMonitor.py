#!/usr/bin/env python
# -*- coding: utf-8 -*-

from portailproLib.portailproLib import client, logger as PortailproLogger

import logging
import sys

import os,time
os.environ['TZ'] = 'Europe/Paris'
time.tzset()

import config

from datetime import datetime
dateJour = datetime.today().strftime('%Y-%m-%d')
#dateJour = '2022-06-01'
print("=======================", dateJour)

logPath = config.LOG_DIR
fileName = logPath+dateJour+'_portailproLog.csv'
if not os.path.exists(fileName):
    with open(fileName, 'w') as f:
        csvHeaders = ['Heure de Paris', 'Login compte portailpro', 'URL de la ressource appelée', 'code retour HTTP', 'balise info', 'nb objets métiers', 'commentaires', 'X-corelation-ID']
        f.write(config.LOG_CSV_SEPARATOR.join(csvHeaders))
        f.write("\n")

logger = PortailproLogger
logger.setLevel(logging.DEBUG)
#handler = logging.StreamHandler(sys.stdout)
handler = logging.FileHandler(fileName)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s;%(message)s', "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)



account = "daf@tasmane.com"
#account = "tatale51@free.fr"
c = client(account, config.ACCOUNT_DICT[account]["password"])
c.connect()
siren= config.ACCOUNT_DICT[account]["sirenList"][0]

print(c.getFederatedAssociations())
print(c.getHabilitationsCompanyList())
print(c.getHabilitationsCompany(siren))
print(c.getRolesCompany(siren))
print(c.getEtablissementsUrssafRG(siren))
print(c.getIndicateursMessagerie(siren))
print(c.getIndicateursCreances(siren))
print(c.getIndicateursDeclarations(siren))
print(c.getDeclarations(siren, 'EN_COURS'))
print(c.getDeclarations(siren, 'TERMINE'))
print(c.getDemandesRemboursement(siren, 'EN_COURS'))
print(c.getDemandesRemboursement(siren, 'TERMINE'))
print(c.getCreances(siren, 'EN_COURS'))
print(c.getCreances(siren, 'TERMINE'))
print(c.getSepaMandates(siren))

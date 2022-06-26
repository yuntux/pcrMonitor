#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime
import sys
import os

import base64
import hashlib
import re
import uuid

import requests
from urllib.parse import urlparse, parse_qs
import secrets

import logging
logger = logging.getLogger(__name__)

import config

class PortailproLog():
    def __init__(self, user, request):
        self.user = user
        self.request = request

    def __str__(self):
        infos = None
        try:
            infos = self.request.json()['infos']
        except :
            pass
        
        nbObjects = None
        try:
            resultat = self.request.json()['resultat']
            if resultat == None :
                nbObjects = 0
            else :
                nbObjects = len(resultat)
        except:
            pass
        

        # les ressources de l'IAM n'ont pas la structure resultat/infos, la charge utile est à la racine du JSON
        try :
            if isinstance(self.request.json(), list):
                nbObjects = len(self.request.json())
        except:
            pass

        comment = None
       
        xCorelationId = None
        try:
            xCorelationId =  self.request.request.headers['X-Correlation-ID']
        except:
            pass
        e = [self.user, self.request.url, self.request.status_code, infos, nbObjects, comment, xCorelationId]
        r = []
        for i in e:
            r.append(str(i).replace(config.LOG_CSV_SEPARATOR, "*"))
        return config.LOG_CSV_SEPARATOR.join(r)


class client:
    def __init__(self, login, password, instance="portailpro.gouv.fr"):
        self.login = login
        self.password = password
        self.instance=instance

    def connect(self):
        state = secrets.token_urlsafe()
        nonce = secrets.token_urlsafe()
        self.xCorrelationID = str(uuid.uuid1())

        client_id = config.PORTAILPRO_OAUTH_CLIENT_ID
        
        code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
        code_verifier = re.sub('[^a-zA-Z0-9]+', '', code_verifier)

        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        code_challenge = code_challenge.replace('=', '')

        payload = {
                    'client_id': client_id,
                    'redirect_uri': 'https://'+self.instance+'/ms/accesspage',
                    'response_type': 'code',
                    'scope' : 'openid internal_login pcr.rattachement',
                    'state' : state,
                    'code_challenge' : code_challenge,
                    'code_challenge_method' : 'S256',
                    'response_mode' : 'query',
                    'nonce' : nonce 
                }

        r = requests.get('https://auth.'+self.instance+'/oauth2/authorize', verify=config.TLS_CERTIFICATE_CHAIN, params=payload)
        sessionDataKey = extractUrlParamValue(r.url, 'sessionDataKey')

        loginform = {
                    'usernameUserInput' : 'tatale51@free.fr',
                    'username' : self.login+'@carbon.super',
                    'password' : self.password,
                    'sessionDataKey' : sessionDataKey,
                }
        r = requests.post('https://auth.'+self.instance+'/commonauth', verify=config.TLS_CERTIFICATE_CHAIN, data=loginform) 

        candidate_state = extractUrlParamValue(r.url, 'state') 
        if not(candidate_state == state):
            print('session state différent', candidate_state, state)
            return False #TODO : plutôt lever une exception

        code = extractUrlParamValue(r.url, 'code')
        

        data = {
                'grant_type' : 'authorization_code',
                'code' : code,
                'client_id' : client_id,
                'redirect_uri' : 'https://'+self.instance+'/ms/accesspage',
                'code_verifier' : code_verifier,
            }
        headers={
                'Authorization' : config.PORTAILPRO_OAUTH_CLIENT_AUTH_HEADER
                }
        r = requests.post('https://auth.'+self.instance+'/oauth2/token', verify=config.TLS_CERTIFICATE_CHAIN, data=data, headers=headers)
        self.oidcTokens = r.json()
        self.idInfo = jwt_payload_decode(self.oidcTokens['id_token'])

    def getAccessToken(self): #TODO ajouter une exception si pas encore défini
        return self.oidcTokens['access_token']

    def getUserSub(self):
        return self.idInfo["sub"]

    def getCommonHeaders(self):
        commonHeaders = {
                'Authorization' : 'Bearer '+self.getAccessToken(),
                'X-Correlation-ID' : self.xCorrelationID
                }
        return commonHeaders

    def getFederatedAssociations(self):
        if not hasattr(self, 'federatedAssociations') :
            r = requests.get('https://auth.'+self.instance+'/api/users/v1/me/federated-associations/', verify=config.TLS_CERTIFICATE_CHAIN, headers=self.getCommonHeaders())
            logger.info(PortailproLog(self.login, r))
            self.federatedAssociations = r.json()
        return self.federatedAssociations

    def getFederatedAssociationParams(self):
        params = {
                'rattachementDgfip' : 'false',
                'rattachementAcoss' : 'false',
                'rattachementDouane' : 'false',
                }
        for fa in self.getFederatedAssociations():
            if fa['idp']['name'] == 'urssaf':
                params['rattachementAcoss'] = 'true'
            if fa['idp']['name'] == 'dgfip':
                params['rattachementDgfip'] = 'true'
            if fa['idp']['name'] == 'dgddi': #TODO : vérifier le code de la DGDDI
                params['rattachementDouane'] = 'true'
        return params

    def getHabilitationsCompanyList(self):
        if not hasattr(self, 'habilitationsCompanyList'):
            params = self.getFederatedAssociationParams()
            params['size'] = 10 #TODO : Gérer la pagination + du cas avec + de 50 SIREN => cette ressource ne retourne aucune liste ?  
            params['page'] = 1
            params['filter'] = 'siren'
            r = requests.get('https://services.'+self.instance+'/pcr-habilitations/v1/habilitations/'+self.getUserSub(), verify=config.TLS_CERTIFICATE_CHAIN, headers=self.getCommonHeaders(), params=params)
            logger.info(PortailproLog(self.login, r))
            self.habilitationsCompanyList = r.json()
        return self.habilitationsCompanyList

    def getHabilitationsCompany(self, siren):
        if not hasattr(self, 'habilitationsCompany'):
            self.habilitationsCompany = {}
        if not (siren in self.habilitationsCompany.keys()):
            params = self.getFederatedAssociationParams()
            r = requests.get('https://services.'+self.instance+'/pcr-habilitations/v1/habilitations/'+self.getUserSub()+'/'+siren, verify=config.TLS_CERTIFICATE_CHAIN, headers=self.getCommonHeaders(), params=params)
            logger.info(PortailproLog(self.login, r))
            self.habilitationsCompany[siren] = r.json()
        return self.habilitationsCompany[siren]

    def getRolesCompany(self, siren):
        if not hasattr(self, 'roleCompany'):
            self.rolesCompany = {}
        if not siren in self.rolesCompany.keys():
            params={'search.siren' : siren}
            r = requests.get('https://services.'+self.instance+'/pcr-roles/v1/roles/utilisateur/'+self.getUserSub(), verify=config.TLS_CERTIFICATE_CHAIN, headers=self.getCommonHeaders(), params=params)
            logger.info(PortailproLog(self.login, r))
            if len(r.text) > 0:
                self.rolesCompany[siren] = r.json()
                return self.rolesCompany[siren]
            return []

    def getEtablissementsUrssafRG(self, siren):
        if not hasattr(self, 'etablissementsUrssafRG'):
            self.etablissementsUrssafRG = {}
        if not siren in self.etablissementsUrssafRG.keys():
            params = self.getFederatedAssociationParams()
            params['siren'] = siren
            r = requests.get('https://services.'+self.instance+'/api-utilitaire-no-business/v1/etablissements', verify=config.TLS_CERTIFICATE_CHAIN, headers=self.getCommonHeaders(), params=params)
            logger.info(PortailproLog(self.login, r))
            self.etablissementsUrssafRG[siren] = r.json()['resultat']
            return self.etablissementsUrssafRG[siren]

    #TODO : manque l'appel pour le bloc TI

    def commonCall(self, url, siren, dictParams={}):
        params = self.getFederatedAssociationParams()
        params['siren'] = siren
        params.update(dictParams)
        r = requests.get(url, verify=config.TLS_CERTIFICATE_CHAIN, headers=self.getCommonHeaders(), params=params)
        logger.info(PortailproLog(self.login, r))
        return r.json()

    def getIndicateursMessagerie(self, siren):
        return self.commonCall('https://services.'+self.instance+'/api-utilitaire-no-business/v1/messagerie/indicateurs', siren)

    def getIndicateursCreances(self, siren):
        return self.commonCall('https://services.'+self.instance+'/api-creance-paiement-pcr/v1/creances/cumuls', siren)

    def getIndicateursDeclarations(self, siren):
        return self.commonCall('https://services.'+self.instance+'/api-declaration-pcr/v1/declarations/tdb', siren)

    def getDeclarations(self, siren, state):
        if state not in ['EN_COURS', 'TERMINE']:
            return "State parameter must be EN_COURS or TERMINE"
        return self.commonCall('https://services.'+self.instance+'/api-declaration-pcr/v1/declarations', siren, {'etat':state})

    def getDemandesRemboursement(self, siren, state):
        if state not in ['EN_COURS', 'TERMINE']:
            return "State parameter must be EN_COURS or TERMINE"
        return self.commonCall('https://services.'+self.instance+'/api-remboursement-pcr/v1/remboursements', siren, {'statut':state})

    def getCreances(self, siren, state):
        if state not in ['EN_COURS', 'TERMINE']:
            return "State parameter must be EN_COURS or TERMINE"
        return self.commonCall('https://services.'+self.instance+'/api-creance-paiement-pcr/v1/creances', siren, {'etat':state})

    def getSepaMandates(self, siren):
        return self.commonCall('https://services.'+self.instance+'/api-mandat-pcr/v1/mandats', siren)

def _b64_decode(data):
    data += '=' * (4 - len(data) % 4)
    return base64.b64decode(data).decode('utf-8')

def jwt_payload_decode(jwt):
    _, payload, _ = jwt.split('.')
    return json.loads(_b64_decode(payload))

def extractUrlParamValue(url, paramKey):
    o = urlparse(url)
    query = parse_qs(o.query)
    if paramKey in query:
        return query[paramKey][0]

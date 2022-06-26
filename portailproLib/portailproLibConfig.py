import os

PORTAILPRO_OAUTH_CLIENT_ID = 'Va3ZplWNIlKE0RhrUCZDoQD_i_Aa'
PORTAILPRO_OAUTH_CLIENT_AUTH_HEADER = 'Basic VmEzWnBsV05JbEtFMFJoclVDWkRvUURfaV9BYTpTQUp4VkVxRDhNVndWaGRkTUdHMm1fT3R6WGth' #concatenation du client_id et d'un autre paramètre propre au client, encodés en base6

TLS_CERTIFICATE_CHAIN = os.path.join(os.path.dirname(__file__),"ca_root+intermediaire.crt")
    #https://whatsmychaincert.com/?portailpro.gouv.fr ==> Supprimer le certif de portailpro (celui en début de fichier) pour ne garder que le root et l'intermédiaire
    #https://levelup.gitconnected.com/solve-the-dreadful-certificate-issues-in-python-requests-module-2020d922c72f

LOG_CSV_SEPARATOR = ";"

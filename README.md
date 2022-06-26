# pcrMonitor

Points d'entrée dans la crontab : 
    MAILTO=""
    */15 * * * * python3 ~/pcrMonitor/pcrMonitor.py
    MAILTO=""
    25 0 * * * python3 ~/pcrMonitor/sendDailyReport.py

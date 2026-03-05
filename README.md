# Bachelor-Project-Database-System
Database system for Bachelor oppgave

## Kommando for å hente database data til lokalt volum
docker compose exec app python exporter.py --CSV

## Kopiere filer fra VPS volum til lokalt
scp user@vps-ip:~/project/my_exports/simulator_data.csv ./Desktop/

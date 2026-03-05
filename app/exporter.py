import argparse
import psycopg2
import csv
import sys

def run_export(format_type):
    conn = psycopg2.connect(host="db", database="mqtt_db", user="user", password="password")
    cur = conn.cursor()
    
    query = """
    SELECT 
        v.session_id, v.event_timestamp, v.event_type, 
        v.payload->>'targetObjectId' as target,
        v.payload->>'action' as action,
        v.telemetry->>'currentScore' as score
    FROM vr_events v
    """
    cur.execute(query)
    rows = cur.fetchall()

    filename = "/exports/simulator_data.csv"
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['Session', 'Time', 'Event', 'Target', 'Action', 'Score'])
        writer.writerows(rows)
    print(f"Export complete: {filename}")

if __name__ == "__main__":
    if "--CSV" in sys.argv:
        run_export("csv")

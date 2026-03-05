import paho.mqtt.client as mqtt
import psycopg2
import json
import os
import time

# Persistent DB Connection
DB_CONF = {
    "host": "db",
    "database": "mqtt_db",
    "user": "user",
    "password": "password"
}

def get_db_connection():
    while True:
        try:
            return psycopg2.connect(**DB_CONF)
        except:
            print("Database not ready, retrying...")
            time.sleep(2)

db_conn = get_db_connection()

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
        
        if msg.topic == "request/points":
            session_id = data.get("sessionId")
            cur = db_conn.cursor()
            cur.execute("SELECT final_score FROM sessions WHERE session_id = %s", (session_id,))
            result = cur.fetchone()
            
            response_topic = f"response/points/{session_id}"
            score = result[0] if result else 0
            client.publish(response_topic, json.dumps({"sessionId": session_id, "score": score}))
            cur.close()
            return 

        header = data.get("header", {})
        session_id = header.get("sessionId")
        timestamp = header.get("timestamp")
        event_type = header.get("eventType")
        
        cur = db_conn.cursor()

        if event_type == "SESSION_START":
            cur.execute("""
                INSERT INTO sessions (session_id, start_time, status) 
                VALUES (%s, %s, 'IN_PROGRESS') ON CONFLICT DO NOTHING;
            """, (session_id, timestamp))

        cur.execute("""
            INSERT INTO vr_events (session_id, event_timestamp, scene_id, event_type, payload, telemetry)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (session_id, timestamp, header.get("sceneId"), event_type, 
              json.dumps(data.get("payload", {})), json.dumps(data.get("telemetry", {}))))

        if event_type == "SESSION_END":
            final_score = data.get("telemetry", {}).get("currentScore", 0)
            cur.execute("""
                UPDATE sessions SET end_time = %s, status = 'COMPLETED', final_score = %s 
                WHERE session_id = %s;
            """, (timestamp, final_score, session_id))

        db_conn.commit()
        cur.close()

    except Exception as e:
        print(f"Error: {e}")
        db_conn.rollback()

client = mqtt.Client()
client.on_message = on_message
client.connect(os.getenv("MQTT_BROKER"), 1883, 60)
client.subscribe([("events/#", 0), ("request/points", 0)])
client.loop_forever()

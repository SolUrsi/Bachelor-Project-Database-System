from paho.mqtt.enums import CallbackAPIVersion
import paho.mqtt.client as mqtt
import psycopg2
import json
import os
import time

DB_CONF = {
    "host": "db",
    "database": "mqtt_db",
    "user": "user",
    "password": "password"
}

db_conn = None

def get_db_connection():
    """Returns a connection; if the global one is dead, it makes a new one."""
    global db_conn
    while True:
        try:
            if db_conn is None or db_conn.closed != 0:
                print("Connecting to database...")
                db_conn = psycopg2.connect(**DB_CONF)
            return db_conn
        except Exception as e:
            print(f"Database not ready ({e}), retrying in 2 seconds...")
            time.sleep(2)

db_conn = get_db_connection()

def on_message(client, userdata, msg):
    conn = get_db_connection()

    try:
        data = json.loads(msg.payload)
        cur = conn.cursor()

        print(f"📥 Received message on topic: {msg.topic}")

        if msg.topic == "request/points":
            session_id = data.get("sessionId")
            print(f"🔍 Fetching points for session: {session_id}")
            cur.execute("SELECT final_score FROM sessions WHERE session_id = %s", (session_id,))
            result = cur.fetchone()

            response_topic = f"response/points/{session_id}"
            score = result[0] if result else 0
            client.publish(response_topic, json.dumps({"sessionId": session_id, "score": score}))
            cur.close()
            print(f"📤 Sent score {score} to {response_topic}")
            return

        header = data.get("header", {})
        session_id = header.get("sessionId")
        timestamp = header.get("timestamp")
        event_type = header.get("eventType")

        print(f"💾 Saving {event_type} for session {session_id}")

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

        conn.commit()
        cur.close()
        print("✅ Database transaction committed.")

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        if conn:
            conn.rollback()

client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION1)
client.on_message = on_message

connected = False
broker_address = os.getenv('MQTT_BROKER')

while not connected:
    try:
        print(f"Attempting to connect to MQTT Broker: {broker_address}...")
        client.connect(broker_address, 1883, 60)
        connected = True
    except Exception as e:
        print(f"MQTT Broker not available ({e}), retrying in 5 seconds...")
        time.sleep(5)

client.subscribe([("events/#", 0), ("request/points", 0)])
print("Subscribed to topics. Starting loop...")
client.loop_forever()                                                                                                                                                                                           106,1       

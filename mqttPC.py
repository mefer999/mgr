import paho.mqtt.client as mqtt 
import time, logging
from db_handlerPC import SQL_handler


broker = "mqtt.eclipseprojects.io"
db = SQL_handler()

def on_connect(client, userdata, flags, rc): #if the connection was successful, subscribing topics
    if rc==0:                                             
        client.connected_flag=True     
        print("connected OK, return code: ", rc)
        client.subscribe("evidence/id")
        client.subscribe("evidence/personFace")
    else:
        print("Bad connection Returned code=",rc)

def on_disconnect(client, userdata, rc): #disconnection info
    logging.info("disconnecting reason  "  +str(rc))
    client.connected_flag=False
    client.disconnect_flag=True
    print("client disconnected ok")

def on_message(client, userdata, message): #message handling
    print("message received " ,str(message.payload.decode("utf-8")))
    if message.topic == "evidence/id": #receiving card ID
        msg = int(float((message.payload.decode("utf-8"))))
        personTup = db.check_idCard('Evidence', str(msg)) #returns data of user or false
        
        if personTup:
            personData = ' '.join(personTup) 
            client.publish("evidence/person", personData) 
        else:
            print("no person")
            client.publish("evidence/person", 0)
    elif message.topic == "evidence/personFace": #receiving name and surname from face recognition
        msg = str(message.payload.decode("utf-8"))
        data = msg.split()
        nameTup = db.check_name('Evidence', data[0], data[1])
        if nameTup:
            nameData = ' '.join(nameTup)
            client.publish("evidence/accept", nameData) 
        else:
            print("no person in db")
            client.publish("evidence/accept", 0)

def on_publish(client, userdata, result):
    print("data published")
    
mqtt.Client.connected_flag = False    
client = mqtt.Client("PC") 
client.on_connect = on_connect 
client.on_disconnect = on_disconnect 
client.on_message = on_message
client.on_publish = on_publish

print("connecting to broker")
try:
    client.connect(broker)
except:
    print("connection failed")
    exit(1)
time.sleep(2)

client.loop_forever()





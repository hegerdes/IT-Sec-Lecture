# Info to P2

## Info P2.1
I tried to capture all exceptions. Even if the server is not running I try 10 times to read the package and then end the MQTT_Dissector. In best case scenario this should be handled before decodeCharString() is called.


## Info P2.2
The dos.py class tries to crash the broker. I build in some delay to avoid overkill because the server thread also sleeps 1 sec.
Depending on the system this delay might have to be changed. But can't test it here. For me 0.5 and 0.25 worked
My MQTT DOS does not call the ```loop()``` function. This saves system resources. But you can call it to make the attack more realistic.
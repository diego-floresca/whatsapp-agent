# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = "AC7ce15c01bbb7f47e78acdd8b6f72f202"
auth_token ="8292cdf35795834e380814e6f604005e"
client = Client(account_sid, auth_token)

call = client.calls.create(
    # Fíjate cómo <prosody> envuelve el texto del código
    twiml='''
    <Response>
        <Say voice="Polly.Mia" language="es-MX">
            Hola. 
            <prosody rate="60%">
                Mucha suerte, te ama tu dieguicatito
            </prosody>
        </Say>
    </Response>
    ''',
    to="+523329559760",
    from_="+16204140329",
)

print(call.sid)
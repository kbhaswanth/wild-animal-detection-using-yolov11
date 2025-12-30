from twilio.rest import Client

ACCOUNT_SID = "ACb6480ba01f5df75da0cc99427a0ed31d"
AUTH_TOKEN = "0fddced93f399c8097b264d8f64e76fc"
TWILIO_NUMBER = "+19793155806"

def send_sms(to_number, message):
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    msg = client.messages.create(
        body=message,
        from_=TWILIO_NUMBER,
        to=to_number
    )
    return msg.sid

import requests
import xml.etree.ElementTree as ET
from userInfo import password_netgsm, username_netgsm

def send_sms(message, send_to):
    url="http://soap.netgsm.com.tr:8080/Sms_webservis/SMS?wsdl"
    #headers = {'content-type': 'application/soap+xml'}
    headers = {'content-type': 'text/xml'}

    message = message.decode('utf-8')

    body = f"""<?xml version="1.0"?>
    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><SOAP-ENV:Body><ns3:smsGonder1NV2 xmlns:ns3="http://sms/"><username>{username_netgsm}</username><password>{password_netgsm}</password><header>Mektup Evi</header><msg>{message}</msg><gsm>{send_to}</gsm><encoding>TR</encoding><filter>0</filter><startdate></startdate><stopdate></stopdate></ns3:smsGonder1NV2></SOAP-ENV:Body></SOAP-ENV:Envelope>"""

    body = body.encode('utf-8')

    response = requests.post(url,data=body,headers=headers)
    root = ET.fromstring(response.content)

    # İstenen öğeyi bulun ve içeriğini alın
    return_element = root.find('.//return')
    value = return_element.text if return_element is not None else None
    if int(value) > 20000:
        print("SMS Gönderimi Başarılı Oldu.")
    else:
        print("SMS Gönderimi Başarısız Oldu. Durum Kodu: " + value)
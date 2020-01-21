import json
import requests

NUTANIX_VIP = '10.149.11.41'

def handle_pd():
  session = requests.Session()
  session.auth = ('admin', 'Nutanix/4u!')
  session.verify = False                              
  session.headers.update({'Content-Type': 'application/json; charset=utf-8'})
  url = f'https://{NUTANIX_VIP}:9440/PrismGateway/services/rest/v2.0/protection_domains/'
  response = session.get(url)
  text = json.dumps(response.json(), indent=2)
  print(text)
  with open('api_pd.json', 'w') as fout:
    fout.write(text)

if __name__ == '__main__':
  handle_pd()

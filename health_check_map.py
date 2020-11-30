import sys
import redfish
import json

# Main Uri addresses
ROOT_URI = '/redfish/v1/'
ILOSYS_URI = '/redfish/v1/systems/1'
IDRACSYS_URI = '/redfish/v1/Systems/System.Embedded.1'
# HP Resource URI
RESOURCE_URI = '/redfish/v1/ResourceDirectory/'

# Populate server list
def parse_json(filename):  # Parses the JSON data from a file, populates a Python dict with the data and returns it.
    print('Loading', filename)
    try:
        with open(filename) as jsonFile:
            data = json.load(jsonFile)
            return data
    except Exception as e:
            print('Unable to load json')
            print(e)

            

def open_connection(systemUrl, loginAccount, loginPassword):
    ''' Open a https session using redfish to a target server.
    If the connection is not established, either the server is down or redfish
    is not supported.    

    Input: server address, user account and password
    Output: returns an object with the open session'''
    
    try:
        serverConnection = redfish.RedfishClient(base_url=systemUrl, username=loginAccount,
                                      password=loginPassword)
        serverConnection.login()
        serverInfo = serverConnection.get(ROOT_URI).dict
        if 'Hp' in serverInfo['Oem'] or 'Hpe' in serverInfo['Oem']:
            serverInfo = serverConnection.get(ILOSYS_URI).dict
            serverType = 'HP'
        elif 'Dell' in serverInfo['Oem']:
            serverInfo = serverConnection.get(IDRACSYS_URI).dict
            serverType = 'Dell'
        else:
            print('Unknown server')
            serverConnection.logout()
            sys.exit()
        print('Connected to', serverInfo['HostName'], 'Vendor:', serverType)
    except redfish.ServerDownOrUnreachableError:
        sys.stderr.write("ERROR: server not reachable or doesn't support Redfish.\n")
        sys.exit()
    return (serverConnection, serverType)


def parse_uri(serverConnection, uri):
    serverObj = serverConnection.get(uri).dict
    print('Parsing uri:', uri)
    return serverObj

def ilo_item_generator(ilo_data, lookup_key='@odata.id'):
    if isinstance(ilo_data, dict):
        for k, v in ilo_data.items():
            if k == lookup_key:
                yield v
            else:
                yield from ilo_item_generator(v, lookup_key)
    elif isinstance(ilo_data, list):
        for item in ilo_data:
            yield from ilo_item_generator(item, lookup_key)

def map_idrac(serverConnection, idracData, uriList=[]):
    lookup = '@odata.id'
    if isinstance(idracData, dict):
        if lookup in idracData and idracData[lookup] not in uriList:
            uriList.append(idracData[lookup])
            uri = parse_uri(serverConnection, idracData[lookup])
            map_idrac(serverConnection, uri, uriList)
       
        for key, value in idracData.items():
            if isinstance(value, list) or isinstance(value, dict):
                map_idrac(serverConnection, value, uriList)
   
    elif isinstance(idracData, list):
        for element in idracData:
            if isinstance(element, list) or isinstance(element, dict):
                map_idrac(serverConnection, element, uriList)
   
    return uriList

def find_status(serverData):
    lookup = 'Status'
    if isinstance(serverData, dict):
        if lookup in serverData:
            return True
       
        for key, value in serverData.items():
            if isinstance(value, list) or isinstance(value, dict):
                find_status(value)
   
    elif isinstance(serverData, list):
        for element in serverData:
            if isinstance(element, list) or isinstance(element, dict):
                find_status(element)
   
    return False

def build_hc_uris(serversFile):
    serversDict = parse_json(serversFile)
    
    for serverInfo in serversDict:
        
        print('Mapping Healthcheck uris for', serverInfo)
        serverConnection, serverType = open_connection(**serversDict[serverInfo])
        
        hcUris = []
        
        if serverType == 'HP':
            resourceUris = serverConnection.get(RESOURCE_URI).dict
            uriList = list(ilo_item_generator(resourceUris))
            
        elif serverType == 'Dell':
            idracData = serverConnection.get(ROOT_URI).dict
            uriList = map_idrac(serverConnection, idracData)
            
        print('Filtering health status uris.')
        for uri in uriList:
            uriData = parse_uri(serverConnection, uri)
            if find_status(uriData):
                hcUris.append(uri)
        
        print('Adding health status uri list to', serverInfo)        
        serversDict[serverInfo]['HC_uris'] = hcUris
        print('Done!')
        serverConnection.logout()
    
    print('Creating server data json file...')
    with open('serverData.json', 'w') as outfile:
        json.dump(serversDict, outfile)
    print('Finished...')

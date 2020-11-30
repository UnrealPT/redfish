import sys
import redfish
import json
import datetime

# Main Uri addresses
ROOT_URI = '/redfish/v1/'
ILOSYS_URI = '/redfish/v1/systems/1'
IDRACSYS_URI = '/redfish/v1/Systems/System.Embedded.1'
ILOMAN_URI = '/redfish/v1/managers/1'
IDRACMAN_URI = '/redfish/v1/Managers/iDRAC.Embedded.1'

# HP ONLY Resource URI
RESOURCE_URI = '/redfish/v1/ResourceDirectory/'


# Create time stamp
dateStamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

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

servers = parse_json('serverData.json')           

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
    return (serverConnection, serverInfo['HostName'], serverType)

def parse_uri(serverConnection, uri):
    serverObj = serverConnection.get(uri).dict
    print('Parsing uri:', uri)
    return serverObj

def build_healthcheck(serverConnection, serverName, serverType, hcUris):
    
    def get_uridata(serverConnection, hcUris):
        uridata = {}
        print('Populating uri data')
        for uri in hcUris:
            serverObj = serverConnection.get(uri).dict
            try:
                uridata[serverObj['@odata.type']] = serverObj
            except KeyError:
                print(serverObj)
        return uridata
    
    def get_status(serverConnection, uriData, healthcheck={}, urisVisited=[]):
        
        lookup = 'Status'

        uriAddress = '@odata.id'
        if isinstance(uriData, dict):
            if lookup in uriData:
                try:                        
                    healthcheck[uriData['@odata.id']] = uriData['Status']
                except (TypeError, KeyError):
                    try:
                        healthcheck[uriData['Name']] = uriData['Status']
                    except (KeyError, TypeError) as e:
                        print(e)
            elif uriAddress in uriData and uriData[uriAddress] not in urisVisited:
                urisVisited.append(uriData[uriAddress])
                uriParsed = parse_uri(serverConnection, uriData[uriAddress])
                get_status(serverConnection, uriParsed, healthcheck, urisVisited)
       
            for key, value in uriData.items():
                if isinstance(value, list) or isinstance(value, dict):
                    get_status(serverConnection, value, healthcheck, urisVisited)
   
        elif isinstance(uriData, list):
            for element in uriData:
                if isinstance(element, list) or isinstance(element, dict):
                    get_status(serverConnection, element, healthcheck, urisVisited)
                    
   
        return healthcheck
    
    print('Building Healthcheck for', serverName)
    serverHC = {}
    
    serverHC['Hostname'] = serverName
    serverHC['Vendor'] = serverType
    serverHC['Date'] = dateStamp
    
    if serverType == 'HP':
        HPdiagnostics = {}
        serverObj = serverConnection.get(ILOMAN_URI).dict
        serverHC['FwVersion'] = serverObj['FirmwareVersion']
        try:
            selfTestLst = serverObj['Oem']['Hp']['iLOSelfTestResults']

        except KeyError:
            selfTestLst = serverObj['Oem']['Hpe']['iLOSelfTestResults']
        for test in range(len(selfTestLst)):
            if selfTestLst[test]['Status'] == 'Informational':
                continue
            HPdiagnostics[selfTestLst[test]['SelfTestName']] = selfTestLst[test]['Status']
            
    elif serverType == 'Dell':
        serverObj = serverConnection.get(IDRACMAN_URI).dict
        serverHC['FwVersion'] = serverObj['FirmwareVersion']
    
    
    
    uriData = get_uridata(serverConnection, hcUris)
    serverHC['Healthcheck'] = get_status(serverConnection, uriData)
    if serverType == 'HP':
        serverHC['Healthcheck'].update(HPdiagnostics)
    
    return serverHC

    
    
def create_hcfiles():
    for server in serverData:
        serverConnection, serverName, serverType = open_connection(**serverData[server])
        hcUris = serverData[server]['HC_uris']
        serverHc = build_healthcheck(serverConnection, serverName, serverType, hcUris):
        print('Creating healtcheck file...')
        with open('hc dump/{}.json'.format(server), 'w') as hcFile:
            json.dump(serverHc, hcFile)
        print('File {}.json created successfully'.format(server))
        serverConnection.logout()
        
        
        
        
        
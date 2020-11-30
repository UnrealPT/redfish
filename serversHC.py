import sys
import redfish
import json
import datetime
import ilo5HC
import ilo4HC
import idracHC

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

servers = parse_json('servers.json')           

def open_connection(systemUrl, loginAccount, loginPassword):
    ''' Open a https session using redfish to a target server.
    If the connection is not established, either the server is down or redfish
    is not supported.    

    Input: server address, user account and password
    Output: returns a tupple with the open session, server name and server type'''
    
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
    return (serverConnection, serverInfo['HostName'], systemUrl, serverType)

def build_healthcheck(serverConnection, serverName, serverAddress, serverType):
    ''' This function builds a dictionary with the hostname and health status
    of the server.
    The dictionary contains bios, hardware and self test diagnostics.
    Most of the info is in nested dictionaries and lists, so I used iterations
    to structure the data in to a simple dictionary.
    
    Input: tuple with redfish connection, server name and server type.
    Output: dictionary with the hostname and health status of the server'''
    
    serverHC = {}
    
    # Server name
    serverHC['Hostname'] = serverName
    serverHC['Host address'] = serverAddress
    serverHC['Date'] = dateStamp
    
    # Server type and version
    if serverType == 'HP':
        serverObj = serverConnection.get(ILOMAN_URI).dict
        serverHC['FwVersion'] = serverObj['FirmwareVersion']
        if serverHC['FwVersion'].split()[1] == '5':
            healthcheck = ilo5HC.build_healthcheck(serverConnection)
        elif serverHC['FwVersion'].split()[1] == '4':
            healthcheck = ilo4HC.build_healthcheck(serverConnection)
        else:
            print('ILO version: ' + serverHC['FwVersion'], 'Unable to build healthcheck' )
            
    elif serverType == 'Dell':
        serverObj = serverConnection.get(IDRACMAN_URI).dict
        serverHC['FwVersion'] = serverObj['FirmwareVersion']
        healthcheck = idracHC.build_healthcheck(serverConnection)

    print('Version:', serverHC['FwVersion'])
    
    serverHC['Healthcheck'] = healthcheck

    return serverHC

def create_hcfiles():
    ''''This function will iterate the servers dict and connect to each server.
    Depending on the type of server (HP or Dell) a connection will be opened and a healthcheck wil be performed
    '''
    for server in servers:
        serverConnection, serverName, serverAddress, serverType = open_connection(**servers[server])
        serverHC = build_healthcheck(serverConnection, serverName, serverAddress, serverType)
        print('Dumping healtcheck to file...')
        with open('hc dump/{}.json'.format(server), 'w') as hcFile:
            json.dump(serverHC, hcFile)
        print('File {}.json created successfully'.format(server))
        serverConnection.logout()
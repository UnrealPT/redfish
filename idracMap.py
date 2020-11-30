import sys
import redfish

# Main uri addresses
ROOT_URI = '/redfish/v1/'
SYSTEMS_URI = '/redfish/v1/Systems/System.Embedded.1'

def open_connection(systemUrl, loginAccount, loginPassword):
    ''' Open a https session using redfish to a target idrac.
    If the connection is not established, either the server is down or redfish
    is not supported.    

    Input: IDRAC address, user account and password
    Output: returns an object with the open session'''
    
    try:
        idracConnection = redfish.RedfishClient(base_url=systemUrl, username=loginAccount,
                                      password=loginPassword)
        idracConnection.login()
        idracInfo = idracConnection.get(SYSTEMS_URI)
        print('Connected to', idracInfo.dict['HostName'])
    except redfish.ServerDownOrUnreachableError:
        sys.stderr.write("ERROR: server not reachable or doesn't support Redfish.\n")
        sys.exit()
    return idracConnection

def parse_uri(uri):
    idracObj = idrac.get(uri)
    return idracObj.dict

def map_idrac(idracData, uriList=[]):
    lookup = '@odata.id'
    if isinstance(idracData, dict):
        if lookup in idracData and idracData[lookup] not in uriList:
            uriList.append(idracData[lookup])
            uri = parse_uri(idracData[lookup])
            map_idrac(uri, uriList)
       
        for key, value in idracData.items():
            if isinstance(value, list) or isinstance(value, dict):
                map_idrac(value, uriList)
   
    elif isinstance(idracData, list):
        for element in idracData:
            if isinstance(element, list) or isinstance(element, dict):
                map_idrac(element, uriList)
   
    return uriList

               
def find_status(idracData):
    lookup = 'Status'
    if isinstance(idracData, dict):
        if lookup in idracData:
            return True
       
        for key, value in idracData.items():
            if isinstance(value, list) or isinstance(value, dict):
                find_status(value)
   
    elif isinstance(idracData, list):
        for element in idracData:
            if isinstance(element, list) or isinstance(element, dict):
                find_status(element)
   
    return False
    
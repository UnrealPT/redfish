import sys
import redfish

# Main Uri addresses
SYSTEMS_URI = '/redfish/v1/Systems/System.Embedded.1'
CHASSIS_URI = '/redfish/v1/Chassis/System.Embedded.1'
THERMAL_URI = '/redfish/v1/Chassis/System.Embedded.1/Thermal'
MEMORY_URI = '/redfish/v1/Systems/System.Embedded.1/Memory'
PROCESSORS_URI = '/redfish/v1/Systems/System.Embedded.1/Processors'
STORAGE_URI = '/redfish/v1/Systems/System.Embedded.1/Storage'
NETWORK_URI = '/redfish/v1/Systems/System.Embedded.1/NetworkAdapters'
ETHIF_URI = '/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces'


def build_healthcheck(idrac):
    ''' This function builds a dictionary with the hostname and health status
    of the idrac. (IDRAC 7)
    The dictionary contains bios, hardware and self test diagnostics.
    Most of the info is in nested dictionaries and lists, so I used iterations
    to structure the data into a simple dictionary.
    
    Input: redfish object with the idrac connection.
    Output: dictionary with the hostname and health status of the idrac'''
    
    idracHealth = {}
    
    # Chassis health
    print('Checking chassis...')
    idracObj = idrac.get(CHASSIS_URI)
    idracHealth['Chassis'] = idracObj.dict['Status']['Health']
    
    # Power supplies
    print('Checking power supplies')
    idracObj = idrac.get(SYSTEMS_URI)
    psuList = idracObj.dict['Links']['PoweredBy']
    psuCheck = []
    for psu in psuList:
        for psu_uri in psu.values():
            idracObj = idrac.get(psu_uri)
            if idracObj.dict['Status']['Health'] != 'OK':
                psuCheck.append(idracObj['Name'])
    if len(psuCheck) > 0:
        idracHealth['Power supplies'] = 'Nok, check PSU: ' + ', '.join(psuCheck)
    else:
        idracHealth['Power supplies'] = 'OK'
        
    # System health
    print('Checking system...')
    idracObj = idrac.get(SYSTEMS_URI)
    idracHealth['System'] = idracObj.dict['Status']['Health']
    
    # Fan health
    print('Checking fans...')
    idracObj = idrac.get(SYSTEMS_URI)
    fanList = idracObj.dict['Links']['CooledBy']
    fanCheck = []
    for fan in fanList:
        for fan_uri in fan.values():
            idracObj = idrac.get(fan_uri)
            if idracObj.dict['Status']['Health'] != 'OK':
                    fanCheck.append(idracObj.dict['FanName'])
    if len(fanCheck) > 0:
        idracHealth['Fans'] = 'Nok, check fans: ' + ', '.join(fanCheck)
    else:
        idracHealth['Fans'] = 'OK'   
        
    # Temperatures
    print('Checking temperatures...')
    idracObj = idrac.get(THERMAL_URI)
    tempList = idracObj.dict['Temperatures']
    tempCheck = []
    for element in tempList:
        try:
            if element['Status']['Health'] != 'OK':
                tempCheck.append(element['Name'])
        except KeyError:
            continue
    if len(tempCheck) > 0:
        idracHealth['Temperatures'] = 'Nok, check temperature: ' + ', '.join(tempCheck)
    else:
        idracHealth['Temperatures'] = 'OK'
    
    # Memory health
    print('Checking memory...')
    idracObj = idrac.get(MEMORY_URI)
    memList = idracObj.dict['Members']
    memCheck = []
    for mem in memList:
        for mem_uri in mem.values():
            idracObj = idrac.get(mem_uri)
            if idracObj.dict['Status']['Health'] != 'OK':
                memCheck.append(idrac.dict['Name'])
    if len(memCheck) > 0:
        idracHealth['Memory'] = 'Nok, check mems: ' + ', '.join(memCheck)
    else:
        idracHealth['Memory'] = 'OK'
    
    # Cpu Health
    print('Checking processors...')
    idracObj = idrac.get(PROCESSORS_URI)
    cpuList = idracObj.dict['Members']
    cpuCheck = []
    for cpu in cpuList:
        for cpu_uri in cpu.values():
            idracObj = idrac.get(cpu_uri)
            if idracObj.dict['Status']['Health'] != 'OK':
                cpuCheck.append(idracObj.dict['Name'])
    if len(cpuCheck) > 0:
        idracHealth['Processors'] = 'Nok, check cpu: ' + ', '.join(cpuCheck)
    else:
        idracHealth['Processors'] = 'OK'
    
    # Storage health
    print('Checking storage...')
    # Array Controllers
    idracObj = idrac.get(STORAGE_URI)
    arrayList = idracObj.dict['Members']
    arrayCheck = []
    diskCheck = []
    enclosureCheck = []
    volumeCheck = []
    for array in arrayList:
        for array_uri in array.values():
            idracObj = idrac.get(array_uri)
            if idracObj.dict['Status']['Health'] != 'OK':
                arrayCheck.append(idracObj['Name'])
            # Physical disks
            diskList = idracObj.dict['Drives']
            for disk in diskList:
                for disk_uri in disk.values():
                    idracObj = idrac.get(disk_uri)
                    if idracObj.dict['Status']['Health'] != 'OK':
                        diskCheck.append(idracObj.dict['Name'])
            # Enclosures
            idracObj = idrac.get(array_uri)
            enclosureList = idracObj.dict['Links']['Enclosures']
            for enclosure in enclosureList:
                for enclosure_uri in enclosure.values():
                    if 'Enclosure' not in enclosure_uri:
                        continue
                    else:
                        idracObj = idrac.get(enclosure_uri)
                        if idracObj.dict['Status']['Health'] != 'OK':
                            enclosureCheck.append(idracObj.dict['Name'])
            # Virtual disks
            idracObj = idrac.get(array_uri + '/Volumes')
            volumeList = idracObj.dict['Members']
            for volume in volumeList:
                for volume_uri in volume.values():
                    idracObj = idrac.get(volume_uri)
                    if idracObj.dict['Status']['Health'] != 'OK':
                        volumeCheck.append(idracObj.dict['Name'])
    if len(arrayCheck) > 0:
        idracHealth['Array Controller'] = 'Nok, check array controller: ' + ', '.join(arrayCheck)
    else:
        idracHealth['Array Controller'] = 'OK'
    if len(volumeCheck) > 0:
        idracHealth['Virtual Disks'] = 'Nok, check logical disk: ' + ', '.join(volumeCheck)
    else:
        idracHealth['Virtual Disks'] = 'OK'
    if len(diskCheck) > 0:
        idracHealth['Disk drives'] = 'Nok, check disk drive: ' + ', '.join(diskCheck)
    else:
        idracHealth['Disk drives'] = 'OK'
    if len(enclosureCheck) > 0:
        idracHealth['Storage Enclosure'] = 'Nok, check enclosure: ' + ', '.join(enclosureCheck)
    else:
        idracHealth['Storage Enclosure'] = 'OK'
        
    # Network
    print('Checking network...')
    idracObj = idrac.get(NETWORK_URI)
    adapterList = idracObj.dict['Members']
    adapterCheck = []
    netdeviceCheck = []
    netportCheck = []
    # Network adpaters/interfaces
    for adapter in adapterList:
        for adapter_uri in adapter.values():
            idracObj = idrac.get(adapter_uri)
            if idracObj.dict['Status']['State'] != 'Enabled':
                adapterCheck.append(idracObj.dict['Id'])
            # Network device functions
            idracObj = idrac.get(adapter_uri + '/NetworkDeviceFunctions')
            netdeviceList = idracObj.dict['Members']
            for netdevice in netdeviceList:
                for device_uri in netdevice.values():
                    idracObj = idrac.get(device_uri)
                    if idracObj.dict['Status']['State'] != 'Enabled':
                        netdeviceCheck.append(idracObj.dict['Id'])
            # Network ports
            idracObj = idrac.get(adapter_uri + '/NetworkPorts')
            netportList = idracObj.dict['Members']
            for netport in netportList:
                for netport_uri in netport.values():
                    idracObj = idrac.get(netport_uri)
                    if idracObj.dict['Status']['State'] != 'Enabled':
                        netportCheck.append(idracObj.dict['Id'])
    if len(adapterCheck) > 0:
         idracHealth['Network adapters'] = 'Nok, check adapter: ' + ', '.join(adapterCheck)
    else:
        idracHealth['Network adapters'] = 'OK'
    if len(netdeviceCheck) > 0:
         idracHealth['Network device function'] = 'Nok, check network device function: ' + ', '.join(netdeviceCheck)
    else:
        idracHealth['Network device function'] = 'OK'
    if len(netportCheck) > 0:
         idracHealth['Network ports'] = 'Nok, check network port: ' + ', '.join(netportCheck)
    else:
        idracHealth['Network ports'] = 'OK'
                        
    print('Healthcheck successful!')
    return idracHealth        
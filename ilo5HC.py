# Main Uri addresses
SYSTEMS_URI = '/redfish/v1/systems/1'
MANAGERS_URI = '/redfish/v1/managers/1'
CHASSIS_URI = '/redfish/v1/Chassis/1'
DEVICES_URI = '/redfish/v1/Chassis/1/Devices/'
PROCESSORS_URI = '/redfish/v1/Systems/1/Processors'
MEMORY_URI = '/redfish/v1/Systems/1/Memory'
POWER_URI = '/redfish/v1/Chassis/1/Power'
SSTORAGE_URI = '/redfish/v1/Systems/1/SmartStorage'
ARRAY_URI = '/redfish/v1/Systems/1/SmartStorage/ArrayControllers'
THERMAL_URI = '/redfish/v1/Chassis/1/Thermal'
EMBMEDIA_URI = '/redfish/v1/Managers/1/EmbeddedMedia'
NETWORK_URI = '/redfish/v1/Systems/1/BaseNetworkAdapters/'
ETHIF_URI = '/redfish/v1/Systems/1/EthernetInterfaces'


def build_healthcheck(ilo):
    ''' This function builds a dictionary with the hostname and health status
    of the ilo. (ILO 5)
    The dictionary contains bios, hardware and self test diagnostics.
    Most of the info is in nested dictionaries and lists, so I used iterations
    to structure the data into a simple dictionary.
    
    Input: redfish object with the ilo connection.
    Output: dictionary with the hostname and health status of the ilo'''
    
    iloHealth = {}
    
    # Chassis health
    print('Checking chassis...')
    iloObj = ilo.get(CHASSIS_URI)
    iloHealth['Chassis'] = iloObj.dict['Status']['Health']
    # Devices
    print('Checking devices...')
    iloObj = ilo.get(DEVICES_URI)
    deviceList = iloObj.dict['Members']
    deviceCheck = []
    for device in deviceList:
        for device_uri in device.values():
            iloObj = ilo.get(device_uri)
            try:
                if iloObj.dict['Status']['Health'] != 'OK' and iloObj.dict['Status']['State'] != 'Absent':
                    deviceCheck.append(iloObj.dict['Name'])
            except KeyError:
                continue
    if len(deviceCheck) > 0:
        iloHealth['Device inventory'] = 'Nok, check device: ' + ', '.join(deviceCheck)
    else:
        iloHealth['Device inventory'] = 'OK'
            
    
    # System health
    print('Checking devices...')
    iloObj = ilo.get(SYSTEMS_URI)
    iloHealth['System'] = iloObj.dict['Status']['Health']
    # Bios health
    iloHealth['Bios'] = iloObj.dict['Oem']['Hpe']['AggregateHealthStatus']['BiosOrHardwareHealth']['Status']['Health']
    
    # Fan health
    print('Checking fans...')
    iloObj = ilo.get(THERMAL_URI)
    fanList = iloObj.dict['Fans']
    fanCheck = []
    for fan in fanList:
        if fan['Status']['Health'] != 'OK':
            fanCheck.append(fan['FanName'])
    if len(fanCheck) > 0:
        iloHealth['Fans'] = 'Nok, check fans: ' + ', '.join(fanCheck)
    else:
        iloHealth['Fans'] = 'OK'
    
    # Temperatures
    print('Checking temperatures...')
    iloObj = ilo.get(THERMAL_URI)
    tempList = iloObj.dict['Temperatures']
    tempCheck = []
    for element in tempList:
        try:
            if element['Status']['Health'] != 'OK':
                tempCheck.append(element['Name'])
        except KeyError:
            continue
    if len(tempCheck) > 0:
        iloHealth['Temperatures'] = 'Nok, check temperature: ' + ', '.join(tempCheck)
    else:
        iloHealth['Temperatures'] = 'OK'
    
    # Memory health
    print('Checing memory...')
    iloObj = ilo.get(MEMORY_URI)
    memList = iloObj.dict['Members']
    memCheck = []
    for mem in memList:
        for mem_uri in mem.values():
            iloObj = ilo.get(mem_uri)
            if iloObj.dict['Status']['Health'] != 'OK':
                memCheck.append(iloObj.dict['Name'])
    if len(memCheck) > 0:
        iloHealth['Memory'] = 'Nok, check mems: ' + ', '.join(memCheck)
    else:
        iloHealth['Memory'] = 'OK'
        
    # Cpu Health
    print('Checking processors...')
    iloObj = ilo.get(PROCESSORS_URI)
    cpuList = iloObj.dict['Members']
    cpuCheck = []
    for cpu in cpuList:
        for cpu_uri in cpu.values():
            iloObj = ilo.get(cpu_uri)
            if iloObj.dict['Status']['Health'] != 'OK':
                cpuCheck.append(iloObj.dict['Id'])
    if len(cpuCheck) > 0:
        iloHealth['Processors'] = 'Nok, check cpu: ' + ', '.join(cpuCheck)
    else:
        iloHealth['Processors'] = 'OK'
        
    # Smartstorage health
    print('Checking storage...')
    iloObj = ilo.get(SSTORAGE_URI)
    iloHealth['Smart Storage'] = iloObj.dict['Status']['Health']
    # Battery 
    iloObj = ilo.get(SYSTEMS_URI)
    try:
        iloHealth['Smart Storage Battery'] = iloObj.dict['Oem']['Hp']['Battery'][0]['Condition']
    except KeyError:
        iloHealth['Smart Storage Battery'] = 'Absent'
    # Array
    iloObj = ilo.get(ARRAY_URI)
    try:
        arrayList = iloObj.dict['Members']
        arrayCheck = []
        logicalCheck = []
        diskCheck = []
        enclosureCheck = []
        for array in arrayList:
            for uri in array.values():
                iloObj = ilo.get(uri)
                if iloObj.dict['Status']['Health'] != 'OK':
                    arrayCheck.append(iloObj.dict['Id'])
                # Logical drives
                iloObj = ilo.get(uri + '/LogicalDrives')
                logicalList = iloObj.dict['Members']
                for drive in logicalList:
                    for drive_uri in drive.values():
                        iloObj = ilo.get(drive_uri)
                        if iloObj.dict['Status']['Health'] != 'OK':
                            logicalCheck.append(iloObj.dict['Id'])
                # Disk Drives
                iloObj = ilo.get(uri + '/DiskDrives')
                diskList = iloObj.dict['Members']
                for disk in diskList:
                    for disk_uri in disk.values():
                        iloObj = ilo.get(disk_uri)
                        if iloObj.dict['Status']['Health'] != 'OK':
                            diskCheck.append(iloObj.dict['Id'])  
                # Enclosures
                iloObj = ilo.get(uri + '/StorageEnclosures')
                enclosureList = iloObj.dict['Members']
                for enclosure in enclosureList:
                    for enclosure_uri in enclosure.values():
                        iloObj = ilo.get(enclosure_uri)
                        if iloObj.dict['Status']['Health'] != 'OK':
                            enclosureCheck.append(iloObj.dict['Id'])
                    
        if len(arrayCheck) > 0:
            iloHealth['Array Controller'] = 'Nok, check array controller: ' + ', '.join(arrayCheck)
        else:
            iloHealth['Array Controller'] = 'OK'
        if len(logicalCheck) > 0:
            iloHealth['Logical Disks'] = 'Nok, check logical disk: ' + ', '.join(logicalCheck)
        else:
            iloHealth['Logical Disks'] = 'OK'
        if len(diskCheck) > 0:
            iloHealth['Disk drives'] = 'Nok, check disk drive: ' + ', '.join(diskCheck)
        else:
            iloHealth['Disk drives'] = 'OK'
        if len(enclosureCheck) > 0:
            iloHealth['Storage Enclosure'] = 'Nok, check enclosure: ' + ', '.join(enclosureCheck)
        else:
            iloHealth['Storage Enclosure'] = 'OK'
    except KeyError:
        iloHealth['Storage Array'] = 'Absent'
    
    # Network adapters
    print('Checking network...')
    iloObj = ilo.get(NETWORK_URI)
    adapterList = iloObj.dict['Members']
    adapterCheck = []
    portCheck = []
    for adapter in adapterList:
        for adapter_uri in adapter.values():
            iloObj = ilo.get(adapter_uri)
            if iloObj.dict['Status']['Health'] != 'OK':
                adapterCheck.append(iloObj.dict['Name'])
            # Network ports
            portList = iloObj.dict['PhysicalPorts']
            for port in portList:
                try:
                    if port['Status']['Health'] != 'OK':
                        portCheck.append(port['Name'])
                except KeyError:
                    continue
    if len(adapterCheck) > 0:
        iloHealth['Network adapters'] = 'Nok, check network adapter: ' + ', '.join(enclosureCheck)
    else:
        iloHealth['Network adapters'] = 'OK'
    if len(portCheck) > 0:
        iloHealth['Physical ports'] = 'Nok, check physical port: ' + ', '.join(portCheck)
    # Ethernet interfaces
    print('Checking ethernet interfaces...')
    iloObj = ilo.get(ETHIF_URI)
    ethList = iloObj.dict['Members']
    ethCheck = []
    for interface in ethList:
        for interface_uri in interface.values():
            iloObj = ilo.get(interface_uri)
            try:
                if iloObj.dict['Status']['Health'] != 'OK':
                    ethCheck.append(iloObj.dict['Id'])
            except KeyError:
                continue
            except TypeError:
                continue
    if len(ethCheck) > 0:
        iloHealth['Ethernet interfaces'] = 'Nok, check ethernet interface: ' + ', '.join(ethCheck)
    else:
        iloHealth['Ethernet interfaces'] = 'OK'
    
    # Embedded Media
    print('Checking embedded media...')
    iloObj = ilo.get(EMBMEDIA_URI)
    iloHealth['Embedded Media controller'] = iloObj.dict['Controller']['Status']['Health']
    
    # Self test status eg. NVRAM, EEMPROM
    print('Checking self test diagnostics...')
    iloObj = ilo.get(MANAGERS_URI)
    selfTestLst = iloObj.dict['Oem']['Hpe']['iLOSelfTestResults']
    for test in range(len(selfTestLst)):
        if selfTestLst[test]['Status'] == 'Informational':
            continue
        iloHealth[selfTestLst[test]['SelfTestName']] = selfTestLst[test]['Status']
    
    print('Healthcheck sucessfull!')
    return iloHealth

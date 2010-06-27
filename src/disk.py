import win32file
import win32con
import win32api
import winioctlcon
import struct
import logging

# This file is a Python translation of the file disk.c
# from 'usb-creator' (https://launchpad.net/usb-creator)

STATUS_WRITING = 0

def getPhysicalDeviceID(device):
    devicename = "\\\\.\\%c:" % (ord('A') + device,)
    hFile = win32file.CreateFile(devicename, 0, 0, None, win32con.OPEN_EXISTING, 0, None)
    if hFile != win32file.INVALID_HANDLE_VALUE:
        pass
    buffer = win32file.DeviceIoControl(hFile, winioctlcon.IOCTL_STORAGE_GET_DEVICE_NUMBER, None, 12)
    tup = struct.unpack("iLL", buffer)
    win32file.CloseHandle(hFile)
    return tup[1]

def getHandleOnFile(location, access):
    location = "\\\\.\\%s" % (location,)
    if access == win32con.GENERIC_READ:
        flags = win32con.OPEN_EXISTING
    else:
        flags = win32con.CREATE_ALWAYS
    return win32file.CreateFile(location, access, 0, None, flags, 0, None)

def getHandleOnDevice(device, access):
    devicename = "\\\\.\\PhysicalDrive%d" % (device,)
    hDevice = win32file.CreateFile(devicename, access, win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE, None, win32con.OPEN_EXISTING, 0, None)
    return hDevice

def getHandleOnVolume(volume, access):
    volumename = "\\\\.\\%c:" % (ord('A') + volume,)
    hVolume = win32file.CreateFile(volumename, access, win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE, None, win32con.OPEN_EXISTING, 0, None);
    return hVolume

def getLockOnVolume(handle):
    data = win32file.DeviceIoControl(handle, winioctlcon.FSCTL_LOCK_VOLUME, None, 0)
    return data

def removeLockOnVolume(handle):
    data = win32file.DeviceIoControl(handle, winioctlcon.FSCTL_UNLOCK_VOLUME, None, 0)
    return data

def unmountVolume(handle):
    data = win32file.DeviceIoControl(handle, winioctlcon.FSCTL_DISMOUNT_VOLUME, None, 0)
    return data

def isVolumeUnmounted(handle):
    data = win32file.DeviceIoControl(handle, winioctlcon.FSCTL_IS_VOLUME_MOUNTED, None, 0)

def readSectorDataFromHandle(handle, startsector, numsectors, sectorsize):
    win32file.SetFilePointer(handle, startsector * sectorsize, win32con.FILE_BEGIN)
    retcode, data = win32file.ReadFile(handle, sectorsize * numsectors)
    if retcode:
        raise Exception("Can't read file")
    return data

def writeSectorDataToHandle(handle, data, startsector, numsectors, sectorsize):
    win32file.SetFilePointer(handle, startsector * sectorsize, win32con.FILE_BEGIN)
    retcode = win32file.WriteFile(handle, data)
    return retcode

def getNumberOfSectors(handle):
    data = win32file.DeviceIoControl(handle, winioctlcon.IOCTL_DISK_GET_DRIVE_GEOMETRY, None, 24)
    Cylinders, MediaType, TracksPerCylinder, SectorsPerTrack, BytesPerSector = struct.unpack("qiiii", data)
    return BytesPerSector, Cylinders * TracksPerCylinder * SectorsPerTrack

def getFileSizeInSectors(handle, sectorsize):
    filesize = win32file.GetFileSize(handle)
    return filesize / sectorsize

def spaceAvailable(location, spaceneeded):
    freespace = win32api.GetDiskFreeSpaceEx(location)[2]
    return spaceneeded <= freespace

def writeImage(imagepath, device, volume="", callback=None):
    deviceID = int(device[-1])
    filelocation = "\\\\.\\%s" % (imagepath,)
    if volume:
        volumeID = ord(volume) - ord('A')
        if deviceID != getPhysicalDeviceID(volumeID):
            print type(deviceID), type(getPhysicalDeviceID(volumeID))
            raise Exception("Wrong volume / disk mapping (%d, %d)" % (deviceID, getPhysicalDeviceID(volumeID)))

        hVolume = getHandleOnVolume(volumeID, win32con.GENERIC_WRITE);
        getLockOnVolume(hVolume)
        unmountVolume(hVolume)

    hFile = getHandleOnFile(filelocation, win32con.GENERIC_READ)
    logging.debug("Image %s opened" % (imagepath, ))

    hRawDisk = getHandleOnDevice(deviceID, win32con.GENERIC_WRITE)
    logging.debug("Device opened")

    sectorsize, availablesectors = getNumberOfSectors(hRawDisk)
    logging.debug("Device has %d sectors of size %d" % (availablesectors, sectorsize))

    numsectors = getFileSizeInSectors(hFile, sectorsize)
    logging.debug("%d sectors of size %d to be written" % (numsectors, sectorsize))

    status = STATUS_WRITING

    if numsectors > availablesectors:
        raise Exception("Not enough space on disk")

    i = 0
    while i < numsectors and status == STATUS_WRITING:
        if numsectors - i >= 1024:
            sectors = 1024
        else:
            sectors = numsectors - i
        sectorData = readSectorDataFromHandle(hFile, i, sectors, sectorsize)
        writeSectorDataToHandle(hRawDisk, sectorData, i, sectors, sectorsize)
        if callback:
            callback(i, numsectors)
        i += 1024

    callback(numsectors, numsectors)

    win32api.CloseHandle(hRawDisk)
    win32api.CloseHandle(hFile)
    if volume:
        removeLockOnVolume(hVolume)
        win32api.CloseHandle(hVolume)

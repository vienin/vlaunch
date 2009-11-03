#!/usr/bin/env python

# UFO-launcher - A multi-platform virtual machine launcher for the UFO OS
#
# Copyright (c) 2008-2009 Agorabox, Inc.
#
# This is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA. 


import uuid
import sys, os
import string

# vmdk file format contants
# type = fullDevice || partitionedDevice

vmdk_header_template ="""# Disk DescriptorFile
version=1
CID=8902101c
parentCID=ffffffff
createType="${type}"

"""

vmdk_footer_template ="""

ddb.virtualHWVersion = "4"
ddb.adapterType="ide"
ddb.geometry.cylinders="${cylinders}"
ddb.geometry.heads="16"
ddb.geometry.sectors="63"
ddb.uuid.image="${uuid}"
ddb.uuid.parent="00000000-0000-0000-0000-000000000000"
ddb.uuid.modification="b0004a36-2323-433e-9bbc-103368bc5e41"
ddb.uuid.parentmodification="00000000-0000-0000-0000-000000000000"
"""

# create a raw vmdk file
# params : target_file_path, device_name, device_size (ko)
def createrawvmdk (target_path, device_name, device_size, partitions = {}, relative = True):
    # generate vmdk uuid
    vmdk_uuid = str(uuid.uuid4())
    
    # write vmdk file
    device_size = int(device_size)
    cylinders = min(device_size / 16 / 63, 16383)

    vmdk_file = open(target_path, 'a')
    
    # write header
    if partitions == {}:
        t = "fullDevice"
    else:
        t = "partitionedDevice"
    vmdk_file.write(string.Template(vmdk_header_template).substitute(type = t))

    # write device infos
    if partitions == {}:
        vmdk_file.write("RW " + str(device_size) + " FLAT \"" + device_name + "\"")
    else:
        partition_table_target_path = target_path[ 0 : len(target_path) - 5] + "-pt.vmdk"

        # copy partition table
        open(partition_table_target_path, 'a').write(open(device_name).read(512))

        # iterate on device partitions
        vmdk_file.write("RW 1 FLAT \"" + os.path.basename(partition_table_target_path) + "\"\n")
        current_part = 1
        incremental_size = 1
        while current_part <= len(partitions):
            part_infos = partitions.get(current_part)

            if relative:
                device = part_infos[0]
                start_bloc = ''
            else:
                device = device_name
                start_bloc = incremental_size

            if part_infos[2]:
                vmdk_file.write("RW " + str(part_infos[1]) + " FLAT \"" + device + "\" " + str(start_bloc) + "\n")
            else:   
                vmdk_file.write("RW " + str(part_infos[1]) + " ZERO " + "\n")

            incremental_size += part_infos[1]
            current_part += 1

        vmdk_file.write("RW " + str(device_size - incremental_size) + " ZERO " + "\n")

    # write footer
    vmdk_file.write(string.Template(vmdk_footer_template).substitute(cylinders = cylinders, uuid = vmdk_uuid))

    vmdk_file.close()

    # return generated uuid to calling process
    return vmdk_uuid

# usefull main
if __name__ == "__main__":
    createrawvmdk(sys.argv[1],sys.argv[2],sys.argv[3]);

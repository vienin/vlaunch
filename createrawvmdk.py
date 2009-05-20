#!/usr/bin/env python

import uuid
import sys
import string

# vmdk file format contants

vmdk_template ="""# Disk DescriptorFile
version=1
CID=8902101c
parentCID=ffffffff
createType="fullDevice"

# Extent description
RW ${size} FLAT "${device}"

# The disk Data Base 
#DDB

ddb.virtualHWVersion = "4"
ddb.adapterType="ide"
ddb.geometry.cylinders="${cylinders}"
ddb.geometry.heads="16"
ddb.geometry.sectors="63"
ddb.uuid.image=${uuid}
ddb.uuid.parent="00000000-0000-0000-0000-000000000000"
ddb.uuid.modification="b0004a36-2323-433e-9bbc-103368bc5e41"
ddb.uuid.parentmodification="00000000-0000-0000-0000-000000000000"
"""

# create a rax vmdk file
# params : target_file_path, device_name, device_size (ko)
def createrawvmdk (target_path, device_name, device_size):
	# generate vmdk uuid
	vmdk_uuid = str(uuid.uuid4())
	
	# write vmdk file
	device_size = int(device_size)
	cylinders = min(device_size / 16 / 63, 16383)

	open(target_path, 'w').write(string.Template(vmdk_template).substitute(
			size = device_size,
			device = device_name,
			cylinders = str(cylinders),
			uuid = vmdk_uuid))

	# return generated uuid to calling process
	return vmdk_uuid

# usefull main
if __name__ == "__main__":
    createrawvmdk(sys.argv[1],sys.argv[2],sys.argv[3]);

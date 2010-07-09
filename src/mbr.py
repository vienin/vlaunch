import os, sys
import struct

BLOCK_SIZE = 512

class MBR:
    def __init__(self, f):
        self.partitions = []
        
        f.seek(0, os.SEEK_SET)
        data = f.read(512)

        for x in xrange(4):
            pt = struct.unpack("BBBBBBBBii", data[x * 16 + 0x01BE : x * 16 + 16 +0x01BE])
            print pt[6], pt[7], pt[6] & 0x3F, pt[6] & 0xC0, pt[7] | (pt[6] & 0xC0)
            self.partitions.append( { "status" : pt[0],
                                      "start_head" : pt[1],
                                      "start_sector" : pt[2] & 0x3F,
                                      "start_cylinder" : pt[3] | ((pt[2] & 0xC0) << 2),
                                      "type" : pt[4],
                                      "end_head" : pt[5],
                                      "end_sector" : pt[6] & 0x3F,
                                      "end_cylinder" : pt[7] | ((pt[6] & 0xC0) << 2),
                                      "lba" : pt[8],
                                      "sectors" : pt[9] })

        self.data = data

    def write(self, f):
        parts = ""
        for part in self.partitions:
            parts += struct.pack("BBBBBBBBii",
                                part["status"],
                                part["start_head"],
                                ((part["start_cylinder"] & 0x300) >> 2) | (part["start_sector"] & 0x3F),
                                part["start_cylinder"] & 0xFF,
                                part["type"],
                                part["end_head"],
                                ((part["end_cylinder"] & 0x300) >> 2) | (part["end_sector"] & 0x3F),
                                part["end_cylinder"] & 0xFF,
                                part["lba"],
                                part["sectors"])
        self.data = self.data[:0x01BE] + parts + "\x55\xAA"
        f.seek(0, os.SEEK_SET)
        f.write(self.data)

    def generate(self, partitions, size, c, h, s):
        cyl_units = h * s * BLOCK_SIZE
        totalsize = cyl_units
        offset = 0
        lba = 1
        start_head = 0
        start_sector = 2
        self.partitions = []
        for n, part in enumerate(partitions):
            type, size, bootable = part["type"], part["size"], part["bootable"]
            if not size:
                cylinders = c - offset
            else:
                cylinders = size / cyl_units - 1
                if size % cyl_units:
                    cylinders += 1
            sectors = cylinders * cyl_units / BLOCK_SIZE
            if bootable:
                status = 0x80
            else:
                status = 0x00
            if n == 0:
                part = {
                     "status" : status,
                     "start_head" : start_head,
                     "start_sector" : start_sector,
                     "start_cylinder" : offset,
                     "end_head" : h - 1,
                     "end_sector" : s,
                     "end_cylinder" : offset + cylinders - 1,
                     "type" : type,
                     "lba" : lba,
                     "sectors" : sectors - lba,
                }
                lba += sectors - lba
            else:
                part = {
                     "status" : status,
                     "start_head" : start_head,
                     "start_sector" : 1,
                     "start_cylinder" : offset,
                     "end_head" : h - 1,
                     "end_sector" : s,
                     "end_cylinder" : offset + cylinders - 1, 
                     "type" : type,
                     "lba" : lba,
                     "sectors" : sectors,
                }
                lba += sectors
            offset += cylinders
            self.partitions.append(part)
    
    def get_partition(self, n):
        return self.partitions[n]

    def get_partition_offset(self, n):
        return self.partitions[n]["lba"] * BLOCK_SIZE

if __name__ == "__main__":
    filename = sys.argv[1]
    mbr = MBR(open(filename))
    print mbr.partitions
    #mbr.generate([700 * 1024 * 1024,
    #              100 * 1024 * 1024,
    #              2500 * 1024 * 1024], 15663104 * 512, 1022, 247, 62)
                  # 100 * 1024 * 1024], 15663104 * 512, 1022, 247, 62)
    #print mbr.partitions



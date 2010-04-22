import sys ; sys.path.insert(0, '.')
import logging
from custom_clamav.clamav import *

CL_Py_Return_Ok = 100
CL_Py_Engine_Error = 101
CL_Py_Bad_Argument = 102
CL_Py_File_Not_Found = 103
CL_Py_Scan_Already_Running = 104
CL_Py_Scan_Cancelled = 105
CL_Py_No_File_To_Scan = 106
CL_Py_DNS_Error = 107
CL_Py_Download_Error = 108
CL_Py_TempFile_Error = 109

errors = {
          CL_Py_Return_Ok : "Execution Successful",
          CL_Py_Engine_Error : "Engine Initialization Error",
          CL_Py_Bad_Argument : "Bad Argument",
          CL_Py_File_Not_Found : "File Not Found",
          CL_Py_Scan_Already_Running : "Scan Already Running",
          CL_Py_Scan_Cancelled : "Scan Cancelled",
          CL_Py_No_File_To_Scan : "No File To Scan",
          CL_Py_DNS_Error : "DNS error",
          CL_Py_Download_Error : "File Too Short",
          CL_Py_TempFile_Error : "Temp File Error"
          }

class Py_Clamav_Exception(Exception):
    """
    Py_Clamav Exception Class
    0 => 30 Clamav Exception
    100 =>  Py Clamav Exception
    """
    def __init__(self, errno):
        Exception.__init__(self)
        self.errno = errno
        
    def __str__(self):
        if self.errno < 30 :
            return cl_strerror(self.errno)
        elif self.errno in errors:
            return errors[self.errno]
        return "Unknown error"

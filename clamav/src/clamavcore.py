# PyDNS library Import 
# Need DNS directory in the same directory of this class
import sys ; sys.path.insert(0, '.')
import DNS
# Other Import
import os
import stat
import mimetypes
import urllib
import urllib2
import time
import stat
import tempfile
import re
import glob
import shutil
import _winreg
import logging 

from string import atoi
from custom_clamav.clamav import *
from logging import StreamHandler

main_url = 'http://database.clamav.net/main.cvd'
daily_url = 'http://database.clamav.net/daily.cvd'

cd_database_path = ".\\update_cd\\"
database_path = ".\\update\\"

main_path = database_path + "main.cvd"
daily_path = database_path + "daily.cvd"

main_type = 1
daily_type = 2

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='[%(thread)d] %(levelname)-2s %(filename)s:%(lineno)d %(message)s')

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

errors = { CL_Py_Return_Ok : "Execution Successful",
           CL_Py_Engine_Error : "Engine Initialization Error",
           CL_Py_Bad_Argument : "Bad Argument",
           CL_Py_File_Not_Found : "File Not Found",
           CL_Py_Scan_Already_Running : "Scan Already Running",
           CL_Py_Scan_Cancelled : "Scan Cancelled",
           CL_Py_No_File_To_Scan : "No File To Scan",
           CL_Py_DNS_Error : "DNS error",
           CL_Py_Download_Error : "File Too Short",
           CL_Py_TempFile_Error : "Temp File Error" }


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


class Py_Clamav(object):
    "Clamav Py Class"
    url_update = "http://database.clamav.net/"
    filters = []
    other_file = True

    def __init__(self, inform, progress_callback=None):
        global database_path
        self.inform = inform
        self.running = False
        self.engine = None
        self.database_loaded = False
        self.update_if_necessary(progress_callback)
        try:
            self.initialize()
        except:
            self.use_emergency_database()
            self.initialize()
        self.database_loaded = True
        
    def initialize(self):
        self.inform(_("initializing database"))
        res = cl_init(CL_INIT_DEFAULT)
        if res != CL_SUCCESS and res != CL_EARG :
            raise Py_Clamav_Exception(res)

        self.engine = cl_engine_new()
        if self.engine == None:
            raise Py_Clamav_Exception(CL_Py_Engine_Error)
        sigs = 0

        ret, sigs = cl_load(database_path, self.engine, sigs, CL_DB_STDOPT)

        if ret != CL_SUCCESS:
            raise Py_Clamav_Exception(ret)
        
        ret = cl_engine_compile(self.engine) 
        
        if ret != CL_SUCCESS:
            raise Py_Clamav_Exception(ret)
        
        self.inform(_("virus database ready"))
        return CL_Py_Return_Ok

    def add_filter(self, ext):
        """
        Add ext to filter list if not empty, else raise exception
        """
        if ext == "":
            raise Py_Clamav_Exception(CL_Py_Bad_Argument)
        
        return self.filters.append(ext)
        
    def remove_filter(self, ext):
        """
        Remove ext to filter list if exist, else raise exception
        """
        if ext in self.filters:
            res = self.filters.remove(ext)
        else:
            raise Py_Clamav_Exception(CL_Py_Bad_Argument)
        return res
        
    def reset_filter(self):
        """
        Reset filter list
        """
        self.filters = []
        return CL_Py_Return_Ok
        
    def __default_print(message):
        """
        Default method called by scan_file to inform file name during scan
        """
        return CL_Py_Return_Ok

    def __default_print_virus(file_name, virus_name):
        """
        Default method for print virus name of infected file
        """
        return CL_Py_Return_Ok

    def scan_file(self, file_name=None, f_func=__default_print, v_func=__default_print_virus):
        """
        Scan file by file_name and call f_func(file_name) for file information and v_func(file_name,virus_name) for virus information 
        """

        if file_name == None:
            raise Py_Clamav_Exception(CL_Py_Bad_Argument)

        if not os.path.exists(file_name):
            raise Py_Clamav_Exception(CL_Py_File_Not_Found)

        if not self.database_loaded:
            f_func("Waiting for database loading")
            while not self.database_loaded:
                time.sleep(0.2)

        f_func('scanning ' + self.pretty_path(file_name))
        try:
            f = open(file_name)
        except IOError:
            f_func('File Open Error' + file_name)
            return

        virus_name = [""]
        size = 0
        res = cl_scandesc(f.fileno(), virus_name, size, self.engine, CL_SCAN_STDOPT)

        if  res[0] == CL_VIRUS :
            v_func(file_name, res[1])

        if res[0] != CL_SUCCESS:
            if res[0] != CL_VIRUS:   
                raise Py_Clamav_Exception(res)
        f.close()
        return res
    
    def scan(self, path, f_func=__default_print, v_func=__default_print_virus):
        if self.running :
            return CL_Py_Scan_Already_Running
        
        if len(self.filters) == 0 and not self.other_file:
            self.inform(_("filter list is empty"))
            return CL_Py_Return_Ok
        self.running = True
        
        if not os.path.exists(path):
            f_func("Error exists " + path)
            
        if os.path.isdir(path) :
            self.scan_dir(path, f_func, v_func)
        if os.path.isfile(path):
            self.scan_file(path, f_func, v_func)
        
        f_func(_("scan finished"))
        self.running = False
        
        return CL_Py_Return_Ok
    
    def stop_scan(self):
        """
        Manual Stop
        """
        if self.running:
            self.running = False

    def scan_dir(self, dir_path=None, f_func=__default_print, v_func=__default_print_virus):
        """
        Scan dir_path 
        """
        if dir_path == None:
            return 1
        
        if not os.path.exists(dir_path):
            return 1
        
        if not dir_path.endswith("/"):
            dir_path = dir_path + "/"
        
        try:
            file_list = os.listdir(dir_path)
        except:
            logging.debug("Antivirus: acces refused on " + dir_path)
            return CL_SUCCESS
        
        if not self.running :
            return CL_Py_Scan_Cancelled
        
        if len(file_list) == 0:
            return CL_Py_No_File_To_Scan
        
        for file_name in file_list:
            if not self.running :
                break
            self.__file_treatment(os.path.join(dir_path+"/"+file_name), f_func, v_func)

    def use_emergency_database(self):
        logging.debug("Antivirus: using emergency database")
        shutil.copy2(os.path.join(cd_database_path + "main.cvd"), os.path.join(database_path + "main.cvd"))
        shutil.copy2(os.path.join(cd_database_path + "daily.cvd"), os.path.join(database_path + "daily.cvd"))
    
    def update_if_necessary(self, call_function_progress=None):
        """
        Check if clamav is up to date, else force update
        """
        global main_url
        global daily_url
        global main_path
        global daily_path

        self.inform(_("checking database updates"))
 
        try:
            # Test if tmporary database file exists, remove them
            tmp_files = glob.glob(os.path.join(database_path, "*.tmp"))
            if len(tmp_files):
                for tmp in tmp_files:
                    os.unlink(tmp)

            # Test if updated database exists, download last one
            if not os.path.exists(main_path):
                logging.debug("Antivirus: no updated main file, forcing update")
                self.inform(_("dowloading database update (1/2)"))
                urllib.urlretrieve(main_url, main_path + ".tmp", call_function_progress)
                os.rename(main_path + ".tmp", main_path)
            if not os.path.exists(daily_path):
                logging.debug("Antivirus: no updated daily file, forcing update")
                self.inform(_("dowloading database update (2/2)"))
                urllib.urlretrieve(daily_url, daily_path + ".tmp", call_function_progress)
                os.rename(daily_path + ".tmp", daily_path)
        except:
            self.use_emergency_database()
            
        try:
            # Test if update download has failed during last session
            self.rescue_failed_update()

            # Here we have update database files in update directory
            r_current_version = self.__get_remote_current_version()
            logging.debug("Antivirus: current remote database version, " + str(r_current_version))
            if not r_current_version:
                return
        
            main_need_update  = False
            daily_need_update = False
            l_main_current_version  = self.__get_local_current_version(main_path)
            l_daily_current_version = self.__get_local_current_version(daily_path)
            logging.debug("Antivirus: current local database version, " + str(l_main_current_version) + ", " + str(l_daily_current_version))

            # Test if updated database version is deprecated
            if not l_main_current_version or l_main_current_version < r_current_version["main"]:
                main_need_update = True
            if not l_daily_current_version or l_daily_current_version < r_current_version["daily"]:
                daily_need_update = True
                
            # Retreive remote database files
            if main_need_update:
                self.inform(_("dowloading database update (1/2)"))
                os.rename(main_path, main_path + ".last")
                urllib.urlretrieve(main_url, main_path, call_function_progress)
                os.remove(main_path + ".last")

            if daily_need_update:
                self.inform(_("dowloading database update (2/2)"))
                os.rename(daily_path, daily_path + ".last")
                urllib.urlretrieve(daily_url, daily_path, call_function_progress)
                os.remove(daily_path + ".last")

        except:
            logging.debug("Antivirus: update downoad failed")
            self.rescue_failed_update()

    def rescue_failed_update(self):
        if os.path.exists(main_path + ".last"):
            logging.debug("Antivirus: retrieving " + main_path + ".last")
            if os.path.exists(main_path):
                os.unlink(main_path)
            os.rename(main_path + ".last", main_path)
        if os.path.exists(daily_path + ".last"):
            if os.path.exists(daily_path):
                os.unlink(daily_path)
            logging.debug("Antivirus: retrieving " + daily_path + ".last")
            os.rename(daily_path + ".last", daily_path)
    
    def pretty_path(self, path):
        if len(path) > 33:
            return path[:10] + "..." + path[len(path)-20:]
        return path

    def __resolv_conf_for_win(self):
        """
        Hack for windows to create resolv.conf for dns server resolution
        """
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters', 0, _winreg.KEY_READ)
        (valeur, typevaleur) = _winreg.QueryValueEx(key, 'DhcpNameServer')
        _winreg.CloseKey(key)

        #fichier temporaire
        resolv_conf = tempfile.NamedTemporaryFile('w+b', -1, '', 'tmp_solv_', '.', False)
        resolv_conf.write('nameserver ' + valeur)
        resolv_conf.close()
        
        return resolv_conf.name
    
    def __get_remote_current_version(self):
        """
        Retrieve last info about database 
        return dictionary that contains engine, main and daily current version, else None
        """
        # automatically load nameserver(s) from /etc/resolv.conf
        # (works on unix - not on windows
        conf = self.__resolv_conf_for_win()
        DNS.ParseResolvConf(conf)
        self.__del_file(conf)
        
        dns_request = DNS.DnsRequest(name='current.cvd.clamav.net', qtype='TXT')
        dns_answer = dns_request.req()
        if not dns_answer:
            return CL_Py_DNS_Error
            
        all_info = dns_answer.answers[0]
        
        raw = str(all_info["data"][0])
        
        raw_split = raw.split(':')
        
        current_version = dict()
        current_version["engine"] = raw_split[0]
        current_version["main"] = atoi(raw_split[1])
        current_version["daily"] = atoi(raw_split[2])
        
        return current_version
    
    def __get_local_current_version(self, file_name=None):
        """
        Return File Version of local Database
        """    
        if not(os.path.exists(file_name)):
            return False

        cl_cvd_test = cl_cvdhead(file_name)
        
        if cl_cvd_test :
            return cl_cvd_test.version
        
        return False
        
    def __del_file(self, file_name):
        """
        Delete file_name if exists    
        """
        if os.path.exists(file_name):
            os.remove(file_name)
            return CL_Py_Return_Ok
        return CL_Py_File_Not_Found

    def __file_treatment(self, file_name, f_func=__default_print, v_func=__default_print_virus):
        """
        Return file list form dir_path
        """
        try:
            st = os.lstat(file_name)
        except os.error:
            f_func('File Open Error' + file_name)
            return
         
        if stat.S_ISDIR(st.st_mode):
            self.scan_dir(file_name, f_func, v_func)
            return

        ok = False
        
        mime, desc = mimetypes.guess_type(file_name)
        if not mime:
            return     
        mime = mime.lower()
        try:
            self.filters.index(mime)
            ok = True
        except ValueError:
            if self.other_file:
                ok = True
            
        if ok : 
            self.scan_file(file_name, f_func, v_func)
        
        return

    def __del__(self):
        if self.engine:
            ret = cl_engine_free(self.engine)
            if ret != CL_SUCCESS:
                raise Py_Clamav_Exception(ret)
                exit(2)

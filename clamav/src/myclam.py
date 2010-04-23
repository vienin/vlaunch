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
import shutil
import _winreg
import logging 
from clam_exception import *


from string import atoi
from custom_clamav.clamav import *
from logging import StreamHandler

main_url = 'http://database.clamav.net/main.cvd'
daily_url = 'http://database.clamav.net/daily.cvd'

cd_database_path = ".\\update_cd\\"
database_path = ".\\update\\"

main_path = database_path + "main.cvd"
daily_path = database_path + "daily.cvd"

dir_temp_path = ""

main_type = 1
daily_type = 2

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='[%(thread)d] %(levelname)-2s %(filename)s:%(lineno)d %(message)s')

class Py_Clamav(object):
    "Clamav Py Class"
    url_update = "http://database.clamav.net/"
    filters = []
    other_file = True
       
    def __init__(self, inform):
        global database_path
        self.inform = inform
        self.running = False
        self.database_loaded = False
        self.update_if_necessary()
        self.initialize()
        self.database_loaded = True
      

        
    def initialize(self):
        self.inform("DataBase initialization")
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
        
        self.inform("Database Ready")
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
        
    def scan_file(self, file_name=None, f_func=__default_print, v_func=__default_print_virus, check_exist=1):
        """
        Scan file by file_name and call f_func(file_name) for file information and v_func(file_name,virus_name) for virus information 
        """
        if file_name == None:
            raise Py_Clamav_Exception(CL_Py_Bad_Argument)
        
        if os.path.exists(file_name) == -1 and check_exist:
            raise Py_Clamav_Exception(CL_Py_File_Not_Found)

        if not self.database_loaded:
            f_func("Waiting for database loading")
            while not self.database_loaded:
                time.sleep(0.2)
            
        f_func('Scanning ' + file_name)
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
                print cl_strerror(res[0])
                raise Py_Clamav_Exception(res)
        f.close()
        return res
    
    def scan(self, path, f_func=__default_print, v_func=__default_print_virus):
        if self.running :
            return CL_Py_Scan_Already_Running
        
        if len(self.filters) == 0 and not self.other_file:
            self.inform("Empty Filter")
            return CL_Py_Return_Ok
        self.running = True
        
        if not os.path.exists(path):
            f_func("Error exists " + path)
            
        if os.path.isdir(path) :
            self.scan_dir(path, f_func, v_func, 1)
        if os.path.isfile(path):
            self.scan_file(path, f_func, v_func, 1)
        
        f_func("End SCAN")
        self.running = False
        
        return CL_Py_Return_Ok
    
    def stop_scan(self):
        """
        Manual Stop
        """
        if self.running:
            self.running = False
        
    def __file_treatment(self, file_name, f_func=__default_print, v_func=__default_print_virus, check_exist=1):
        """
        Return file list form dir_path
        """
        try:
            st = os.lstat(file_name)
        except os.error:
            f_func('File Open Error' + file_name)
            return
         
        if stat.S_ISDIR(st.st_mode):
            self.scan_dir(file_name, f_func, v_func, check_exist)
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
            self.scan_file(file_name, f_func, v_func, check_exist)
        
        return
            
    def scan_dir(self, dir_path=None, f_func=__default_print, v_func=__default_print_virus, check_exist=1):
        """
        Scan dir_path 
        """
        if dir_path == None:
            return 1
            
        if os.path.exists(dir_path) == -1 and check_exist:
            return 1
        
        if not dir_path.endswith("/"): 
            dir_path = dir_path + "/"
        
        file_list = os.listdir(dir_path)
        
        if not self.running :
            return CL_Py_Scan_Cancelled
        
        if len(file_list) == 0:
            return CL_Py_No_File_To_Scan
        
        for file_name in file_list:
            if not self.running :
                break
            self.__file_treatment(os.path.join(dir_path+"/"+file_name), f_func, v_func, check_exist)
            
    def progression(nb_block_transfered, block_size, total_size):
        return
    
    def _resolv_conf_for_win(self):
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
        conf = self._resolv_conf_for_win()
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
    
    def __get_last_file(self, remote_file, target_file, call_function=progression):
        """
        Download remote_file to target_file
        Return 1 if success, else False
        """
        global dir_temp_path
        
        if not(dir_temp_path) :
            self.__init_temp_dir()
        
        target_file = dir_temp_path + target_file
        self.__del_file(target_file)
        
        try: 
            urllib.urlretrieve(remote_file, target_file, call_function)
        except urllib.ContentTooShortError:
            self.__del_file(target_file)
            return CL_Py_Download_Error
        except IOError:
            self.__del_file(target_file)
            return CL_Py_Download_Error 
        
        return target_file
        
    def __del_file(self, file_name):
        """
        Delete file_name if exists    
        """
        if os.path.exists(file_name):
            os.remove(file_name)
            return CL_Py_Return_Ok
        return CL_Py_File_Not_Found
    
    def __check_tmp_database(self, db_path):
        """
        Try to load database
        Return      if success, else False
        """
        res = cl_init(CL_INIT_DEFAULT)
        if res != CL_SUCCESS:
            return False
    
        engine = cl_engine_new()
    
        if engine == None:
            return False
        
        sigs = 0
        ret, sigs = cl_load(db_path, engine, sigs, CL_DB_STDOPT)
    
        if ret != CL_SUCCESS:
            return False
    
        if cl_engine_compile(engine) != CL_SUCCESS:
            return False
            
        cl_engine_free(engine)
            
        return True
    
    def __clean_database_dir(self):
        """
        Delete all temp folders created by the program
        """
        global database_path
        regex_test = re.compile("^cl_db_")
    #    database path_cleaning
        for file_name in os.listdir(database_path):
            if regex_test.search(file_name):
                try:
                    st = os.lstat(os.path.join(database_path + file_name))
                    if stat.S_ISDIR(st.st_mode):
                        shutil.rmtree(os.path.join(database_path + file_name))
                except os.error:
                    continue
                
    def __init_temp_dir(self):
        """
        Create temp folder for downloading database
        """
        global database_path
        global dir_temp_path
    
        self.__clean_database_dir()
    #    dir temp generation
        dir_temp_path = tempfile.mkdtemp("", "cl_db_", database_path)
        if not(dir_temp_path):
            raise Py_Clamav_Exception(CL_Py_TempFile_Error)
        dir_temp_path = dir_temp_path + "/" 
        
        return dir_temp_path
    
    def update_if_necessary(self, call_function_progress=None):
        """
        Check if clamav is up to date, else force update
        """
        global main_url
        global daily_url
        global main_path
        global daily_path
        global dir_temp_path
        
        self.inform("DataBase Updating")
        if not(os.path.exists(main_path)) or not(os.path.exists(daily_path)):
            if not self.force_update(call_function_progress):
                shutil.copy2(os.path.join(cd_database_path + "main.cvd"), os.path.join(database_path + "main.cvd"))
                shutil.copy2(os.path.join(cd_database_path + "daily.cvd"), os.path.join(database_path + "daily.cvd"))
                return False
        
        r_current_version = self.__get_remote_current_version()
        
        if not r_current_version:
            return False
        
        self.__init_temp_dir()
        
        main_v_local = self.__get_local_current_version(main_path)
        main_need_update = False
        
        if not main_v_local:
            main_need_update = 1
        else:
            if main_v_local < r_current_version["main"]:
                main_need_update = 1
                
        if main_need_update:
            if not(self.__get_last_file(main_url, "main.cvd", call_function_progress)):
                shutil.copy2(os.path.join(database_path + "main.cvd"), os.path.join(dir_temp_path + "main.cvd"))
        else:
            shutil.copy2(os.path.join(database_path + "main.cvd"), os.path.join(dir_temp_path + "main.cvd"))

        daily_v_local = self.__get_local_current_version(daily_path)
        daily_need_update = False
        
        if not daily_v_local:
            daily_need_update = 1
        else:
            if daily_v_local < r_current_version["daily"]:
                daily_need_update = 1
        if daily_need_update:
            if not(self.__get_last_file(daily_url, "daily.cvd", call_function_progress)):
                shutil.copy2(os.path.join(database_path + "daily.cvd"), os.path.join(dir_temp_path + "daily.cvd"))
        else:
            shutil.copy2(os.path.join(database_path + "daily.cvd"), os.path.join(dir_temp_path + "daily.cvd"))
            
        if main_need_update or daily_need_update :
            if self.__check_tmp_database(dir_temp_path):
                shutil.copy2(os.path.join(dir_temp_path + "main.cvd"), os.path.join(database_path + "main.cvd"))
                shutil.copy2(os.path.join(dir_temp_path + "daily.cvd"), os.path.join(database_path + "daily.cvd"))
            else: 
                shutil.copy2(os.path.join(cd_database_path + "main.cvd"), os.path.join(database_path + "main.cvd"))
                shutil.copy2(os.path.join(cd_database_path + "daily.cvd"), os.path.join(database_path + "daily.cvd"))
            
        self.__clean_database_dir()
        dir_temp_path = ""

    def force_update(self, call_function_progress=None):
        global main_url
        global daily_url
        global main_path
        global daily_path
        global dir_temp_path
        
        self.__init_temp_dir()
        if not(self.__get_last_file(main_url, "main.cvd", call_function_progress)):
                return False
        if not(self.__get_last_file(daily_url, "daily.cvd", call_function_progress)):
                return False
            
        if self.__check_tmp_database(dir_temp_path):
            shutil.copyfile(os.path.join(dir_temp_path + "main.cvd"), os.path.join(database_path + "main.cvd"))
            shutil.copyfile(os.path.join(dir_temp_path + "daily.cvd"), os.path.join(database_path + "daily.cvd"))
            self.initialize()
        else: 
            logging.debug("Erreur")
            return False

        self.__clean_database_dir()
        dir_temp_path = ""
        return 1
    
    def __del__(self):
        self.__clean_database_dir()
        dir_temp_path = ""
        ret = cl_engine_free(self.engine)
        if ret != CL_SUCCESS:
            raise Py_Clamav_Exception(ret)
            exit(2)

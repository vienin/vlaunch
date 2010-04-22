import sys
import os
from PyQt4 import QtGui, QtCore
import myclam
import time
import threading
import logging 
import _winreg
import shutil

VIRUS_DELETE = 1
VIRUS_IGNORE = 2
VIRUS_PASS = 3


class Antivirus(QtGui.QDialog):
    def __init__(self, print_widget_dest, parent=None):
        super(Antivirus, self).__init__(parent)
        
        self.user_home_path = os.path.expanduser("~")
        self.shell_key = ('Desktop', 'My Music', 'My Pictures')
        self.running = False
        self.print_widget_dest = print_widget_dest
        self.connect(self, QtCore.SIGNAL("virus_list_updated"), self.refresh_virus_list)
        self.virus_tab_exist = False
        
        self.mutex_running = QtCore.QMutex()
        self.mutex_running.lock()

        self.thread_scan = T_scan()
        self.connect(self.thread_scan, QtCore.SIGNAL("scan_end_signal"), self.after_scan)      
        self.connect(self.thread_scan, QtCore.SIGNAL("scan_end_signal"), self.after_scan)      
        self.connect(self, QtCore.SIGNAL("scan_stop_signal"), self.thread_scan.stop_scan)
        
        self.connect(self.thread_scan, QtCore.SIGNAL("virus_detected(QString,QString)"), self.print_scan_virus)
        self.connect(self.thread_scan, QtCore.SIGNAL("virus_detected(QString,QString)"), self.manage_virus_found)
        self.connect(self.thread_scan, QtCore.SIGNAL("inform(QString)"), self.print_info)
        
        self.init_shell_folder()
        
        self.add_selection_button = QtGui.QPushButton("+")
        self.connect(self.add_selection_button, QtCore.SIGNAL('clicked()'), self.click_add_selection)
        
        self.remove_selection_button = QtGui.QPushButton("-")
        self.connect(self.remove_selection_button, QtCore.SIGNAL('clicked()'), self.click_remove_selection)
        
        self.launch_button = QtGui.QPushButton("Launch")
        self.connect(self.launch_button, QtCore.SIGNAL('clicked()'), self.click_scan)
        self.launch_button.installEventFilter(self)
        
        self.del_button = dict()
        self.ignore_button = dict()
        self.pass_button = dict()
        
        self.dir_model = QtGui.QFileSystemModel()
        index = self.dir_model.setRootPath("/")
        self.dir_model.insertRow(5)      
        self.root_tree_view = QtGui.QTreeView()
        self.root_tree_view.setModel(self.dir_model)
        self.root_tree_view.setAnimated(1)
        self.root_tree_view.setColumnHidden(3, True)
        self.root_tree_view.setColumnWidth(0, 150)
        self.root_tree_view.setSortingEnabled(True)
        self.connect(self.root_tree_view, QtCore.SIGNAL("clicked(QModelIndex)"), self.__disable_shell_list)
        
        self.list_scan = QtGui.QTreeWidget()
        self.list_scan.setColumnCount(3)
        self.list_scan.setHeaderLabels(("Name", "Path", "Checked"))
        
        self.shell_list = QtGui.QTreeWidget()
        self.shell_list.setColumnCount(1)
        self.shell_list.setHeaderLabel("My Documents")
        
        for dir_name in self.shell_folder:
            self.shell_list.addTopLevelItem(QtGui.QTreeWidgetItem((str(dir_name), str(self.shell_folder[dir_name]))))
        self.connect(self.shell_list, QtCore.SIGNAL("itemPressed(QTreeWidgetItem *,int)"), self.__disable_racine_tree)
        
        self.print_layout = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight)
        print_widget = QtGui.QWidget()
        self.print_label = QtGui.QLabel("")
        self.print_layout.addWidget(self.print_label)
        print_widget.setLayout(self.print_layout)
        
        selection_widget = QtGui.QWidget()
        selection_layout = QtGui.QHBoxLayout()
        selection_layout.addWidget(self.add_selection_button)
        selection_layout.addWidget(self.remove_selection_button)
        selection_widget.setLayout(selection_layout)
        
        command_widget = QtGui.QWidget()
        command_layout = QtGui.QHBoxLayout()
        command_layout.addWidget(self.launch_button)
        command_widget.setLayout(command_layout)
        
        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(self.shell_list)
        main_layout.addWidget(self.root_tree_view)
        main_layout.addWidget(selection_widget)
        main_layout.addWidget(self.list_scan)
        main_layout.addWidget(command_widget)
        main_layout.addWidget(print_widget)
        
        main_interface = QtGui.QDialog()
        main_interface.setLayout(main_layout)
        
        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.addTab(main_interface, "Main")
        
        general_layout = QtGui.QHBoxLayout()
        general_layout.addWidget(self.tab_widget)
        
        self.setLayout(general_layout)
        
        self.virus_pass = dict()
        self.virus_found = dict()
        
    def init_shell_folder(self):
        """
        Get Shell Folders path from registry 
        Only for Windows
        """
        self.shell_folder = dict({})
        key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders', 0, _winreg.KEY_READ)
        
        for one in self.shell_key:
            (valeur, typevaleur) = _winreg.QueryValueEx(key, "Desktop")
            self.shell_folder[one] = _winreg.ExpandEnvironmentStrings(valeur)
        _winreg.CloseKey(key)
        
    def __disable_racine_tree(self, item, column):
        """
        Disable any selection on root_tree_view
        """
        self.root_tree_view.clearSelection()
        
    def __disable_shell_list(self, index):
        """
        Disable any selection on shell_list
        """
        self.shell_list.clearSelection()
        
    def click_add_selection(self):
        """
        Add Selection Listener
        """
        if not(self.root_tree_view.selectedIndexes()) and not(self.shell_list.selectedIndexes()):
            return
        
        if self.root_tree_view.selectedIndexes() :
            list_selected = self.root_tree_view.selectedIndexes() 
            item_selected = list_selected[0]
            file_path = self.dir_model.filePath(item_selected)
            file_name = self.dir_model.fileName(item_selected)
            
        if self.shell_list.selectedIndexes() :
            list_selected = self.shell_list.selectedIndexes()
            item_selected = self.shell_list.itemFromIndex(list_selected[0])
            file_path = item_selected.text(1)
            file_name = item_selected.text(0)
        
        if self.__selection_son_of_element(file_name):
            return
        
        self.__selection_father_of_element(file_path)
        
        if self.__selection_same(file_path):
            return
        
        self.list_scan.addTopLevelItem(QtGui.QTreeWidgetItem((file_name, file_path)))
        
    def click_remove_selection(self):
        """
        Remove Selection Listener
        """
        list_selected = self.list_scan.selectedIndexes()
        if not list_selected :
            return
        last = self.list_scan.findItems(self.list_scan.itemFromIndex(list_selected[0]).text(1), QtCore.Qt.MatchFlag(QtCore.Qt.MatchExactly), 1)
        if not last:
            return
        self.list_scan.removeItemWidget(last[0], 0)
        
    def click_scan(self):
        """
        Launch Scan Listener
        """
        self.mutex_running.lock()
        if self.running == True:
            scan_list = self.list_scan.findItems(".*", QtCore.Qt.MatchFlag(QtCore.Qt.MatchRegExp))
            scan_list_clean = []
            for one in scan_list:
                if self.running == False:
                    return
                scan_list_clean.append(str(one.text(1)))
            
            self.thread_scan.launch_scan(scan_list_clean, self.print_scan, self.print_scan_virus)
    
    def __selection_son_of_element(self, path):
        """
        Check if path is a son of an element in scan list
        """
        path_search = os.path.dirname(str(path))
        old_path = ""
        while(path_search != old_path):
            if self.list_scan.findItems(path_search, QtCore.Qt.MatchFlag(QtCore.Qt.MatchExactly), 1):
                return True
            
            if path_search.endswith("/"):
                path_search = path_search[0:len(path_search) - 1]
                if self.list_scan.findItems(path_search, QtCore.Qt.MatchFlag(QtCore.Qt.MatchExactly), 1):
                    return True
            old_path = path_search
            path_search = os.path.dirname(path_search)
        return False
    
    def __selection_father_of_element(self, path):
        """
        Check if father of element of scan list
        Delete all of sons 
        """
        matched_list = self.list_scan.findItems(str(path), QtCore.Qt.MatchFlag(QtCore.Qt.MatchStartsWith), 1)
        for i in range(len(matched_list)):
            if matched_list[i].text(1) != str(path):
                self.list_scan.removeItemWidget(matched_list[i], 0)
                  
    def __selection_same(self, path):
        """
        Check if already exists in scan list
        """
        return  self.list_scan.findItems(str(path), QtCore.Qt.MatchFlag(QtCore.Qt.MatchExactly), 1)
    
    def before_scan(self):
        """
        Before Scan Actions 
        """
        self.running = True
        self.add_selection_button.setEnabled(False)
        self.remove_selection_button.setEnabled(False)
        self.launch_button.setText("Stopper")
        
    def after_scan(self):
        """
        After Scan Actions
        """
        self.running = False
        self.add_selection_button.setEnabled(True)
        self.remove_selection_button.setEnabled(True)
        self.launch_button.setText("Lancer")
        self.launch_button.setEnabled(True)
        self.print_label.setText("")
    
    def eventFilter(self, sender_object, received_event):
        """
        Event Filter for 
        - launch_button
        """
        if sender_object in [self.launch_button] :
            if (received_event.type() == QtCore.QEvent.MouseButtonPress): 
                if self.running == True:
                    self.running = False
                    self.emit(QtCore.SIGNAL("scan_stop_signal"))
                else:
                    self.before_scan()
                self.mutex_running.unlock()
        return QtCore.QObject.eventFilter(self, sender_object, received_event)

    def print_scan(self, message):
        self.print_label.setText(message)
        
    def print_info(self, message):
        self.print_label.setText(message)
        
    def print_scan_virus(self, file_name, virus_name):
        logging.debug("Virus Found in" + file_name + " :" + virus_name)

    def manage_virus_found(self, file_name, virus_name):
        if not (file_name in self.virus_found) and not (file_name in self.virus_pass):
            self.virus_found[file_name] = virus_name
            self.emit(QtCore.SIGNAL("virus_list_updated"))

    def del_virus_attitude(self, file_path):
        """
        Remove path where virus was found
        """
        if file_path in self.virus_found:
            if not os.path.exists(file_path):
                return 1
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            if os.path.isfile(file_path):
                self.unlink(file_path)
                
    def pass_virus_attitude(self, file_path):
        """
        Add file_name to virus_pass list
        """
        if not (file_path in self.virus_found):
            return
        
        if not (file_path in self.virus_pass):
            self.virus_pass[file_path] = self.virus_found[file_path]
            self.virus_found.pop(file_path)
            self.emit(QtCore.SIGNAL("virus_list_updated"))
            
        
        
    def ignore_virus_attitude(self, file_path):
        """
        Remove file_name from virus_found list
        """
        if file_path in self.virus_found:
            self.virus_found.pop(file_path) 
            self.emit(QtCore.SIGNAL("virus_list_updated"))

    def virus_attitude(self, file_name, virus_name, action=VIRUS_DELETE):
        """
        CallBack for virus treatment
        """
        {
        VIRUS_DELETE:self.del_virus_attitude,
        VIRUS_IGNORE:self.ignore_virus_attitude,
        VIRUS_PASS:self.pass_virus_attitude  
        }[action](file_name)
    
    def init_virus_tab(self):
        """
        Initialize virus tab
        """
        virus_tab = QtGui.QDialog()
        layout = QtGui.QVBoxLayout()
        self.virus_list = QtGui.QTreeWidget()
        self.virus_list.setColumnCount(2)
        self.virus_list.setHeaderLabels(("Name", "Path"))
        
        ignore_button = QtGui.QPushButton("IGNORE")
        self.connect(ignore_button, QtCore.SIGNAL('clicked()'), self.click_virus_ignore)
        
        delete_button = QtGui.QPushButton("DELETE")
        self.connect(delete_button, QtCore.SIGNAL('clicked()'), self.click_virus_del)
        
        virus_command = QtGui.QWidget()
        virus_layout = QtGui.QHBoxLayout()
        virus_layout.addWidget(ignore_button)
        virus_layout.addWidget(delete_button)
        virus_command.setLayout(virus_layout)
        
        
        layout.addWidget(self.virus_list)
        layout.addWidget(virus_command)
        virus_tab.setLayout(layout)
        self.virus_tab_exist = self.tab_widget.addTab(virus_tab, "Virus Found")

    def del_virus_tab(self):
        """
        Remove Virus Tab
        """
        if self.virus_tab_exist :
            self.tab_widget.removeTab(self.virus_tab_exist)
            self.virus_tab_exist = False
        
    def refresh_virus_list(self):
        """
        Refresh virus list on virus tab
        """
        if not self.virus_tab_exist:
            self.init_virus_tab()
        self.virus_list.clear()
        
        if len(self.virus_found) == 0 and len(self.virus_pass) == 0:
            self.del_virus_tab()
            return 
        
        for name in self.virus_found:
            self.virus_list.addTopLevelItem(QtGui.QTreeWidgetItem((self.virus_found[name], name)))
            
        for name in self.virus_pass:
            self.virus_list.addTopLevelItem(QtGui.QTreeWidgetItem((self.virus_pass[name], name)))
            
    def click_virus_del(self):
        """
        CallBack for button delete virus on virus tab
        """
        if not self.virus_tab_exist:
            return
        if self.virus_list.selectedIndexes() :
            list_selected = self.virus_list.selectedIndexes()
            index_selected = list_selected[0] 
            item_selected = self.virus_list.itemFromIndex(index_selected)
            virus_name = item_selected.text(0)
            file_name = item_selected.text(1)
        
    def click_virus_ignore(self):
        """
        CallBack for button ignore virus on virus tab
        """
        if not self.virus_tab_exist:
            return
        if self.virus_list.selectedIndexes() :
            list_selected = self.virus_list.selectedIndexes()
            index_selected = list_selected[0] 
            item_selected = self.virus_list.itemFromIndex(index_selected)
            virus_name = item_selected.text(0)
            file_name = item_selected.text(1)
            self.ignore_virus_attitude(file_name)
    
    def show(self):
        """
        Override for forcing virus tab to appear if present
        """
        if self.virus_tab_exist : 
            self.tab_widget.setCurrentIndex(self.virus_tab_exist)
        QtGui.QWidget.show(self)
        
class T_scan(QtCore.QThread):
    """
    Scan Thread
    """
    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.clamav_instance = False
        self.mutex_running = threading.Lock()
        self.action = -1
        self.start(QtCore.QThread.LowestPriority)
        
    def run(self):
        while(True):
            if not self.clamav_instance:
                
                self.clamav_instance = myclam.Py_Clamav(self.inform)
            {
             - 1:lambda :time.sleep(5),
             'scan':self.__scan
             }[self.action]()
            
        
    def __virus_detected(self, file_name, virus_name):
        """
        Callback when virus is detected
        """
        self.emit(QtCore.SIGNAL("virus_detected(QString,QString)"), file_name, virus_name)
        
    def __scan(self):
        """
        scan method
        """
        self.mutex_running.acquire()
        self.running = True
        self.mutex_running.release()
        
        self.action = -1
         
        for one in self.to_scan:
            self.mutex_running.acquire()
            if not self.running :         
                self.mutex_running.release()
                break
            self.mutex_running.release()
            self.clamav_instance.scan(one, self.normal_print, self.virus_print)
            
        self.emit(QtCore.SIGNAL("scan_end_signal"))
        
    def launch_scan(self, to_scan, normal_print, virus_print):
        """
        launch scan 
        to_scan list of path to scan
        """
        self.normal_print = normal_print
        self.virus_print = self.__virus_detected
        self.to_scan = to_scan
        self.mutex_running.acquire()
        if not self.isRunning():
            self.start(QtCore.QThread.LowestPriority)
            
        self.action = 'scan'
        self.mutex_running.release()
        
    def stop_scan(self):
        """
        Manual stop scan
        """
        self.mutex_running.acquire()
        if self.isRunning():
            self.clamav_instance.stop_scan()
            self.running = False
            
            self.inform("Stop Scanning asked")
            
        self.mutex_running.release()
    
    def inform(self, message):
        """
        CallBack for showing information
        """
        self.emit(QtCore.SIGNAL("inform(QString)"), message)


class TestForm(QtGui.QMainWindow):
    def __init__(self, parent=None):
        self.antivirus = None
        QtGui.QWidget.__init__(self, parent)
        self.launch_button = QtGui.QPushButton("Anti-Virus")
        self.connect(self.launch_button, QtCore.SIGNAL('clicked()'), self.launch_AV)
        
        self.layout = QtGui.QVBoxLayout()
        container = QtGui.QWidget()
        container.setLayout(self.layout)
        self.layout.addWidget(self.launch_button)
        self.setCentralWidget(container)
    
    def launch_AV(self):
        if self.antivirus == None:
            self.antivirus = Antivirus(self)
            self.antivirus.show()
        else:
            self.antivirus.show()
    def addCustomWidget(self, widget):
        self.layout.addWidget(widget)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    w = TestForm()
    w.show()
    sys.exit(app.exec_())


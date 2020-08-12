import os
import threading
from platform import system
import re
import requests
import zipfile
import json
from PyQt5 import QtCore, QtGui, QtWidgets

row_count = 0


if system() == 'Windows':
    appdata = os.environ['APPDATA']
    appdata = appdata.replace('C:', '').replace('\\', '/')
    for folder in os.listdir(appdata):
        if "minecraft" in folder:
            mine_dir = appdata + "/.minecraft"
        else:
            # some kind of error message
            mine_dir = appdata
elif system() == 'Linux':
    userhome = os.path.expanduser('~')
    for folder in os.listdir(userhome):
        if "minecraft" in folder:
            mine_dir = userhome + "/.minecraft"
        else:
            # some kind of error message
            mine_dir = userhome
elif system() == 'Darwin':
    userhome = os.path.expanduser('~')
    userhome = userhome + "/Library/Application Support"
    for folder in os.listdir(userhome):
        if "minecraft" in folder:
            mine_dir = userhome + "/minecraft"
        else:
            # some kind of error message
            mine_dir = userhome
else:
    # some kind of error message
    mine_dir = "/"

class Load_Profile(QtCore.QThread):
    lp_sig1 = QtCore.pyqtSignal(str, str, str)
    lp_sig2 =QtCore.pyqtSignal()

    def __init__(self, profile, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.prof = profile
        # self.run(self.prof)

    def run(self):
        profile = self.prof
        # print(cur_dir)
        # cur_dir = cur_dir + "/"
        # file_path = os.path.join(cur_dir, file)
        with open(profile, 'r') as openfile:
            mod_json = json.load(openfile)
        mod_dir = mod_json[0]['mod_dir']
        # print(mod_json)
        for mod in mod_json:
            if "mod_dir" in mod:
                continue
            else:
                self.lp_sig1.emit(mod_dir, mod['name'], mod['filename'])
        self.lp_sig2.emit()
        return

class Ui_Dialog(object):
    dia_sig = QtCore.pyqtSignal(str, str)
    dia_sig2 = QtCore.pyqtSignal(str)
    cd_var = None

    def Dia_setupUi(self, Dialog, profiles, cur_dir):
        # self.profiles = profiles
        Dialog.setObjectName("Dialog")
        Dialog.resize(276, 247)
        # self.setWindowFlags(None, Qt.Dialog | WindowTitleHint)
        Dialog.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(10, 215, 256, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.listWidget = QtWidgets.QListWidget(Dialog)
        self.listWidget.setGeometry(QtCore.QRect(10, 20, 256, 192))
        self.listWidget.setObjectName("listWidget")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(10, 5, 80, 13))
        self.label.setObjectName("label")
        self.cd_var = cur_dir
        # self.file_var = file

        self.Dia_retranslateUi(Dialog, profiles)
        # self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.accepted.connect(self.button_test)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def Dia_retranslateUi(self, Dialog, profiles):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Profile Menu"))
        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        for profile in profiles:
            item = QtWidgets.QListWidgetItem(profile)
            self.listWidget.addItem(item)
        self.listWidget.setSortingEnabled(__sortingEnabled)
        self.label.setText(_translate("Dialog", "Choose a Profile:"))

    def button_test(self):
        item = self.listWidget.currentItem().text()
        # print(item)
        # print(self.cd_var)
        # print(self.file_var)
        profile = self.cd_var + "/" + item + ".json"
        # print(profile)
        self.lp = Load_Profile(profile)
        self.lp.lp_sig1.connect(self.call_back)
        self.lp.lp_sig2.connect(self.close_dia)
        self.lp.start()

    def call_back(self, mod_dir, mod_name, mod_file):
        # print(mod_name)
        self.dia_sig.emit(mod_name, mod_file)
        self.dia_sig2.emit(mod_dir)

    def close_dia(self):
        self.close()

class Dialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, profiles, cur_dir, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.Dia_setupUi(self, profiles, cur_dir)

class Scan_Mods(QtCore.QThread):
    sig1 = QtCore.pyqtSignal(str, str)
    sig2 = QtCore.pyqtSignal(str)
    sig3 = QtCore.pyqtSignal(int, list)
    sig4 = QtCore.pyqtSignal(list)
    sig5 = QtCore.pyqtSignal(bool, object, object)
    sig6 = QtCore.pyqtSignal(bool)

    def __init__(self, m_d, test_prot, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.mod_dir = m_d
        self.test_prot = test_prot
        # self.run(self.mod_dir)

    def run(self):
        mod_dir = self.mod_dir
        if self.test_prot:
            mod_count = 0
        not_found = []
        json_list = []
        mod_count = len([mod for mod in os.listdir(mod_dir) if mod.endswith(".jar")])
        self.sig5.emit(False, mod_count, None)
        for mod in os.listdir(mod_dir):
            if mod.endswith(".jar"):
                if self.test_prot:
                    mod_count = mod_count + 1
                if self.test_prot and mod_count == 4:
                    return
                mod_fp = os.path.join(mod_dir, mod)
                archive = zipfile.ZipFile(mod_fp, 'r')
                zip_list = archive.namelist()
                no_mod_nfo = True
                for file in zip_list:
                    if "mcmod.info" in file:
                        no_mod_nfo = False
                        mcmod = archive.read('mcmod.info')
                        mcmod = mcmod.decode("utf-8")
                        name = re.search('("name" ?: ".+")|("name" ?: ".+:.+")', mcmod)
                        name = name.group()
                        mod_name = name.replace('name', '').replace(':', '').replace('"', '').replace(' ', '', 1)
                        self.sig5.emit(False, None, mod_name)
                        version = re.search(r'"mcversion" ?: "\d?\.\d{1,2}\.?\d{0,2}"', mcmod)
                        if version:
                            version = version.group(0)
                            version = version.split(':')
                            mod_version = version[1].replace('"', '')
                            mod_version = mod_version.replace(' ', '', 1)
                            # print(mod_name)
                            mod_info = self.mod_id_lookup(mod_name, mod)
                            if not json_list:
                                json_dict = {"mod_dir": mod_dir}
                                json_list.append(json_dict)
                            if "not_found" in mod_info:
                                json_dict = {"name": mod_name, "version": mod_version, "id": "not_found",
                                             "filename": mod}
                                mod_id = "not_found"
                                # self.add_rows(mod_name, mod_version, mod_id, mod)
                                self.sig1.emit(mod_name, mod)
                                self.sig5.emit(True, None, None)
                            elif mod_info == "error":
                                self.sig2.emit(mod_info)
                                return
                            else:
                                json_dict = {"name": mod_info[0], "version": mod_version, "id": mod_info[1],
                                             "filename": mod}
                                # self.add_rows(mod_info[0], mod_version, mod_info[1], mod)
                                self.sig1.emit(mod_info[0], mod)
                                self.sig5.emit(True, None, None)
                            json_list.append(json_dict)
                        else:
                            mod_info = self.mod_id_lookup(mod_name, mod)
                            if "not_found" in mod_info:
                                json_dict = {"name": mod_name, "version": "", "id": "not_found", "filename": mod}
                                md_vers = ""
                                md_id = "not_found"
                                # self.add_rows(mod_name, md_vers, md_id, mod)
                                self.sig1.emit(mod_name, mod)
                                self.sig5.emit(True, None, None)
                            else:
                                json_dict = {"name": mod_info[0], "version": "", "id": mod_info[1], "filename": mod}
                                md_vers = ""
                                # self.add_rows(mod_info[0], md_vers, mod_info[1], mod)
                                self.sig1.emit(mod_info[0], mod)
                                self.sig5.emit(True, None, None)
                            json_list.append(json_dict)
                if no_mod_nfo:
                    not_found.append(mod)
                    self.sig5.emit(True, None, None)
        if not_found:
            nf_cnt = len(not_found)
            not_found_dict = {"noID":not_found}
            json_list.append(not_found_dict)
            self.sig3.emit(nf_cnt, not_found)
        self.sig4.emit(json_list)

    def mod_id_lookup(self, mod_name, mod):
        # print(mod_name)
        user_agent = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        mod_file = mod
        search_url_1 = "https://addons-ecs.forgesvc.net/api/v2/addon/search?gameId=432&pageSize=255&searchFilter="
        mod_url = "https://addons-ecs.forgesvc.net/api/v2/addon/"
        search_url_2 = search_url_1 + mod_name
        # print(search_url_1)
        response = requests.get(search_url_2, headers=user_agent)
        # print(response)
        if response.status_code != 200:
            # print(response.status_code)
            return "error"
        data1 = response.json()
        tmp_list = []
        pos_mm = True  # pos_mm = possible mismatch
        # searching for mod send 1
        for index, name in enumerate(data1):
            m_n = name['name']
            if m_n == mod_name:
                # mod found send 2
                pos_mm = False
                mod_id = name['id']
                tmp_list.append(m_n)
                tmp_list.append(str(mod_id))
                return tmp_list
        if pos_mm:
            if ' ' in mod_name:
                mod_name_s = mod_name.split(' ', 2)
                new_len = len(mod_name_s[0])
                if new_len < 5:
                    mod_name_s = mod_name_s[0] + " " + mod_name_s[1]
                else:
                    mod_name_s = mod_name_s[0]
                mod_name = mod_name_s
            else:
                str_len = len(mod_name)
                if str_len >= 12:
                    new_len = round(str_len / 3)
                elif str_len > 4:
                    new_len = round(str_len / 2)
                else:
                    new_len = str_len
                mod_name = mod_name[0:new_len]
            mod_search_url = search_url_1 + mod_name
            response = requests.get(mod_search_url, headers=user_agent)
            data1 = response.json()
            m_f = False  # mod found
            break1 = False
            for name in data1:
                mod_id = name['id']
                print(mod_id)
                m_n = name['name']
                new_search = mod_url + str(mod_id) + "/files"
                print(new_search)
                response = requests.get(new_search, headers=user_agent)
                if response.status_code != 200:
                    # break1 = True
                    return "error" # response.status_code
                data2 = response.json()
                for file in data2:
                    filename = file['fileName']
                    if filename == mod_file:
                        # mod found send 2
                        tmp_list.append(m_n)
                        tmp_list.append(str(mod_id))
                        # break1 = True
                        m_f = True
                        return tmp_list
                    # if break1:
                    #     break
                # if break1:
                #     break
            if not m_f:
                # still send 2
                tmp_list.append("not_found")
                return tmp_list

    # def run(self):
    #     cur_dir = os.path.dirname(os.path.realpath(__file__))
    #     cur_dir = cur_dir.replace('C:', '').replace('\\', '/')
    #     for file in os.listdir(cur_dir):
    #         if file.endswith(".json"):
    #             cur_dir = cur_dir + "/"
    #             file_path = os.path.join(cur_dir, file)
    #             with open(file_path, 'r') as openfile:
    #                 mod_json = json.load(openfile)
    #             if mod_json[0]['mod_dir'] == mod_dir:
    #                 for mod in mod_json:
    #                     if "mod_dir" in mod:
    #                         continue
    #                     else:
    #                         self.add_rows(mod['name'], mod['version'], mod['filename'])
                            # self.lp_sig1.emit(mod['name'], mod['filename'])
                    # return

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(795, 581)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../mine_updater_icon_sm.ico"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        MainWindow.setWindowIcon(icon)
        self.not_found = ""
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(690, 160, 101, 23))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(690, 130, 101, 23))
        self.pushButton_2.setObjectName("pushButton_2")
        self.incr = 0
        self.max_prog = 0
        self.pushButton_2.clicked.connect(self.scan_mods)
        self.pushButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_3.setGeometry(QtCore.QRect(690, 220, 101, 23))
        self.pushButton_3.setObjectName("pushButton_3")
        # self.pushButton_3.clicked.connect(self.profile_name)
        self.pushButton_4 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_4.setGeometry(QtCore.QRect(690, 190, 101, 23))
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_5 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_5.setGeometry(QtCore.QRect(660, 20, 25, 23))
        self.pushButton_5.setObjectName("toolButton")
        self.pushButton_5.clicked.connect(self.get_dir)
        self.pushButton_6 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_6.setGeometry(QtCore.QRect(690, 100, 101, 23))
        self.pushButton_6.setObjectName("pushButton_6")
        self.pushButton_6.clicked.connect(self.pick_profile)
        self.pushButton_7 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_7.setGeometry(QtCore.QRect(690, 70, 101, 23))
        self.pushButton_7.setObjectName("pushButton_7")
        self.pushButton_7.clicked.connect(self.clear_table)
        self.pushButton_8 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_8.setGeometry(QtCore.QRect(5, 47, 65, 19))
        self.pushButton_8.setObjectName("pushButton_8")
        self.btn_st = None
        self.pushButton_8.clicked.connect(self.sel_all)
        self.pushButton_9 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_9.setGeometry(QtCore.QRect(234, 47, 25, 19))
        self.pushButton_9.setObjectName("pushButton_9")
        self.pushButton_9.clicked.connect(self.get_checked)
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.setGeometry(QtCore.QRect(125, 47, 105, 19))
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(5, 508, 681, 20))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.hide()
        self.progressBar_1 = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar_1.setGeometry(QtCore.QRect(5, 505, 716, 12))
        self.progressBar_1.setProperty("value", 0)
        self.progressBar_1.setObjectName("progressBar_1")
        self.progressBar_1.hide()
        self.progressBar_2 = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar_2.setGeometry(QtCore.QRect(5, 532, 716, 12))
        self.progressBar_2.setProperty("value", 0)
        self.progressBar_2.setObjectName("progressBar_2")
        self.progressBar_2.hide()
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(5, 530, 671, 16))
        self.label.setObjectName("label")
        self.label.hide()
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QtCore.QRect(5, 70, 681, 431))
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setRowCount(row_count)
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        #item = QtWidgets.QTableWidgetItem()
        #self.tableWidget.setVerticalHeaderItem(0, item)
        #item = QtWidgets.QTableWidgetItem()
        #self.tableWidget.setVerticalHeaderItem(1, item)
        #item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderLabels(['Mod Name', 'Current', 'Update', 'Changelog'])
        #item = QtWidgets.QTableWidgetItem()
        #self.tableWidget.setHorizontalHeaderItem(1, item)
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(5, 20, 651, 23))
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setReadOnly(False)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(6, 3, 71, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(690, 263, 31, 16))
        self.label_3.setObjectName("label_3")
        self.label_3.hide()
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(750, 263, 21, 16))
        self.label_4.setObjectName("label_4")
        self.label_4.hide()
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(690, 280, 47, 13))
        self.label_5.setObjectName("label_5")
        self.label_5.hide()
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(750, 279, 41, 16))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
        self.label_6.setPalette(palette)
        self.label_6.setObjectName("label_6")
        self.label_6.hide()
        self.label_7 = QtWidgets.QLabel(self.centralwidget)
        self.label_7.setGeometry(QtCore.QRect(80, 50, 47, 13))
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(self.centralwidget)
        self.label_8.setGeometry(QtCore.QRect(690, 250, 47, 13))
        self.label_8.setObjectName("label_8")
        self.label_8.hide()
        self.label_9 = QtWidgets.QLabel(self.centralwidget)
        self.label_9.setGeometry(QtCore.QRect(750, 250, 47, 13))
        self.label_9.setObjectName("label_9")
        self.label_9.hide()
        self.label_10 = QtWidgets.QLabel(self.centralwidget)
        self.label_10.setGeometry(QtCore.QRect(5, 542, 681, 16))
        self.label_10.setObjectName("label_10")
        self.label_10.hide()
        self.label_11 = QtWidgets.QLabel(self.centralwidget)
        self.label_11.setGeometry(QtCore.QRect(5, 515, 681, 16))
        self.label_11.setObjectName("label_11")
        self.label_11.hide()
        self.label_12 = QtWidgets.QLabel(self.centralwidget)
        self.label_12.setGeometry(QtCore.QRect(5, 532, 681, 16))
        self.label_12.setObjectName("label_12")
        self.label_12.hide()
        self.label_6.mousePressEvent = self.no_ID_msg
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 795, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.actionLoad_Profile = QtWidgets.QAction(MainWindow)
        # self.actionLoad_Profile.setObjectName("actionLoad_Profile")
        self.actionClear_Cache = QtWidgets.QAction(MainWindow)
        self.actionClear_Cache.setObjectName("actionClear_Cache")
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        # self.menuFile.addAction(self.actionLoad_Profile)
        self.menuFile.addAction(self.actionClear_Cache)
        self.menuFile.addAction(self.actionExit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Minecraft Mod Updater"))
        self.pushButton_6.setText(_translate("MainWindow", "Load Profile"))
        self.pushButton_2.setText(_translate("MainWindow", "Scan Mods"))
        self.pushButton.setText(_translate("MainWindow", "Check for Update"))
        self.pushButton_3.setText(_translate("MainWindow", "Restore"))
        self.pushButton_4.setText(_translate("MainWindow", "Update"))
        self.pushButton_5.setText(_translate("MainWindow", "..."))
        self.pushButton_7.setText(_translate("MainWindow", "Clear"))
        self.pushButton_8.setText(_translate("MainWindow", "Select All"))
        self.pushButton_9.setText(_translate("MainWindow", "Go"))
        self.comboBox.setItemText(0, _translate("MainWindow", "All"))
        self.comboBox.setItemText(1, _translate("MainWindow", "Update Available"))
        self.label_7.setText(_translate("MainWindow", "Filter by:"))
        self.label.setText(_translate("MainWindow", "TextLabel"))
        #item = self.tableWidget.verticalHeaderItem(0)
        #item.setText(_translate("MainWindow", "New Row"))
        #item = self.tableWidget.verticalHeaderItem(1)
        #item.setText(_translate("MainWindow", "New Row"))
        #item = self.tableWidget.horizontalHeaderItem(0)
        #item.setText(_translate("MainWindow", "New Column"))
        #item = self.tableWidget.horizontalHeaderItem(1)
        #item.setText(_translate("MainWindow", "New Column"))
        self.label_2.setText(_translate("MainWindow", "Mod Directory:"))
        self.label_3.setText(_translate("MainWindow", "Mods:"))
        self.label_4.setText(_translate("MainWindow", "0"))
        self.label_5.setText(_translate("MainWindow", "Not ID\'d:"))
        self.label_6.setText(_translate("MainWindow", "0"))
        self.label_8.setText(_translate("MainWindow", "MC Vers:"))
        self.label_9.setText(_translate("MainWindow", "1.12.2"))
        self.label_11.setText(_translate("MainWindow", "Prog1"))
        self.label_10.setText(_translate("MainWindow", "Prog2"))
        self.label_12.setText(_translate("MainWindow", "Prog1_2"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        # self.actionLoad_Profile.setText(_translate("MainWindow", "Load Profile"))
        self.actionClear_Cache.setText(_translate("MainWindow", "Clear Cache"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))

    def sel_all(self):
        if self.btn_st:
            self.pushButton_8.setText("Select All")
            self.btn_st = None
            for i in range(self.tableWidget.rowCount()):
                self.tableWidget.item(i, 0).setCheckState(QtCore.Qt.Unchecked)
        else:
            self.pushButton_8.setText("Deselect All")
            self.btn_st = True
            for i in range(self.tableWidget.rowCount()):
                self.tableWidget.item(i, 0).setCheckState(QtCore.Qt.Checked)

    def pick_profile(self):
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        cur_dir = cur_dir.replace('C:', '').replace('\\', '/')
        profiles = []
        no_profiles = True
        for file in os.listdir(cur_dir):
            if file.endswith(".json"):
                no_profiles = False
                profile = file.replace('.json', '')
                profiles.append(profile)
        if no_profiles:
            self.no_profiles()
            return
        else:
            dia_show = Dialog(profiles, cur_dir)
            dia_show.dia_sig.connect(self.add_rows)
            dia_show.dia_sig2.connect(self.update_mod_dir)
            dia_show.exec_()

    def no_profiles(self):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle('Whoops')
        msg.setText("There are currently no modpack profiles available.")
        msg.exec()

    def update_mod_dir(self, mod_dir):
        self.lineEdit.setText(mod_dir)

    def add_rows(self, mod_name_var, installed_file):
        table = self.tableWidget
        rows = table.rowCount()
        table.insertRow(rows)
        mod_name = QtWidgets.QTableWidgetItem(mod_name_var)
        mod_name.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        mod_name.setCheckState(QtCore.Qt.Unchecked)
        # mine_vers = QtWidgets.QTableWidgetItem(mine_vers)
        installed_file = QtWidgets.QTableWidgetItem(installed_file)
        # new_file = QtWidgets.QTableWidgetItem(new_file)
        # changelog = QtWidgets.QTableWidgetItem(changelog)
        table.setItem(rows, 0, mod_name)
        # table.setItem(rows, 1, mine_vers)
        table.setItem(rows, 1, installed_file)
        # table.setItem(rows, 3, new_file)
        # table.setItem(rows, 4, changelog)
        rows = table.rowCount()
        if not self.label_4.isVisible():
            self.label_3.show()
            self.label_4.show()
        self.label_4.setText(str(rows))
        # table.resizeColumnsToContents()
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

    def scan_mods(self):
        test_prot = False           # used to test mod finding; stops at the 3rd mod
        mod_dir = self.lineEdit.text()
        self.scanmods = Scan_Mods(mod_dir, test_prot)
        self.scanmods.sig1.connect(self.add_rows)
        self.scanmods.sig2.connect(self.conn_err)
        self.scanmods.sig3.connect(self.no_ID)
        self.scanmods.sig4.connect(self.profile_name)
        self.scanmods.sig5.connect(self.update_prog_1)
        self.scanmods.start()

    def conn_err(self):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setWindowTitle('Error')
        msg.setText("Error contacting server.\n\nMake sure you have an internet connection.")
        msg.exec()

    def profile_name(self, json_list):
        p_name, okPressed = QtWidgets.QInputDialog.getText(None, "New Profile", "Profile name:",
                                                           QtWidgets.QLineEdit.Normal, "")
        if not okPressed or not p_name:
            while True:
                qm = QtWidgets.QMessageBox()
                ret = qm.question(None, 'Aww man...', "Without a profile name, you will have to rescan\nyour mod "
                                                      "folder everytime.\n\nAre you sure you want to continue without "
                                                      "one?", qm.Yes | qm.No)
                if ret == qm.Yes:
                    return
                else:
                    p_name, okPressed = QtWidgets.QInputDialog.getText(None, "New Profile", "Profile name:",
                                                                       QtWidgets.QLineEdit.Normal, "")
                    if okPressed and p_name:
                        break
        if json_name:
            self.create_json(p_name, json_list)

    def create_json(self, p_name, json_list):
        # print(json_list)
        filename = p_name + ".json"
        json_obj = json.dumps(json_list, indent=4)
        with open(filename, "w") as outfile:
            outfile.write(json_obj)

    def no_ID(self, nf_cnt, not_found):
        self.label_6.setText(str(nf_cnt))
        self.label_5.show()
        self.label_6.show()
        self.not_found = not_found

    def no_ID_msg(self, Event):
        nf_str = ""
        for item in self.not_found:
            if nf_str:
                nf_str = nf_str + "\n" + item
            else:
                nf_str = item
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle('Whoops')
        msg.setText("These mods could not be identified:\n\n" + nf_str + "\n\nYou can add them to the JSON or update "
                                                                         "them manually.")
        msg.exec()

    def get_dir(self):
        f_d = QtWidgets.QFileDialog
        mod_dir = str(f_d.getExistingDirectory(None, "Select Directory", mine_dir))
        mod_dir = mod_dir.replace('C:', '')
        self.lineEdit.setText(mod_dir)

    def update_prog_1(self, prog_i, max_prog="", mod_name=""):
        if max_prog:
            self.max_prog = max_prog
            self.progressBar_1.setMaximum(self.max_prog)
        self.progressBar_1.show()
        self.label_11.show()
        if mod_name:
            self.label_11.setText(mod_name)
            mod_name = None
        if prog_i == True:
            self.incr = self.incr + 1
            self.progressBar_1.setValue(self.incr)
        pass

    def clear_table(self):
        table = self.tableWidget
        table.clearContents()
        table.setRowCount(0)
        self.lineEdit.setText("")
        self.label_3.hide()
        self.label_4.setText("")
        self.label_4.hide()
        self.label_5.hide()
        self.label_6.setText("")
        self.label_6.hide()
        self.tableWidget.resizeColumnsToContents()

    def get_checked(self):
        checked_list = []
        for i in range(self.tableWidget.rowCount()):
            # print(self.tableWidget.rowCount())
            if self.tableWidget.item(i, 0).checkState() == QtCore.Qt.Checked:
                # checked_list.append([i, 0])
                print(self.tableWidget.item(i, 0).text())
            else:
                print("nope")
        # print(checked_list)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

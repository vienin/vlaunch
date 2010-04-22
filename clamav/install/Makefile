#COMMAND
PYTHON=C:\Python26\python.exe
MINGW=C:\MinGW\bin\

#SWIG
SWIG=C:\swigwin-1.3.40\swig.exe
SWIG_FILE=clamav.i
SWIG_OPTIONS= -threads -python 
CLAMAV_LIB=C:\clamav-devel\libclamav
CLAMAV_RELEASE=C:\clamav-devel\win32\Release

#DISTUTILS
SETUP_FILE=setup.py
SETUP_OPTIONS=

#OS COMMAND
RM = del /Q /S
RM_DIR = rmdir /S /Q 
CP = copy /Y
MV = move
MKDIR = mkdir

#OTHER 
MODULE_NAME = custom_clamav
SRC_DIR = ..\src
UPDATE_DIR = update
UPDATE_CD_DIR = update_cd
MAIN_CVD = X:\clamav-dll\myclam\update_cd\main.cvd
DAILY_CVD = X:\clamav-dll\myclam\update_cd\daily.cvd
all: clean build

build:
	@echo build
	$(CP) $(CLAMAV_LIB)\clamav.h /y
	$(CP) $(CLAMAV_RELEASE)\libclamav.lib /y
	$(CP) $(CLAMAV_RELEASE)\libclamunrar.lib /y
	$(CP) $(CLAMAV_RELEASE)\libclamav.dll /y
	$(CP) $(CLAMAV_RELEASE)\libclamunrar.dll /y
	$(SWIG) $(SWIG_OPTIONS) $(SWIG_FILE)
	$(PYTHON) $(SETUP_FILE) build_ext -I $(CLAMAV_LIB);$(CLAMAV_RELEASE) --inplace --plat-name win32
	$(MKDIR) $(SRC_DIR)\$(MODULE_NAME)
	$(MKDIR) $(SRC_DIR)\$(UPDATE_DIR)
	$(MKDIR) $(SRC_DIR)\$(UPDATE_CD_DIR)
	@echo ''>$(SRC_DIR)\$(MODULE_NAME)\__init__.py
	$(CP) clamav.py $(SRC_DIR)\$(MODULE_NAME)
	$(CP) _clamav.pyd $(SRC_DIR)\$(MODULE_NAME)
	$(CP) libclamav.dll $(SRC_DIR)\$(MODULE_NAME)
	$(CP) libclamunrar.dll $(SRC_DIR)\$(MODULE_NAME)
	$(CP) $(MAIN_CVD) $(SRC_DIR)\$(UPDATE_CD_DIR)
	$(CP) $(DAILY_CVD) $(SRC_DIR)\$(UPDATE_CD_DIR)
	@$(RM) *.h clamav.py *.c *.lib *.pyd *.swp *.dll
	@$(RM_DIR) build
	
clean:
	@$(RM_DIR) $(SRC_DIR)\$(MODULE_NAME)
	@$(RM_DIR) $(SRC_DIR)\$(UPDATE_DIR)
	@$(RM_DIR) $(SRC_DIR)\$(UPDATE_CD_DIR)
	@echo clean
	@$(RM) *.h 
	@$(RM) clamav.py
	@$(RM) *.c
	@$(RM) *.lib 
	@$(RM) *.pyd 
	@$(RM) *.swp 
	@$(RM) *.dll
	@$(RM) *.pyc
	@$(RM_DIR) build


	
	
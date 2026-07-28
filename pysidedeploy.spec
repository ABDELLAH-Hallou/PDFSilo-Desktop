[app]

# pdfsilo's checked-in windows deployment configuration.
title = PDFSilo
project_dir = .
input_file = pdfsilo\ui\main.py
exec_directory = dist/windows
project_file = 
icon = packaging/windows/pdfsilo.ico

[python]
python_path = venv\Scripts\python.exe
packages = Nuitka==4.1.3,ordered-set==4.1.0,zstandard==0.25.0
android_packages = buildozer==1.5.0,cython==0.29.33

[qt]
qml_files = 
excluded_qml_plugins = 
modules = Core,Gui,Widgets

# nuitka includes its sensible desktop plug-ins by default. this additional
# family is the only dependency retained by pyside6-deploy after filtering.
plugins = platforminputcontexts

[android]
wheel_pyside = 
wheel_shiboken = 
plugins = 

[nuitka]
macos.permissions = 
mode = standalone
extra_args = --quiet --assume-yes-for-downloads --low-memory --lto=no --windows-console-mode=disable --output-filename=PDFSilo.exe --include-package-data=pdfsilo.ui.resources --company-name="Abdellah HALLOU" --product-name=PDFSilo --file-description="Privacy-first local PDF toolkit" --file-version=0.1.0.0 --product-version=0.1.0.0 --copyright="Copyright (c) 2026-present Abdellah HALLOU"

[buildozer]
mode = debug
recipe_dir = 
jars_dir = 
ndk_path = 
sdk_path = 
local_libs = 
arch = 


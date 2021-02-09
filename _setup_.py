# coding: utf-8

from cx_Freeze import setup, Executable
import sys,os,shutil

build_exe1=os.path.join(os.curdir,'B2B_Exchange')

try:
    os.mkdir(build_exe1)
except:
    pass


print (build_exe1)


base='win32' #'Win32GUI'
#base=None if sys.platform=='win32' else None

executables = [
            Executable('B2B_Exchange.py', targetName='B2B_Exchange.exe')
               ]

excludes = ['asyncio','concurrent','ctypes','distutils','html','lib2to3','multiprocessing','pydoc_data','test','tkinter','unittest','xml','xmlrpc']

zip_include_packages = ['certifi','chardet','collections','email','encodings','http','idna','importlib','json','logging','requests','urllib','urllib3','queue']
                                                

includes = [
    "queue"
            ]

packages = ["os", "requests","http.client","json"]

options = {
    'build_exe': {
        'include_msvcr': True
        ,'excludes': excludes
        ,'includes': includes
        ,'zip_include_packages': zip_include_packages
        ,'packages': packages
	,'build_exe': 'B2B_Exchange'
       ,'optimize':1
	}
}

setup(
      name='B2B Exchange',
      version='1.0',
      description='B2B Exchange ABI',
      executables=executables,
	  options=options
	  )

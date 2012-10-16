#!/usr/bin/env python

from sys import argv
from ConfigParser import SafeConfigParser
from ftldat import FTLDatUnpacker as du
from ftldat import FTLDatPacker as dp
from shutil import copy

import tempfile as tf
import easygui as eg
import zipfile as zf
import shutil as sh
import platform
import glob
import xml
import sys
import os

progname = "Grognak's Mod Manager v1.4"

if platform.system()=='Darwin':
   msg="Are you using Steam?"
   yn=["Yes","No"]
   steam=eg.choicebox(msg,progname,yn)
   dir_root=os.getcwd() + '/'
   if steam=='Yes':
       dir_res=os.path.join(os.environ['HOME'],'Library/Application Support/Steam/SteamApps/common/FTL Faster Than Light/FTL.app/Contents/resources')
   if steam=='No' or steam==None:
      app=eg.diropenbox(msg="Select your FTL app",title=progname)
      dir_res=os.path.join(app,'Contents/resources')
   os.chdir(dir_root)
   cfg=SafeConfigParser()
   cfg.read("modman.cfg")
   dir_mods=cfg.get("settings","macmodsdir")
   dir_mods=os.path.expanduser(dir_mods)
   if not os.path.exists(dir_mods):
      os.makedirs(dir_mods)
      #copy(os.path.join(dir_root,"mods/Beginning Scrap Advantage.ftl"),dir_mods)
      eg.msgbox("A folder has been created on "+dir_mods+" .Please put any FTL mods there.",progname)
   if os.path.exists(dir_mods):
      eg.msgbox("Your mod folder is located at "+dir_mods+" . Place any FTL mods there..",progname)
else:
   dir_root = dir_root = os.path.realpath(__file__)
   dir_mods = os.path.join(dir_root, "mods")
   dir_res = os.path.join(dir_root, "resources")

def ftl_path_join(*args):
    """ Joins paths in the way FTL expects them to be in .dat files.
        That is: the UNIX way. """
    return '/'.join(args)

def appendfile(src, dst):
    source = open(src, "r")
    target = open(dst, "a")
    
    target.write(source.read() + "\n")
    
    source.close()
    target.close()
    
def mergefile(src, dst):
    pass
    
def packdat(datafolder, datfile):
    print "\nRepacking " + datfile
    print 'Listing files to pack ...'
    s = [()]
    files = []
    while s:
        current = s.pop()
        for child in os.listdir(os.path.join(datafolder, *current)):
            full_path = os.path.join(datafolder,
                                        *(current + (child,)))
            if os.path.isfile(full_path):
                files.append(current + (child,))
            elif os.path.isdir(full_path):
                s.append(current + (child,))
    print 'Create datfile ...'
    indexSize = len(files)
    packer = dp(open(datfile, "wb"), indexSize)
    print 'Packing ...'
    for _file in files:
        full_path = os.path.join(datafolder, *_file)
        size = os.stat(full_path).st_size
        with open(full_path, 'rb') as f:
            packer.add(ftl_path_join(*_file), f, size)

def unpackdat(datafile):
    print "Unpacking %s..." % datafile
    unpacker = du(open(datafile, "rb"))
    
    for i, filename, size, offset in unpacker:
        target = os.path.join(datafile + "-unpacked", filename)
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        with open(target, 'wb') as f:
            unpacker.extract_to(filename, f)

# Verify that the user put GMM in the right location
if platform.system() == "Windows":
    if not os.path.isfile(os.path.join(dir_root, "FTLGame.exe")):
        eg.msgbox("Error: This executable must be in the same folder as FTLGame.exe", progname)
        sys.exit(0)
elif platform.system() == "Darwin":
    pass
elif platform.system() == "Linux":
    if not os.path.isfile(os.path.join(dir_root, "FTL")):
        eg.msgbox("Error: Grognak's Mod Manager must be located directly above the FTL folder.", progname)
        sys.exit(0)
else:
    eg.msgbox("Warning: Unsupported platform. Results may be unexpected.", progname)

# Load up config file values
cfg = SafeConfigParser()
cfg.read("modman.cfg")

allowzip = cfg.getboolean("settings", "allowzip")

print dir_root + "\n"

# Loop through the .ftl files, check if on mod list.
os.chdir(dir_mods)
modorder = open("modorder.txt", "a+")
modorder.seek(0)
modorder_read = modorder.readlines()

modorder_read = [word.strip() for word in modorder_read]

for f in glob.glob("*.ftl"):
    if not f in modorder_read:
        modorder.write(f + "\n")
        
if allowzip:
    for f in glob.glob("*.zip"):
        if not f in modorder_read:
            modorder.write(f + "\n")

# Refresh the list
modorder.seek(0)
modorder_read = modorder.readlines() 
modorder_read = [word.strip() for word in modorder_read]

# Mod list sans the .ftl extention
if allowzip:
    modname_list = modorder_read
else:
    modname_list = [word[:-4] for word in modorder_read]

# Gets list of mods the player wants to be patched in
msg = "Pick the modifications you'd like active:"
mergelist = eg.multchoicebox(msg, progname, modname_list)

# User clicked cancel
if (mergelist == None):
    sys.exit(0) 

# Create data file backups, if necessary
os.chdir(dir_res)

if not os.path.isfile("data.dat.bak"):
    print "Backing up data.dat"
    sh.copy2("data.dat", "data.dat.bak")
    
if not os.path.isfile("resource.dat.bak"):
    print "Backing up resource.dat\n"
    sh.copy2("resource.dat", "resource.dat.bak")
    
# Overwrite old data files with their respective backups
sh.copy2("data.dat.bak", "data.dat")
sh.copy2("resource.dat.bak", "resource.dat")
    
# Extract both of the backup files
unpackdat("data.dat")
unpackdat("resource.dat")

# Go through each .ftl archive and apply changes
tmp = tf.mkdtemp()
if allowzip:
    modlist = mergelist
else:
    modlist = [word + ".ftl" for word in mergelist]

for filename in modlist:
    os.chdir(dir_mods)
    ftl = zf.ZipFile(filename, 'r')
    
    print "\nInstalling " + filename
    
    # Unzip everything into a temporary folder
    for item in ftl.namelist():
        if item.endswith('/'):
            path = os.path.join(tmp, item)
            if not os.path.exists(path):
                os.makedirs(path)
        else:
            ftl.extract(item, tmp)
    
    # Go through each directory in the .ftl file
    for directory in os.listdir(tmp):
        if directory == "data":
            print " - Merging " + directory + " folder"
            for root, dirs, files in os.walk(os.path.join(tmp, directory)):
                for d in dirs:
                    path = os.path.join(dir_res, "data.dat-unpacked", root[len(tmp)+1:], d)
                    if not os.path.exists(path):
                        os.makedirs(path)
                for f in files:
                    if f.endswith(".append"):
                        appendfile(os.path.join(root, f), os.path.join(dir_res, "data.dat-unpacked", root[len(tmp)+1:], f[:-len(".append")]))
                    elif f.endswith(".merge"):
                        mergefile(os.path.join(root, f), os.path.join(dir_res, "data.dat-unpacked", root[len(tmp)+1:], f[:-len(".append")]))
                    else:
                        sh.copy2(os.path.join(root, f), os.path.join(dir_res, "data.dat-unpacked", root[len(tmp)+1:], f))
                    
        elif directory in ("audio", "fonts", "img"):
            print " - Merging " + directory + " folder"
            for root, dirs, files in os.walk(os.path.join(tmp, directory)):
                for d in dirs:
                    path = os.path.join(dir_res, "resource.dat-unpacked", root[len(tmp)+1:], d)
                    if not os.path.exists(path):
                        os.makedirs(path)
                for f in files:
                    if f.endswith(".append"):
                        appendfile(os.path.join(root, f), os.path.join(dir_res, "resource.dat-unpacked", root[len(tmp)+1:], f[:-len(".append")]))
                    else:
                        sh.copy2(os.path.join(root, f), os.path.join(dir_res, "resource.dat-unpacked", root[len(tmp)+1:], f))
                        
        else:
            print " - WARNING: Unsupported folder " + directory
        
    # Clean up temporary folder's contents
    for root, dirs, files in os.walk(tmp):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            sh.rmtree(os.path.join(root, d))
    
# All the mods are installed, so repack the files.
os.chdir(dir_res)
packdat("data.dat-unpacked", "data.dat")
packdat("resource.dat-unpacked", "resource.dat")
    
# All done!
eg.msgbox("Patching completed successfully", progname)
    

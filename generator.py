##############################################
# Darksoft Neogeo Romset Generator by Aluzed #
# 2020                                       #
##############################################

import os
import sys
import re
import io
import hashlib
import glob
from os import walk

dir_path = os.path.dirname(os.path.realpath(__file__))

if 1 in sys.argv:
  dir_path = sys.argv[1]

f = [] # List dir files
c_files = []
v_files = []
p_files = []
s_rom = m1_rom = ""

def clear_folder(folder_path):
  files = glob.glob(folder_path + os.path.sep + '**', recursive=True)
  for f in files:
    try:
        os.remove(f)
    except OSError as e:
        print("Error: %s : %s" % (f, e.strerror))

def concat_files(export_path, file_list):
  data = ""

  if len(file_list) > 0:
    with open(export_path, "ab") as exported_rom:
      for filename in file_list:
        with open(dir_path + os.path.sep + filename, "rb") as file2:
          print(filename + ' found')
          exported_rom.write(file2.read())
          file2.close()    
      exported_rom.close()

    with open(export_path, "rb") as exported_rom:
      data = exported_rom.read()

  return data

# CROM must be concat 2 per 2
def split_per2(export_path, collection):
  tmp_files = []
  iter_cache = []

  for item in collection:
    iter_cache.append(item)
    if len(iter_cache) > 0 and len(iter_cache) % 2 == 0:
      tmp_path = "out" + str(len(tmp_files)) + ".bin"
      join_crom0(dir_path + os.path.sep + tmp_path, iter_cache)
      tmp_files.append(tmp_path)
      iter_cache = []
  
  data = concat_files(export_path, tmp_files)
  clear_temp_files(tmp_files)

  return data

def clear_temp_files(collection):
  for item in collection:
    try:
        os.remove(dir_path + os.path.sep + item)
    except OSError as e:
        print("Error: %s : %s" % (f, e.strerror))

def copy_file(source, dest):
  with open(dest, "ab") as destination_file:
    with open(source, "rb") as source_file:
      destination_file.write(source_file.read())
      source_file.close()
    destination_file.close()

def convert_roms():
  global s_rom
  
  print('start rom conversion for ' + dir_path)

  for (dirpath, dirnames, filenames) in walk(dir_path):
    f.extend(filenames)
    break

  for filename in f:
    # Get S Rom
    if re.search(r'.s1$', filename) or re.search(r'[-_]s1.(rom|bin)', filename):
      s_rom = filename

    # Get M Rom
    if re.search(r'.m1$', filename) or re.search(r'[-_]m1.(rom|bin)$', filename):
      m1_rom = filename

    # Get P Roms
    if re.search(r'.p\d$', filename) or re.search(r'[-_]p\d.(rom|bin)$', filename):
      p_files.append(filename)

    # Get C Roms
    if re.search(r'[-_]c\d.(rom|bin)$', filename) or re.search(r'.c\d$', filename):
      c_files.append(filename)

    # Get V Roms
    if re.search(r'.v\d$', filename) or re.search(r'[-_]v\d.(rom|bin)$', filename):
      v_files.append(filename)

  # Second loop for SP files
  for filename in f:
    if re.search(r'.sp\d$', filename) or re.search(r'[-_]sp\d.(rom|bin)$', filename):
      p_files.append(filename)

  # Setting our export path
  export_path = dir_path + os.path.sep + "export"

  # Setting our SROM file path
  srom_path = export_path + os.path.sep + "srom"

  # Setting our M1ROM file path
  m1rom_path = export_path + os.path.sep + "m1rom"

  # Setting our CROM file path
  crom_path = export_path + os.path.sep + "crom0"

  # Setting our VROM file path
  vrom_path = export_path + os.path.sep + "vroma0"

  # Setting our PROM file path
  prom_path = export_path + os.path.sep + "prom"

  # Cascading make dir
  if not os.path.exists(export_path):
    os.makedirs(export_path)
  else:
    clear_folder(export_path)

  # Handle S file
  if s_rom != "":
    copy_file(dir_path + os.path.sep + s_rom, srom_path)

  # Handle M1 file
  if m1_rom != "":
    copy_file(dir_path + os.path.sep + m1_rom, m1rom_path)

  # Handle C files
  data = split_per2(crom_path, c_files)
  
  if data == "":
    print('something went wrong parsing c files')
  else:
    print('crom0 generated with SHA256 checksum : ' + hashlib.sha256(data).hexdigest())
    print('crom0 generated with SHA1 checksum : ' + hashlib.sha1(data).hexdigest())
    print('crom0 generated with MD5 checksum : ' + hashlib.md5(data).hexdigest())

  # Handle V files
  data = concat_files(vrom_path, v_files)

  if data == "":
    print('something went wrong parsing v files')
  else:
    print('vroma0 generated with SHA256 checksum : ' + hashlib.sha256(data).hexdigest())
    print('vroma0 generated with SHA1 checksum : ' + hashlib.sha1(data).hexdigest())
    print('vroma0 generated with MD5 checksum : ' + hashlib.md5(data).hexdigest())

  # Handle P files
  data = concat_files(prom_path, p_files)
  
  if data == "":
    print('something went wrong parsing v files')
  else:
    print('prom generated with SHA256 checksum : ' + hashlib.sha256(data).hexdigest())
    print('prom generated with SHA1 checksum : ' + hashlib.sha1(data).hexdigest())
    print('prom generated with MD5 checksum : ' + hashlib.md5(data).hexdigest())

def join_crom0(export_path, files):
  print(files)
  inputs = []

  # Stop computing if array is empty
  if len(files) == 0:
    return None

  for f in files:
    fp = open(f, "rb")
    inputs.append(fp)

  output = open(export_path,"wb")

  breakable = False

  while breakable is False:
    datarows = []

    # Read 2 bytes from each file
    for fp in inputs:
      data = fp.read(2)
      if not data: 
        breakable = True
      else:
        if breakable is False:
          datarows.append(data)

    # now inser them into the merged crom 
    if breakable is False:
      for d in datarows:
        output.write(d)

  # close our new file
  output.close()

# Launch /!\ 
try:
    convert_roms()
except:
    print (sys.exc_info()[0])
    raise

print('job done, press a key to exit...')
input()
#######################################
# Get File Hash by Aluzed             #
# 2020                                #
#######################################

import hashlib, sys

if len(sys.argv) != 3:
  print('Error must have 2 args : python get_hash.py <algo> <filename>')
  exit(1)

algo = sys.argv[1]
filename = sys.argv[2]

func = getattr(hashlib, algo)

if func is not None:
  print(func(open(filename, 'rb').read()).hexdigest())
  
input()
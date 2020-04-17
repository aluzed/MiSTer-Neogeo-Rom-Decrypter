# Darksoft Neogeo Rom generator for MiSTer-FPGA by Aluzed

Use decrypted **NeorageX** rom to get it working. 

Unzip the rom, add **generator.py** to the folder and execute with python : 
```
python.exe (or python3 on linux/mac) generator.py
```

It generates an extract folder, that you can add to your MiSTer-FPGA SD card.
Don't forget to rename the folder, to the correct game name in **romset.sample.xml**

# Tools

I added another python tool that is get_hash.py, to check the game checksum and see if everything is ok.

How to use 

```
python.exe get_hash.py <algo> <filename>
```

List of available algo(in lower case) : 
* sha256
* sha1 
* md5

Compare your checksum with the one in **"Darksoft Neo Geo SMDB.txt"** file that I grabbed from Everdrive github.

Here is the file organisation (line per line) : 
```
<SHA256> <filename> <SHA1> <MD5> <CRC>
```

If your checksum matches with the DB file, then your rom is well generated.

For the FPGA file, it contains the key of the starting index. For any game you convert, you must have a fpga file in your rom folder. 
Now to figure out what is the index for your current rom, check the **"Darksoft Neo Geo SMDB.txt"** file, look at the current rom **fpga** file line.
Then grab your md5 hash for your **fpga** file. 

Now use a reverse MD5 database (on Google or whatever) and paste your MD5 hash, you should get the key (it looks like "10" or "25"... it is a number).
Just create your **fpga** file with the number inside.

The you are ready to go, copy/paste your folder to your SD card.

# Finally

Add a line into your **romset.xml** corresponding to the **romset.sample.xml** line of your rom.

# Warning

Not 100% of the romset is playable yet, because the algorithm is over.

# Result

![Me playing](https://raw.githubusercontent.com/aluzed/MiSTer-Neogeo-Rom-Decrypter/master/preview.jpg)

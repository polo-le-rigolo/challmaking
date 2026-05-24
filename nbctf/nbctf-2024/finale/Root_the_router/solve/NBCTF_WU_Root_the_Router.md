The challenge involves gaining access to a router via a UART connection that is password-protected. We are provided access via netcat (`nc`) to access the UART shell but cannot interact with it because it requires a password. We managed to dump the router’s firmware, and our goal is to extract the root password from this firmware to gain access to the UART shell and retrieve the flag.

---
## Steps:

### 1. Connecting via Netcat:
We are given access to a simulated UART shell using `nc`:

```
nc instance_ip port
```

Upon connection, the device asks for a password. The task is to find this password by analyzing the router’s dumped firmware.

### 2. Analyzing the Firmware:

We start with a firmware binary called `firmware.bin`:

```
file firmware.bin 
```

This simply tells us the file is binary data. To extract more information, we run **binwalk** to 
identify embedded filesystems and other data in the firmware:

```
binwalk firmware.bin
```

The output shows the presence of a bootloader (U-boot), an LZMA compressed archive (likely the linux kernel) and a **SquashFS** filesystem within the firmware:

```
0             0x0             U-Boot version string, "U-Boot 1.1.3 (Jan 19 2018 - 17:59:01)"
49632         0xC1E0          LZMA compressed data, properties: 0x5D, dictionary size: 8388608 bytes, uncompressed size: 3101556 bytes
1359840       0x14BFE0        Squashfs filesystem, little endian, version 4.0, compression:gzip, size: 729195 bytes, 34 inodes, blocksize: 131072 bytes, created: 2024-10-24 12:58:04

```
### 3. Extracting the Filesystem:

Using `binwalk -e`, we extract the contents of the firmware:

```
binwalk -e firmware.bin
```

This creates a directory `_firmware.bin.extracted/` containing the extracted files, including the **SquashFS** filesystem.

### 4. Navigating the Extracted Files:

We explore the contents of the extracted filesystem by navigating to the **squashfs-root** directory:
```
$ cd _firmware.bin.extracted/squashfs-root/
$ ls
bin  etc  home	mnt  root  sbin  tmp  usr  var
```

The directory contains standard Linux folders, such as `/bin`, `/etc`, `/home`, and `/root`. We start by exploring potential files that may contain sensitive information.

### 5. Hint Discovery:

Checking the `/home/admin` directory, we find a file named `flag.txt`:
```
cat home/admin/flag.txt
```
This file contains the following message:
```
Congratulations on getting the filesystem!
Maybe look around the files to find a password to authenticate on the UART shell?
Good luck :p

PS: John is a good friend, maybe he can help you?
```

This suggests the use of **John** to crack passwords. We proceed to check the `/etc/shadow` file for password hashes.

### 6. Extracting Password Hash:

The `/etc/shadow` file contains password hashes for both the `admin` and `root` users:
```
cat etc/shadow
```
Output:
```
admin:$1$$8f1f7aaf3e931f2b42af99f6720c27b4:18551:0:99999:7:::
root:$1$$8f1f7aaf3e931f2b42af99f6720c27b4:18551:0:99999:7:::
```

Both users share the same hash: `8f1f7aaf3e931f2b42af99f6720c27b4`.

### 7. Cracking the Hash:

Following the hint about **John**, we can either use John the Ripper or an online hash-cracking service to crack the password. Using an online service like [hashes.com](https://hashes.com/en/decrypt/hash), we input the hash and get the password:

- Password: **peanutbutter**

### 8. Accessing the UART Shell:
With the obtained password, we reconnect to the UART root shell via netcat:


```
eddymalou@parrot:~$ nc localhost 12345
Please enter the password:
>peanutbutter

 
 ____             _     _   _                            _            
|  _ \ ___   ___ | |_  | |_| |__   ___   _ __ ___  _   _| |_ ___ _ __ 
| |_) / _ \ / _ \| __| | __| '_ \ / _ \ | '__/ _ \| | | | __/ _ \ '__|
|  _ < (_) | (_) | |_  | |_| | | |  __/ | | | (_) | |_| | ||  __/ |   
|_| \_\___/ \___/ \__|  \__|_| |_|\___| |_|  \___/ \__,_|\__\___|_|   
           
    
[>] Enter 'help' for a list of commands.

> help
Available commands are: help, flag, exit
>
> flag
Congrats! Here's the flag: NBCTF{P34NUT_8UTT3r_J311Y_T1M3}
>

```


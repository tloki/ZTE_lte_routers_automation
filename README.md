# ZTE LTE routers Simple SMS automation using Python

a project that makes it easy to fetch some data from these
routers via python / cli. 

especially for A1 versions in Croatia that seem to have broken
SMS reader (will wait indefinitely).

also has a feature that will sync local SMS-es to remote (SSH)
directory (using default system / user ssh credentials).

Works with all MF-286 / MF-286R / MF-286X routers.

To configure the service you need to create virtualenv 
and install dependencies from requirements (scp and paramiko optional
if you don't want transfer to remote ssh server).

Tested on Linux and Raspberry Pi 3/4/5/Zero and latest Ubuntu and Raspberry Pi OS as of 14. Sep. 2024.

the only required config should be in config.json (set router IP/hostname, pass, etc)

to install periodical service check bottom of zte_sms.service unit file.

Any feedback / PR is welcome!

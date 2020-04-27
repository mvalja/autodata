Some notes about this system:

Linux root password is "Vasteras1!"
(excluding the quotes of course)

DE400:
Note that all passwords for Oracle accounts (schema users) are case sensitive and in UPPERCASE.
When you log in to DE400-client enter:
Operator name:   cc_user (case insensitive)
Password:        CC_USER
DE 400 Instance: MDB


UDW/Oracle:
Oracle for UDW is not started automatically after a reboot.
This is done by purpose to save resources in vCloud.
UDW shall only be started if you need it.
To start it proceed like this:
either...
  Login as oracle in bldas01 and state "udwstart"
  wait about 30s
  Login as oracle in bldas02 and state "udwstart"
or...
  Open WS500 picture Maintenance -> Control System Information
  Select application server "ORA_DB"
  Click start at bldas01
  wait about 30s
  Click start at bldas02
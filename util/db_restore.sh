#!/usr/bin/bash
sqlcmd \
-S host \
-U stox \
-P stox \
-Q "RESTORE DATABASE [stox] FROM DISK = N'stox.bak' WITH FILE = 1, NOUNLOAD, REPLACE, STATS = 10"

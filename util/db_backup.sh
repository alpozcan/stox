#!/usr/bin/bash
sqlcmd \
-S host \
-U stox \
-P stox \
-Q "BACKUP DATABASE [stox] TO DISK = N'stox.bak' WITH NOFORMAT, NOINIT, NAME = 'stox-full-backup', SKIP, NOREWIND, NOUNLOAD, STATS = 10"

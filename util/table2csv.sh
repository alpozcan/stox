#!/usr/bin/bash
/opt/mssql-tools/bin/sqlcmd \
-S host \
-U stox \
-P stox \
-d stox \
-Q "select * from [stocks].[daily]" \
-s ',' -w 511 \
| tr -d ' '

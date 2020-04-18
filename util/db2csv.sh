#!/usr/bin/bash
sqlcmd \
-S host \
-U stox \
-P stox \
-d stox \
-Q "select * from [stocks].[daily]" \
-s ',' -w 511 \
| tr -d ' '

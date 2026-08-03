# AMI v3.2.2

## Summary
- **Windows**: hardening contro crash dopo pochi minuti (ping localizzato, cache icone tray, niente QThread a ogni poll, dashboard matplotlib solo se visibile)
- **Diagnostica**: log crash in cartella dati utente (`ami-crash.log`) invece di `/tmp`

## Install
Scarica lo ZIP della tua piattaforma (`AMI-v3.2.2-macos.zip` o `AMI-v3.2.2-windows.zip`), estrai e avvia **AMI.app** (macOS) o `AMI.exe` (Windows).

Su Windows, in caso di problemi: `%LOCALAPPDATA%\CiaoIM\AMI\ami-crash.log`

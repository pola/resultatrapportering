REM i powershell skriv:
REM Set-ItemProperty HKCU:\Console VirtualTerminalLevel -Type DWORD 1
REM eller
REM
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1

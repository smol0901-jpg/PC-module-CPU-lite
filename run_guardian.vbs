Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.SpecialFolders("Startup") & "\PCGuardian.vbs"
oWS.Run "pythonw.exe pc_health_guardian.py", 0, False

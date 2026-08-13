' Запуск без консольного окна (только GUI и трей)
Set objShell = CreateObject("WScript.Shell")
objShell.Run "pythonw.exe pc_health_guardian.py", 0, False


import pythoncom
import win32com.client

pythoncom.CoInitialize()

try:
    app = win32com.client.Dispatch("PowerPoint.Application")

    print("PowerPoint COM launch: PASS")
    print("Version:", app.Version)
    print("Presentations:", app.Presentations.Count)

except Exception as error:
    print("PowerPoint COM launch: FAIL")
    print(type(error).__name__ + ":", error)

finally:
    pythoncom.CoUninitialize()

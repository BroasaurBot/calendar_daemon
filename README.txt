--------------Calendar command line deamon and query ----------------------

Requirements:
-python3 or greater

Default Installation:
- daemon.py (responsible for data base management)
	installed at /opt/calendar/daemon.py
- calendar.py (queries data base and can add and update events)
	installed at /opt/calendar/calendar.py
- cald_db.csv (csv containg events)
	created at /opt/calendar/cald_db.csv

To change the default calendar data base location:
1 - open /etc/init.d/calendar in your favourite text edit
2 - On the line DEFAULT_DATABASE_PATH within " " enter new absolute path and file name

Usage:
- daemon is run automatically on boot up and closed on poweroff and reboot
- enter: calendar COMMAND ....  , to interact run calendar.py

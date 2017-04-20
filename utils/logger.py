import syslog
import helper


def log(message):
    message = helper.utf_to_str(message)

    syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
    syslog.syslog(syslog.LOG_INFO, message.strip())
    print message

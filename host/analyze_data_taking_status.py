''' Script that sends info E-Mails if the data taking stops. Therefore it checks if at least one file of some given files in a specified folder 
is changed in a specified time. If not an alert E-Mail is send. If the data taking work again an info email is send
'''
import time
import os
import string
import smtplib
import logging
import pprint
from threading import Event
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - [%(levelname)-8s] (%(threadName)-10s) %(message)s")

configuration = {
    "path_to_monitor": 'data',  # the monitor the watchdog checks
    "timeout": 1,  # the timeout in seconds until an alert email is send if the data files did not change
    'data_files': ['foo.h5', 'bar.h5'],  # the files that are monitored for changes
    "check_subfolders": True,  # check also the subfolders of 'path_to_monitor'
    "email_host": 'mail.gmx.net',  # outgoing mail server
    "email_to": ["pohl@physik.uni-bonn.de", "janssen@physik.uni-bonn.de"],  # the Email adresses the status emails are send to
    "email_account": ['mr_beam@gmx.de', 'pidub123']  # email account name and password used to send email
}


def send_mail(text, subject=''):
    logging.info('send status E-Mail (' + subject + ')')
    body = string.join((
            "From: %s" % configuration['email_account'][0],
            "To: %s" % configuration['email_to'],
            "Subject: %s" % subject,
            "",
            text
            ), "\r\n")
    server = smtplib.SMTP(configuration['email_host'])
    server.login(configuration['email_account'][0], configuration['email_account'][1])
    server.sendmail(configuration['email_account'][0], configuration['email_to'][0], body)
    server.quit()


class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if os.path.basename(event.src_path) in configuration['data_files']:
            data_changed.set()

if __name__ == '__main__':
    logging.info('Configuration:\n' + pprint.pformat(configuration))
    alert_status = Event()
    data_changed = Event()
    alert_status.clear()
    data_changed.clear()
    observer = Observer()
    observer.schedule(MyHandler(), path=configuration['path_to_monitor'], recursive=configuration['check_subfolders'])
    observer.start()

    try:
        while True:
            time.sleep(configuration['timeout'])
            if not data_changed.is_set():
                logging.info('data taking BAD')
                if not alert_status.is_set():
                    send_mail("Sorry... go to work ;-)\nSincerely Mr. Beam", subject='TESTBEAM WARNING')
                    alert_status.set()
            else:
                logging.info('data taking OK')
                if alert_status.is_set():
                    send_mail("Very nice, I see that the data taking works again\nSincerely Mr. Beam", subject='TESTBEAM INFO')
                    alert_status.clear()
            data_changed.clear()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

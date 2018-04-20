import os
import sys
import time
import poplib
import smtplib
import email
from io import StringIO
from datetime import datetime
import base64
import icalendar as ic
# from . import database as db
from abe.helper_functions.ics_helpers import ics_to_dict
from abe.helper_functions.converting_helpers import mongo_to_dict
from abe import database as db
from mongoengine import ValidationError

from email import parser

def get_msg_list(pop_items, pop_conn):
    """ Takes a list of items and the pop3 connection
    (resp, items, octets = pop3conn.list())
    and returns a list of email.message.Message
    objects.
    """
    messages = []
    for item in pop_items:
        id, size = item.decode().split(' ')
        resp, text, octets = pop_conn.retr(id)

        text = [x.decode() for x in text]
        text = "\n".join(text)
        file = StringIO(text)

        orig_email = email.message_from_file(file)
        messages.append(orig_email)
    return messages

def get_attachments(message):
    """ Given a message object,
    checks for an attachment
    and returns it if one exists.
    """
    payload = message.get_payload()
    if len(payload) >= 2:
        attachment = payload[1]
        print(attachment.get_content_type())
        return attachment
    return None

def email_test(filename):
    """ TO DO: determine best way to test. Currently, file does
    not exist in this framework.
    """
    with open(filename, 'r') as myfile:
        data = myfile.read()

    message = email.message_from_string(data)
    calendars = []
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == 'text/calendar':
                decoded = base64.b64decode(part.get_payload()).decode('utf-8')
                cal = ic.Calendar.from_ical(decoded)
                for event in cal.walk('vevent'):
                    date = event.decoded('dtstart')
                    summary = event.decoded('summary')

                    print(date)
                    print(summary)
                print("-------------------------------------------------------------")
                print(decoded)
                calendars.append(cal)
    return calendars

def ical_to_dict(cal):
    """ Given a calendar, creates a dictionary as
    specified in ics_to_dict.
    :input: calendar object
    :return: tuple of event dictionary and sender email as string
    """
    # event_def = {}
    # utc = pytz.utc
    # convert_timezone = lambda a: a.astimezone(utc) if isinstance(a, datetime) else a
    event = cal.walk('vevent')[0]

    # sender can be found in the form of 'ORGANIZER': vCalAddress('b'MAILTO:<email>)
    sender = str(event.get('organizer')).strip().split(':')[1]
    # Get the labels off of the description. Assumes description is in format
    # [tags][go][here]\n
    # "rest of description"
    labels_and_desc = str(event.get('description')).strip().split('\n')
    if '[' == labels_and_desc[0][0]: # if the bracket is in the first line of the description, there are labels
        label_str = labels_and_desc[0].lower()
        labels = label_str.replace('[', ' ').replace(']', '').strip().split()
        desc = '\n'.join(labels_and_desc[1:]).strip()
    else:
        desc = '\n'.join(labels_and_desc).strip()
        labels = None
    event_def = ics_to_dict(event, labels)
    event_def['description'] = desc
    return event_def, sender

def get_messages_from_email():
    """ Fetches unread emails from the email address
    specified by the environmental variable ABE_EMAIL
    (password given by env var ABE_PASS). Returns a 
    list of messages.

    :return: List of email message objects
    """
    pop_conn = poplib.POP3_SSL('pop.gmail.com')
    try:
        pop_conn.user(os.environ['ABE_EMAIL']) # should be 'abe.at.olin@gmail.com'
        pop_conn.pass_(os.environ['ABE_PASS']) # should be 'abe@olin'
    except:
        pop_conn.user('abe.at.olin@gmail.com')
        pop_conn.pass_('abe@olin')
    pop3info = pop_conn.stat() #access mailbox status
    resp, items, octets = pop_conn.list()

    messages = get_msg_list(items, pop_conn)
    pop_conn.quit()
    return messages

def get_calendars_from_messages(messages):
    """ Returns any icals found as Calendar
    objects from the icalendar library.
    
    :inputs:
        messages:   List of email Message instances
    :return:        List of Calendar instances
    """
    calendars = []

    for message in messages:
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == 'text/calendar':
                    decoded = base64.b64decode(part.get_payload()).decode('utf-8')
                    cal = ic.Calendar.from_ical(decoded)
                    calendars.append(cal)
    return calendars

def cal_to_event(cal):
    """ Creates an event from a calendar object """
    received_data, sender = ical_to_dict(cal)
    try:
        new_event = db.Event(**received_data)
        if new_event.labels == []: # if no labels were given
            new_event.labels = ['unlabeled']
        if 'recurrence' in new_event: # if this is a recurring event
            if new_event.recurrence.forever == False: # if it doesn't recurr forever
                # find the end of the recurrence
                new_event.recurrence_end = find_recurrence_end(new_event)
        new_event.save()
    except ValidationError as error:
        error_reply(sender, error)
        return {'error_type': 'validation',
                'validation_errors': [str(err) for err in error.errors],
                'error_message': error.message}, 400
    else:  # return success
        new_event_dict = mongo_to_dict(new_event)
        reply_email(sender, new_event_dict)
        return new_event_dict, 201

def smtp_connect():
    """ Connects to the smtp server
    :return: server instance, gmail to send
    """
    try:
        gmail = os.environ['ABE_EMAIL'] # should be 'abe.at.olin@gmail.com'
        gpass = os.environ['ABE_PASS'] # should be 'abe@olin'
    except:
        gmail = 'abe.at.olin@gmail.com'
        gpass = 'abe@olin'
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail, gpass)
    except:
        print('Connecting to gmail failed...')
        return
    return server, gmail

def error_reply(to, error):
    """ Given the erros, sends an email with the errors that
    occured to the original sender. """
    server, sent_from = smtp_connect()
    subject = 'Event Failed to Add'
    body = "ABE didn't manage to add the event, sorry. Here's what went wrong: \n"
    for err in error.errors:
        body = body + str(err) + '\n'
    body = body + "Final error message: " + error.message

    email_text = """
    From: {}
    To: {}
    Subject: {}

    {}
    """.format(sent_from, to, subject, body)

    send_email(server, email_text, sent_from, to)

def reply_email(to, event_dict):
    """ Responds after a successful posting with
    the tags under which the event was saved. """
    server, sent_from = smtp_connect()
    subject = '{} added to ABE!'.format(event_dict['title'])
    tags = ', '.join(event_dict['labels']).strip()
    body = "Your event was added to ABE! Here's the details: "

    email_text = """
    From: {}
    To: {}
    Subject: {}

    {}
    Description: {}
    Tags: {}
    """.format(sent_from, to, subject, body, event_dict['description'], tags)
    send_email(server, email_text, sent_from, to)

def send_email(server, email_text, sent_from, sent_to):
    server.sendmail(sent_from, sent_to, email_text)
    server.close()

def scrape():
    """ Scrapes emails and parses them into events """
    msgs = get_messages_from_email()
    cals = get_calendars_from_messages(msgs)
    print("Scraped", len(cals), "from abe.at.olin@gmail.com")
    completed = []
    for cal in cals:
        completed.append(cal_to_event(cal))
    return completed

if __name__ == '__main__':
    cals = email_test('test_email.txt')
    for cal in cals:
        ical_to_dict(cal)
    # messages = get_messages_from_email()
    # calendars = get_calendars_from_messages(messages)
    # for calendar in calendars:
    #     print(calendar)
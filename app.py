import requests
import json
import smtplib
import datetime

from bs4 import BeautifulSoup
from string import Template

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apscheduler.schedulers.blocking import BlockingScheduler

url = 'http://www.concursosfcc.com.br/concursoNovo.html'

ADDRESS = open('utils/.email').read()
PASSWORD = open('utils/.password').read()

email_server = smtplib.SMTP('smtp.gmail.com', 587)
email_server.starttls()
email_server.login(ADDRESS, PASSWORD)

def scraper():
	page = requests.get(url)
	soup = BeautifulSoup(page.text, 'html.parser')

	contests_list = soup.find(id='refazerLista')

	contests = contests_list.find_all(class_='textoInstituicao2')

	contests_info = []

	for contest in contests:
		text = contest.find('a')
		contests_info.append(text.contents[0])

	return contests_info

def get_contacts():
	with open('utils/contacts.json', mode='r', encoding='utf-8') as contacts:
		return json.loads(contacts.read())

def read_template():
	with open('utils/template.txt', mode='r', encoding='utf-8') as template_file:
		return Template(template_file.read())

def get_contests_text():
	text = ""
	
	for contest in scraper():
		text += "- {}\n".format(contest)

	return text
		
scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', day_of_week='mon-fri', hour=14)
def send_emails():
	print('sending email...')
	contacts = get_contacts()
	contests_text = get_contests_text()
	
	for name, email in contacts.items():
		email_text = MIMEMultipart()

		message = read_template().substitute(who=name, contests=contests_text, url=url)

		today = datetime.date.today()
		date = today.strftime('%d/%m')

		email_text['From'] = ADDRESS
		email_text['To'] = email
		email_text['Subject'] = 'Concursos FCC - {}'.format(date)

		email_text.attach(MIMEText(message, 'plain'))

		email_server.send_message(email_text)

		del email_text

scheduler.start()
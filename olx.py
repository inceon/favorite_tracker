import requests
import time
import pync
import config
import telebot
from bs4 import BeautifulSoup

def get_html(site):
    r = requests.get(site, cookies=dict(PHPSESSID=config.olx_session))
    return r.text

def get_page_data(html):
    soup = BeautifulSoup(html, 'lxml')
    return soup

def notify(title, text):
	favicon_link = config.olx_favicon
	open_link = config.olx_url
	main_sound_name = "Ping"
	pync.notify(
		text, 
		title 	= title, 
		appIcon = favicon_link,
		sound   = main_sound_name,
		open  	= open_link)  

bot = telebot.TeleBot(config.token)
bot.send_message(config.channel, "OLX script succesfully started")
notify("OLX script", "OLX script succesfully started")

while(True):
	page_html = get_html(config.olx_url)
	page_data = get_page_data(page_html)
	site_username = page_data.find(class_ = "userbox-login").text.strip()
	if site_username != config.olx_username:
		notify("OLX script", "We have problem with authorization")
		bot.send_message(config.channel, "We have problem with authorization")
	else:
		new_ads_data = page_data.find_all(class_ = "observedsearch")

		for (idx, el) in enumerate(new_ads_data):
			# notify_text = "[" + str(idx+1) + "] " + el.text.split(":")[1].strip();
			has_new = el.find(class_ = "newAds")
			category = el.find(class_ = "fbold").text

			if has_new:
				print(has_new.text)
				notify(category, has_new.text.split(":")[1].strip())

	print("Last check " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))			
	time.sleep(60)
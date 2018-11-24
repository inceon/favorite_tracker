import requests
import time
import pync
import config
import telebot
import random
from threading import Thread
from bs4 import BeautifulSoup

def log(text):
	current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	print("{0} - {1}".format(current_time, text))

def read_proxy_file():
	with open(config.olx_proxies_file, "r+") as fp:
		return fp.read().splitlines()

olx_proxies_list = read_proxy_file()
current_proxy = random.choice(olx_proxies_list)

def remove_proxy(url):
	global current_proxy
	global olx_proxies_list

	olx_proxies_list.remove(url)
	new_proxy_list = parse_new_proxies()
	olx_proxies_list.extend(new_proxy_list)

	# remove equal proxy url
	olx_proxies_list = list(set(olx_proxies_list))
	with open(config.olx_proxies_file, "w") as fp:
		fp.write("\n".join(olx_proxies_list))

	current_proxy = random.choice(olx_proxies_list)

def parse_new_proxies():
	try:
		res = requests.get(config.proxy_list_url)
		parsed_res = BeautifulSoup(res.text, 'lxml')

		new_proxy_list = []
		for proxy in parsed_res.find(id = "proxylisttable").find_all("tr")[1:-1]:
			proxy_info = proxy.find_all("td")
			if(proxy_info[6].text == "yes"):
				new_proxy_list.append("https://{0}:{1}".format(proxy_info[0].text, proxy_info[1].text))

		return new_proxy_list
	except Exception:
		log("We have problems with parsing new proxy")

def get_html(site, changeProxy = False):
	global current_proxy
	global olx_proxies_list

	headers = {"User-Agent": ""}
	if config.USER_AGENT_LIST:
		headers = {"User-Agent": random.choice(config.USER_AGENT_LIST)}

	if changeProxy:
		current_proxy = random.choice(olx_proxies_list)
		try:
			log('{0} {1}'.format("Proxy ip:", requests.get(config.get_ip_service, proxies = {"https" : current_proxy }).text))
		except Exception:
			log('{0} {1}'.format("Lol, not valid proxy:", current_proxy))
			remove_proxy(current_proxy)

	try:
		r = requests.get(
			site, 
			cookies = dict(PHPSESSID=config.olx_session),
			proxies = {
				"https" : current_proxy
			},
			headers = headers,
			timeout = 10
		)
	except Exception:
		log("Connection problem with: {0}".format(current_proxy))
		remove_proxy(current_proxy)
		return get_html(site, True)
	else:
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


### BOT LOGIC ###

def check_ip():
	try:
		ip_text = requests.get(config.get_ip_service, proxies = {"https" : current_proxy }).text
		log('{0} {1}'.format("Proxy ip:", ip_text))
	except Exception:
		log("Removed proxy: {0}".format(current_proxy))
		remove_proxy(current_proxy)
		check_ip()

log("My current ip: {0}".format(requests.get(config.get_ip_service).text))
check_ip()

bot = telebot.TeleBot(config.token)

# register handler for PHSESSION
@bot.message_handler(commands=['key'])
def handler_key(message):
	olx_key = message.text.split(maxsplit=1)[1]
	config.olx_session = olx_key
	bot.send_message(config.channel, "Key succesfully applied")

def check_favorites():
	while(True):
		page_html = get_html(config.olx_url)
		page_data = get_page_data(page_html)
		site_username = page_data.find(class_ = "userbox-login").text.strip()
		if site_username != config.olx_username:
			notify("OLX script", "We have problem with authorization")
			bot.send_message(config.channel, "We have problem with authorization. Username is {0}".format(site_username))
		else:
			new_ads_data = page_data.find_all(class_ = "observedsearch")

			if len(new_ads_data) == 0:
				log("Looks loke we don't have favorites :(")

			for (idx, el) in enumerate(new_ads_data):
				# notify_text = "[" + str(idx+1) + "] " + el.text.split(":")[1].strip();
				has_new = el.find(class_ = "newAds")
				category = el.find(class_ = "fbold").text

				if has_new:
					log(has_new.text)
					notify(category, has_new.text.split(":")[1].strip())

		log("latest check")			
		time.sleep(120)


t1 = Thread(target = check_favorites)
t1.setDaemon(True)
t1.start()

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print("Catched telebot error") 
        time.sleep(15)

notify("OLX script", "OLX script succesfully started")
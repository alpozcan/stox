#!/usr/bin/env python3
# Download the current ASX All Ordinaries(XAO) index table from Westpac
import os, random, time
from selenium import webdriver
from nerodia.browser import Browser

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
INDICES_DIR = BASE_DIR + '/../data/indices'
INDICES_FILE = INDICES_DIR + '/Market_Indices.csv'
XAO_FILE = INDICES_DIR + '/XAO_Makeup.csv'

LOGIN_PAGE = 'https://onlineinvesting.westpac.com.au/login'

def slp(duration=1.0):
    time.sleep(duration + random.random() * (duration / 2))

fp = webdriver.FirefoxProfile()
fp.set_preference("browser.download.folderList", 2)
fp.set_preference("browser.download.dir", INDICES_DIR)
fp.set_preference("browser.helperApps.neverAsk.saveToDisk", 'text/plain,text/csv,application/csv,application/download,application/octet-stream,application/text')
fp.set_preference('browser.download.manager.showWhenStarting', False)
fp.set_preference("browser.cache.disk.enable", False)

b = Browser(browser=webdriver.Firefox(fp, service_log_path='/dev/null'))

b.goto(LOGIN_PAGE)
slp(2)
b.text_field(id='username').set(os.environ['WPOIU'])
b.text_field(id='password').set(os.environ['WPOIP'])
b.button(type='submit').click()
slp(4)

b.link(text='Quotes & Research').click()
slp(2)

b.link(text='Market Indices').click()
slp(3)

os.remove(INDICES_FILE)
b.link(text='Download CSV').click()
slp(8)

b.links(title='Index Makeup')[0].click()
slp(14)

os.remove(XAO_FILE)
b.link(text='Download CSV').click()
slp(10)

b.link(id='ctl00_LoginControl1_btnLogout_implementation').click()
slp(3)
b.close()

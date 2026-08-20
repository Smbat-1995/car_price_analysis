#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from sqlalchemy import create_engine
import time
import os
from dotenv import load_dotenv


# In[2]:


auto_am_main = 'https://auto.am/'

auto_am_url = f'{auto_am_main}'+"""search/passenger-cars?q={%22category%22:%221%22,%22page%22:%221%22,%22sort%22:%22latest%22,%22layout%22:%22list%22,%22user%22:{%22dealer%22:%220%22,%22official%22:%220%22,%22id%22:%22%22},%22make%22:[%22246%22],%22model%22:{%22246%22:[%22490%22,%224043%22,%224044%22,%222957%22,%224045%22,%221974%22,%221975%22,%224046%22,%225186%22,%221976%22,%225554%22,%221972%22,%223590%22]},%22year%22:{%22gt%22:%222012%22,%22lt%22:%222017%22},%22usdprice%22:{%22gt%22:%220%22,%22lt%22:%22100000000%22},%22custcleared%22:%221%22,%22mileage%22:{%22gt%22:%220%22,%22lt%22:%221000000%22}}"""
list_am_url = """https://www.list.am/category/1472?n=0&cmtype=&bid=49&mid=957%2C3284&crc=&price1=&price2=&_a27=0&_a2_1=2013&_a2_2=2017&_a15=&_a28_1=&_a28_2=&_a207_1=&_a207_2=&_a13=&_a23=&_a1_1=&_a1_2=&_a109=&_a43=&_a16=&_a17=&_a197=&_a22=0&_a105=&_a106=&_a102=0&_a101=&_a103=&_a104="""


# In[ ]:





# In[3]:


def open_url(url):
    driver = webdriver.Edge()
    driver.get(url)
    return driver


# In[4]:


driver = open_url(auto_am_main)


# In[5]:


def select_mark():
    driver.find_element(By.ID,'select2-filter-make-container').find_element(By.CLASS_NAME , 'select2-selection__placeholder').click()
    driver.find_element(By.CLASS_NAME, 'select2-search__field').send_keys('Mercedes-Benz')
    time.sleep(2)
    driver.find_element(By.CLASS_NAME, 'select2-results').click()
    time.sleep(2)


# In[6]:


def select_model():
    driver.find_element(By.ID,'select2-v-model-container').find_element(By.CLASS_NAME , 'select2-selection__placeholder').click()
    driver.find_element(By.CLASS_NAME, 'select2-search__field').send_keys('CLS')
    time.sleep(2)
    driver.find_element(By.XPATH, '/html/body/span/span/span[2]/ul/li[1]').click()
    time.sleep(2)


# In[7]:


def select_start_year():
    driver.find_element(By.XPATH, '/html/body/section[1]/div/div[2]/div/div/div/div[3]/label[1]/span/span[1]/span/span[1]').click()
    driver.find_element(By.CLASS_NAME, 'select2-search__field').send_keys('2012')
    time.sleep(2)
    driver.find_element(By.CLASS_NAME, 'select2-results__options').click()
    time.sleep(2)


# In[8]:


def select_end_year():
    driver.find_element(By.XPATH, '/html/body/section[1]/div/div[2]/div/div/div/div[3]/label[2]/span/span[1]/span/span[1]').click()
    driver.find_element(By.CLASS_NAME, 'select2-search__field').send_keys('2017')
    time.sleep(2)
    driver.find_element(By.CLASS_NAME, 'select2-results__options').click()
    time.sleep(2)


# In[9]:


def duty_free():
    driver.find_element(By.XPATH, '/html/body/section[1]/div/div[2]/div/div/div/div[6]/div[1]/label/span').click()


# In[10]:


def search():
    driver.find_element(By.ID,'search-btn').click()


# In[11]:


select_mark()
select_model()
select_start_year()
select_end_year()
duty_free()
search()


# In[12]:


def get_content():
    # driver = webdriver.Edge()
    # driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    driver.close()
    return soup

def get_cars(soup):
    search_results = soup.find('div', attrs={'id':'search-result'})
    cars = search_results.find_all('div',attrs  = {'class':'card'})
    return cars

def get_hrefs(cars):
    hrefs = [auto_am_main + car.find('a', attrs={'class':"click-for-gtag"})['href']  for car in cars]
    return hrefs

def get_specific_car_content(href):
    html = requests.get(href).text
    soup = BeautifulSoup(html, "html.parser")
    return soup

def get_car_name(car_soup):
    return car_soup.find('title').text.split(' - ')[-1]

def get_car_vin(car_soup):
    try:
        return car_soup.find('div',attrs={'class':"pad-left-6"}).text.strip()
    except:
        return

def get_car_year(car_soup):
    return car_soup.find('a',attrs={'class':"grey-text"}).text

def get_car_metadata(car_soup):
    metadata_html = car_soup.find('tbody')
    rows = metadata_html.find_all('tr')
    metadata = {}
    for row in rows:
        cells = row.find_all('td')
        header,value = cells
        metadata[header.text] = value.text.strip().split(' "')[0]
    return metadata

def get_add_info(car_soup):
    add_infos = car_soup.find_all('div',attrs={'class':"nottii bltitle medium"})
    count = 0
    add_exists = False
    for i in add_infos:
        if i.text == 'Լրացուցիչ':
            add_exists = True
            break
        else:
            count += 1
    if add_exists:
        add_info = car_soup.find_all('div',attrs={'class':"ad-options"})[count].text.strip()
    else:
        add_info = None
    return add_info

def get_car_seller_phone(car_soup):
    try:
        return car_soup.find('a' , attrs={'id':"callBtnOptional1"}).text.strip()
    except:
        return car_soup.find('a' , attrs={'id':"callBtn1"}).text.strip()

def get_car_price(car_soup):
    return car_soup.find('span',attrs={'class':"fnum"}).text.replace(' ','')


# In[13]:


soup = get_content()
cars = get_cars(soup)
hrefs = get_hrefs(cars)


# In[14]:


print(f'Found {len(hrefs)} cars')


# In[15]:


final_data = {
    'car_name': [],
    'year': [],
    'add_info': [],
    'phone': [],
    'price': [],
    'Վազքը': [],
    'Թափքը': [],
    'Շարժիչը': [],
    'Փոխանցման տուփը': [],
    'Ղեկը': [],
    'Գույնը': [],
    'Վիճակը': [],
    'Սրահի գույնը': [],
    'Շարժիչի ծավալը': [],
    'Դռների քանակը': [],
    'Ձիաուժը': [],
    'Մոդիֆիկացիան': [],
    'Մխոցների քանակը': [],
    'Քարշակը': [],
    'Անվահեծերը': [],
    'Link':[]}
count = 0
for href in hrefs:
    car_soup = get_specific_car_content(href)
    car_name = get_car_name(car_soup)
    year = get_car_year(car_soup)
    metadata = get_car_metadata(car_soup)
    vin = get_car_vin(car_soup)
    add_info = get_add_info(car_soup)
    phone = get_car_seller_phone(car_soup)
    price = get_car_price(car_soup)
    final_data['car_name'].append(car_name) 
    final_data['year'].append(year) 
    final_data['price'].append(price) 
    final_data['add_info'].append(add_info)
    final_data['phone'].append(phone)
    final_data['Link'].append(href)
    for data in metadata:
        final_data[data].append(metadata[data])
    count += 1
    for key in final_data:
        if len(final_data[key]) < count:
            final_data[key].append(None)


# In[16]:


df = pd.DataFrame(final_data)


# In[17]:


df['scrape_date'] = pd.to_datetime(datetime.today())


# In[18]:


# 2. Define your PostgreSQL credentials
load_dotenv()
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME')

# 3. Create the SQLAlchemy engine for PostgreSQL
connection_string = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require'
engine = create_engine(connection_string)


# In[19]:


# 4. Append the data to the table
df.to_sql(
    name='auto_am_listings', 
    con=engine, 
    if_exists='append', 
    index=False
)

print(f"Successfully appended {len(df)} rows to PostgreSQL for {df['scrape_date'].iloc[0]}")


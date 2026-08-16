import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
import cloudscraper
import os
from dotenv import load_dotenv

list_am_main = 'https://www.list.am'
list_am_url = f"{list_am_main}/category/1472?n=0&bid=49&mid=957%2C3284&_a2_1=2012&_a2_2=2017&_a27=0&_a22=0&_a102=0"


def get_html_response(url):
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)
    response_text = response.text
    soup = BeautifulSoup(response_text, "html.parser")
    return soup


def get_cars(soup):
    search_results = soup.find_all('div' ,attrs={'class':'dl'})
    return search_results

def get_hrefs(cars):
    if len(cars)>1:
        top_links = cars[0].find('div' ,attrs={'class':'gl'})
        hrefs =  [list_am_main + link['href'] for link in top_links.find_all('a',attrs={'class':"h"})]
        normal_links = cars[1].find('div' ,attrs={'class':'gl'})
        hrefs1 = [list_am_main + link['href'] for link in normal_links.find_all('a',attrs={'class':"class"})]
        hrefs = hrefs + hrefs1
    else:
        hrefs = [list_am_main + link['href'] for link in cars.find_all('a',attrs={'class':"class"})]
    return hrefs

def get_specific_car_content(href):
    scraper = cloudscraper.create_scraper()
    html = scraper.get(href).text
    #html = requests.get(href).text
    soup = BeautifulSoup(html, "html.parser")
    return soup

def get_car_name(car_soup):
    return car_soup.find('title').text.split(' - ')[0]

def get_car_vin(car_soup):
    try:
        return car_soup.find('div',attrs={'class':"pad-left-6"}).text.strip()
    except:
        return

def get_car_year(car_soup):
    return car_soup.find('a',attrs={'class':"grey-text"}).text

def get_car_metadata(car_soup):
    data_dict = {}
    all_details = car_soup.find('div', class_='vi')

    car_detils = all_details.find_all('div',class_='attr g new')
    for detail in car_detils:
        sub_details = detail.find_all('div',class_='at2')
        for sub_detail in sub_details:
            names = sub_detail.find_all('div')
            for name in names[1:]:
                titles = name.find_all('p')
                if len(titles) > 1:
                    tag_element,name_element = titles
                else:
                    tag_element =  titles[0]
                    name_element = titles[0]
                data_dict[name_element.text] = tag_element.text
                data_dict = reverse_keys(data_dict , new_keys=('Հնարավոր է փոխանակում','Մաքսազերծված է'))

    return data_dict


def get_car_seller_phone(car_soup):
    try:
        return car_soup.find('a' , attrs={'id':"callBtnOptional1"}).text.strip()
    except:
        return car_soup.find('a' , attrs={'id':"callBtn1"}).text.strip()

def get_seller_id(car_soup):
    return car_soup.find('a',class_ = 'n')['href'].split('/')[-1]

def get_car_price(car_soup):
    element = car_soup.find('span', class_='price x')
    return element.text.strip()

def get_add_info(car_soup):

    def extract_post_id(span):
        return span.text.split(' ')[-1]

    def extract_create_date(span):
        return span.text.split(' ')[-1]

    def extract_update_date(span):
        if span: 
            return ' '.join(span.text.split(' ')[-2:]) 

    description = car_soup.find('div', class_='vi').find('div', class_='body').text
    other_info = car_soup.find('div', class_='vi').find('div', class_='footer').find_all('span')

    if len(other_info) == 3:
        post_id_span,create_date_span,update_date_span = other_info
    else:
        post_id_span,create_date_span = other_info
        update_date_span = None
    post_id,create_date,update_date = extract_post_id(post_id_span) ,extract_create_date(create_date_span),extract_update_date(update_date_span)
    return description,post_id,create_date,update_date

def reverse_keys(metadata,new_keys):
    new_dict = {}
    for i in metadata.items():
        for j in new_keys:
            if j == i[1]:
                new_dict[j] = i[0]

    for value in new_dict.values():
        del metadata[value]
    metadata.update(new_dict)
    return metadata


soup = get_html_response(list_am_url)
cars = get_cars(soup)
hrefs = get_hrefs(cars)


print(f'Found {len(hrefs)} cars')

count = 0
cars_list = []
for href in hrefs: #filter(lambda x: x == 'https://www.list.am/item/24081985?ld_src=2',hrefs):
    print(href)
    car_soup = get_specific_car_content(href)
    car_name = get_car_name(car_soup)
    price = get_car_price(car_soup)
    metadata = get_car_metadata(car_soup=car_soup)
    description,post_id,create_date,update_date = get_add_info(car_soup)
    seller_id = get_seller_id(car_soup)
    metadata['car_name']=car_name
    metadata['price'] = price
    metadata['description'] = description
    metadata['post_id'] = post_id
    metadata['seller_id'] = seller_id
    metadata['create_date'] = create_date
    metadata['update_date'] = update_date
    metadata['Link'] = href
    cars_list.append(metadata)


df = pd.DataFrame(cars_list)
df['scrape_date'] = pd.to_datetime(datetime.today())



# Read credentials from environment
# Load environment variables from .env file
load_dotenv()
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME')

# 3. Create the SQLAlchemy engine for PostgreSQL
connection_string = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
engine = create_engine(connection_string)


# 4. Append the data to the table
df.to_sql(
    name='list_am_listings', 
    con=engine, 
    if_exists='append', 
    index=False
)

print(f"Successfully appended {len(df)} rows to PostgreSQL for {df['scrape_date'].iloc[0]}")
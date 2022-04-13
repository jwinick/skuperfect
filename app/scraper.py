from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import urllib
import requests


def scrape_walmart(item_id=None,image_size='250'):
    if item_id is None:
        return 'missing item_id'

    item_id = str(item_id)
    image_size = str(image_size)

    driver = webdriver.Firefox()
    try:

        driver.get("https://www.walmart.com/ip/"+item_id)
        images = driver.find_elements_by_css_selector('#product-overview ul.slider-list img')

        urls = []
        for x in range(len(images)):
            image = images[x]
            url = image.get_attribute('src')

            final_url = []

            url_split = url.split('.jpeg?',1)

            a = url_split[0]+'.jpeg?'
            final_url.append(a)

            b = url_split[1].split('&',2)

            c = b[0].split('=',1)

            d = c[0]+'='
            final_url.append(d)

            e = image_size+'&'
            final_url.append(e)

            f = b[1].split('=',1)

            g = f[0]+'='
            final_url.append(g)

            h = image_size+'&'
            final_url.append(h)

            i = b[2]
            final_url.append(i)

            final_url = ''.join(final_url)

            urls.append(final_url)

            file_name = '_'.join(['w',item_id,str(x),'.jpg'])
            file_name = 'images/'+file_name
            print(file_name)
            img_data = requests.get(final_url).content
            with open(file_name, 'wb') as handler:
                handler.write(img_data)
    except:
        urls = None
    finally:
        driver.quit()
    return {'urls':urls}

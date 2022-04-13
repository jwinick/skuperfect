import json
from datetime import datetime, timedelta, date
from flask import render_template, flash, redirect, url_for, request, current_app, g, \
    jsonify, current_app, send_from_directory, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User, load_user
from app.main import bp
from app import login
import pymysql.cursors
from flask_mail import Message
from app import mail, basedir
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from os import listdir
from os.path import isfile, join
import random
import string
import pdfkit
import numpy as np
from twilio.rest import Client
from app.email import send_email
import glob
import base64
import pandas as pd
import urllib
import urllib.request
from app.myconnutils import getConnection
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import requests
import re
import time

account_sid = '*******'
auth_token = ''*******''
client = Client(account_sid, auth_token)

def text(body):
    message = client.messages.create(
      messaging_service_sid=''*******'',
      body=body,
      to='*******'
    )
    return message.sid

#general functions
def get_user(user_id):
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * from users WHERE user_id = %s ORDER BY user_id ASC LIMIT 1"
            cursor.execute(sql,(user_id))
            result = cursor.fetchone()
            return result
    finally:
        connection.close()

def get_email(email):
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * from users WHERE email = %s ORDER BY user_id ASC LIMIT 1"
            cursor.execute(sql,(email))
            result = cursor.fetchone()
            return result
    finally:
        connection.close()

@bp.route('/comming_soon',methods=['GET','POST'])
def test():
    return renter_template('comming_soon.html',)

@bp.route('/screener/<section>',methods=['GET','POST'])
@bp.route('/screener',methods=['GET','POST'],defaults={'section':None})
def screener(section):
    return render_template('screener.html',section=section)


@bp.route('/<section>/<code>',methods=['GET','POST'])
@bp.route('/<section>', methods=['GET', 'POST'], defaults={'code':None})
@bp.route('/', methods=['GET', 'POST'], defaults={'section':None,'code':None})
def index(section,code):
    basedir = os.path.abspath(os.path.dirname(__file__))
    l = basedir.split('/')[:-1]
    l.append('templates')
    x = '/'.join(l)
    mylist = glob.glob(x + '/index_*.html')
    mylist.sort(key=os.path.getmtime)
    name = mylist[len(mylist)-1]
    template_name = os.path.basename(name)
    user = None
    access_requests = None
    connection = getConnection()

    if current_user.is_authenticated:
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT * FROM `users` WHERE `user_id` = %s'
                cursor.execute(sql,(current_user.id))
                user = cursor.fetchone()
        except:
            user = None
    elif code is not None and user is None:
        if section == 'register':
            try:
                with connection.cursor() as cursor:
                    sql = 'SELECT `access_code`, `email`, `company_name`, `user_id` FROM `users` WHERE `access_code` = %s'
                    cursor.execute(sql,(code))
                    user = cursor.fetchone()
            except:
                user = None

    return render_template(template_name, section=section,user=user,code=code,title='SKU Perfect')

@bp.route('/load_admin',methods=['POST'])
def load_admin():

    access_requests = 'None'
    per_page = int(request.json['per_page'])
    page = int(request.json['page'])

    offset = (page-1)*per_page
    limit = per_page

    if current_user.id == 1:
        connection = getConnection()
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT COUNT(`user_id`) AS `count` FROM `users` WHERE `approved` = 0'
                cursor.execute(sql,())
                row = cursor.fetchone()
                count = row['count']
        except:
            count = '0'
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT `user_id`,`first_name`, `last_name`, `email`,`company_name`, `created` FROM `users` WHERE `approved` = 0 LIMIT %s, %s'
                cursor.execute(sql,(offset,limit))
                access_requests = cursor.fetchall()
        except:
            access_requests = 'None'

        connection.close()
        result = {'access_requests':access_requests,'count':count}
    return result




def validate_form():
    return 'pass'



# @bp.route('/submit_page_view',methods=['POST'])
# def submit_page_view():


@bp.route('/submit_form',methods=['POST'])
def submit_form():
    print('submit_form()')
    section = request.json['section']
    data = request.json['data']
    print('Section: '+str(section))
    print('Data: '+str(data))
    output = dict()
    for x in data:
        input_id = x['id']
        input_id = input_id[len(section)+1:]
        input_value = x['value']
        input_class = x['class']

        #validation tk
        value = str(input_value)

        validation_func = 'validate_'+input_id
        try:
            validation_result = globals()[func](string=string,section=section)
        except:
            validation_result = 'pass'
        if validation_result == 'pass':
            output[input_id] = value
        else:
            return {'section':section,'result':'fail','id':input_id}

    validate_func = 'validate_'+section
    validation_result = None
    try:
        validation_result = globals()[func](output=output)
    except:
        validation_result = None

    if validation_result is not None and validation_result['result'] != 'pass':
        result = {'section':section,'result':'fail','id':validation_result['id']}
    else:
        func = 'submit_'+section
        print('Chosen func: '+str(func))
        print(output)
        result = globals()[func](output=output)
        print('global func result: '+str(result))
        try:
            result = {'section':section,'result':result['result'],'id':result['id']}
        except:
            result = {'section':section,'result':result,'id':None}
    print(result)
    return result

@bp.route('/load_brand',methods=['POST'])
def load_brand():
    print('load_brand()')
    brand_id = int(request.json['brand_id'])
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT * FROM `brands` WHERE brand_id = %s AND user_id = %s ORDER BY brand_id DESC LIMIT 1'
            cursor.execute(sql,(brand_id,current_user.id))
            brand = cursor.fetchone()
    except:
        brand = None
    finally:
        connection.close()
    return brand


@bp.route('/load_sku',methods=['POST'])
def load_sku():
    print('load_sku()')
    sku_id = int(request.json['sku_id'])
    connection = getConnection()

    try:
        with connection.cursor() as cursor:
            sql = 'SELECT sk.name AS name, sk.sku_id AS sku_id, i.image_id AS image_id FROM skus sk LEFT JOIN pages p ON sk.sku_id = p.sku_id LEFT JOIN images i ON p.page_id  = i.page_id WHERE sk.sku_id = %s ORDER BY sk.sku_id DESC LIMIT 1'
            cursor.execute(sql,(sku_id))
            sku = cursor.fetchone()
    except:
        print('query load sku fail')
        sku = None
    finally:
        connection.close()

    return sku

@bp.route('/load_brand_list',methods=['POST'])
def load_brand_list():
    print('load_brand_list()')
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT * FROM `brands` WHERE user_id = %s ORDER BY brand_id ASC'
            cursor.execute(sql,(current_user.id))
            brands = cursor.fetchall()
    except:
        brands = None
    finally:
        connection.close()
    return {'brands':brands}

@bp.route('/fetch_page_id',methods=['POST'])
def fetch_page_id():
    print('fetch_page_id()')
    sku_id = request.json['sku_id']
    sitebrand_id = request.json['sitebrand_id']
    print('sku_id: '+str(sku_id))
    print('sitebrand_id: '+str(sitebrand_id))
    try:
        sku_id = int(sku_id)
        sitebrand_id = int(sitebrand_id)
    except:
        print('error converting parameters')
        return 'fail'

    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT page_id AS page_id FROM `pages` WHERE `sku_id` = %s AND sitebrand_id = %s'
            cursor.execute(sql,(sku_id,sitebrand_id))
            row = cursor.fetchone()
    except:
        print('error quering page')
        row = None
    finally:
        connection.close()

    if row:
        try:
            return row
        except:
            return 'fail'
    else:
        return 'fail'


@bp.route('/load_page',methods=['POST'])
def load_page():
    print('load_page()')
    page_id = request.json['page_id']
    try:
        page_id = int(page_id)
    except:
        return 'fail'
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT sk.sku_id AS `sku_id`,sk.name AS `sku_name`,p.modified AS `modified`, p.page_id AS `page_id`, s.name AS `site_name` FROM pages p LEFT JOIN sitebrands sb ON p.sitebrand_id = sb.sitebrand_id LEFT JOIN sites s ON sb.site_id = s.site_id LEFT JOIN skus sk ON p.sku_id = sk.sku_id WHERE p.page_id = %s ORDER BY p.created DESC LIMIT 1'
            cursor.execute(sql,(page_id))
            page = cursor.fetchone()
    except:
        page = None
    finally:
        connection.close()

    if page == None:
        print('error querying page')
        return 'fail'
    else:
        return page



@bp.route('/fetch_site_name',methods=['POST'])
def fetch_site_name():
    print('fetch_site_name()')
    site_id = request.json['site_id']
    print(site_id)
    try:
        site_id = int(site_id)
    except:
        return 'fail'

    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT `name` FROM `sites` WHERE site_id = %s'
            cursor.execute(sql,(site_id))
            row = cursor.fetchone()
    except:
        row = None
    finally:
        connection.close()

    print('Row: '+str(row))
    if row:
        try:
            site_name = row['name']
            return str(site_name)
        except:
            return 'fail'
    else:
        return 'fail'

@bp.route('/load_sitebrands',methods=['POST'])
def load_sitebrands():
    print('load sitebrands()')
    sku_id = int(request.json['sku_id'])
    section_id = request.json['section_id']
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT * FROM brands b LEFT JOIN sitebrands sb ON b.brand_id = sb.brand_id WHERE b.user_id = %s'
            cursor.execute(sql,(current_user.id))
            rows = cursor.fetchall()
    except:
        print('error scraping sitebrands')
        rows = None

    connection.close()
    if rows == None:
        return 'fail'
    else:
        return {'sitebrands':rows,'section_id':section_id}



@bp.route('/load_skus',methods=['POST'])
def load_skus():
    print('load_skus()')
    brand_id = request.json['brand_id']
    section = request.json['section']
    per_page = int(request.json['per_page'])
    page = int(request.json['page'])
    print('Per page: '+str(per_page))
    print('Page: '+str(page))
    offset = (page-1)*per_page
    limit = per_page

    print('current user: '+str(current_user.id))
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT COUNT(DISTINCT sk.sku_id) AS `count` FROM `skus` sk LEFT JOIN `brands` b ON b.brand_id = sk.brand_id LEFT JOIN `pages` p ON sk.sku_id = p.sku_id LEFT JOIN `images` i ON i.page_id = i.image_id WHERE b.user_id = %s'

            cursor.execute(sql,(current_user.id))

            row = cursor.fetchone()

        if row == None:
            count = 0
        else:
            count = row['count']
        print('Count: '+str(count))
    except:
        print('failed querying count')
        count = None
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT sk.sku_id sku_id,sk.name name, min(i.image_id) AS `image_number` FROM skus sk LEFT JOIN `brands` b ON b.brand_id = sk.brand_id LEFT JOIN pages p ON sk.sku_id = p.sku_id LEFT JOIN images i ON i.page_id = p.page_id WHERE b.user_id = %s GROUP BY sk.sku_id ORDER BY sk.created DESC LIMIT %s, %s'
            cursor.execute(sql,(current_user.id,offset,limit))
            skus = cursor.fetchall()
            print('SKUs: '+str(skus))
    except:
        print('failed querying skus')
        skus = None
    finally:
        connection.close()
    return {'skus':skus,'count':count,'section':section,'per_page':per_page,'page':page}


@bp.route('/load_pages',methods=['POST'])
def load_pages():
    print('load_pages()')
    site_id = request.json['site_id']
    brand_id = request.json['brand_id']
    per_page = int(request.json['per_page'])
    page = int(request.json['page'])

    offset = (page-1)*per_page
    limit = per_page

    conditions = []
    conditions.append(current_user.id)
    if site_id == None:
        site_condition = ''
    else:
        site_condition = ' AND sb.site_id = %s'
        conditions.append(int(site_id))

    if brand_id == None:
        brand_condition = ''
    else:
        brand_condition = ' AND b.brand_id = %s'
        conditions.append(int(brand_id))

    connection = getConnection()
    try:
        with connection.cursor() as cursor:
                sql = 'SELECT count(*) AS `count` FROM `pages` p LEFT JOIN `sitebrands` sb ON p.sitebrand_id = sb.sitebrand_id LEFT JOIN `brands` b ON sb.brand_id = b.brand_id WHERE b.user_id = %s'+site_condition+brand_condition
                cursor.execute(sql,(conditions))
                row = cursor.fetchone()
                print(row)

        if row == None:
            count = 0
        else:
            count = row['count']
    except:
        count = None

    conditions.append(offset)
    conditions.append(limit)
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT p.page_id AS page_id, min(i.`image_id`) AS `page_number` FROM `pages` p LEFT JOIN `sitebrands` sb ON p.sitebrand_id = sb.sitebrand_id LEFT JOIN `brands` b ON sb.brand_id = b.brand_id LEFT JOIN `images` i ON p.page_id = i.page_id WHERE b.user_id = %s'+site_condition+brand_condition+' GROUP BY 1 ORDER BY p.created DESC LIMIT %s, %s'
            print(sql)
            cursor.execute(sql,(conditions))
            pages = cursor.fetchall()
            print('Pages: '+str(pages))
    except:
        pages = None
    finally:
        connection.close()
    return {'pages':pages,'count':count}

@bp.route('/load_images',methods=['POST'])
def load_images():
    print('load_images()')
    page_id = request.json['page_id']
    print('Page ID: '+str(page_id))
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT i.image_id AS `image_id` FROM images i LEFT JOIN pages p ON i.page_id = p.page_id WHERE i.page_id = %s'
            print(sql)
            cursor.execute(sql,(page_id))
            rows = cursor.fetchall()
    finally:
        connection.close()
    image_ids = []
    try:
        for x in range(len(rows)):
            row = rows[x]
            image_id = row['image_id']
            if image_id != None and image_id not in image_ids:
                image_ids.append(image_id)
    except:
        image_ids = None
    print('Image IDs: '+str(image_ids))
    return {'image_ids':image_ids}


def validate_list(output):
    if isinstance(output, list) and len(output) > 0:
        return 'pass'
    else:
        return 'fail'


def validate_change_password(output):
    psw = str(output['psw'])
    psw2 = str(output['psw2'])

    if psw == psw2:
        return 'pass'
    else:
        return 'fail'

def validate_reset_password(output):
    psw = str(output['psw'])
    psw2 = str(output['psw2'])

    if psw == psw2:
        return 'pass'
    else:
        return 'fail'


def validate_register(output):
    psw = str(output['psw'])
    psw2 = str(output['psw2'])

    if psw == psw2:
        return 'pass'
    else:
        return 'fail'


def validate_old_psw(psw):
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT `psw` FROM `users` WHERE `user_id` = %s LIMIT 1'
            cursor.execute(sql,(current_user.id))
            row = cursor.fetchone()
    except:
        row = None
    finally:
        connection.close()

    if row == None:
        return 'fail'

    try:
        pwhash = row['psw']
    except:
        return 'fail'

    if check_password_hash(pwhash=pwhash,password=psw) == True:
        return 'pass'
    else:
        return 'fail'

def validate_psw(psw):
    if len(psw) > 1:
        return 'pass'
    else:
        return 'fail'

def validate_psw2(psw):
    if len(psw) > 1:
        return 'pass'
    else:
        return 'fail'


def validate_username(string,section):
    if section == 'register':
        connection = getConnection()
        with connection.cursor() as cursor:
            sql = 'SELECT `username` FROM `users` WHERE `username` = %s LIMIT 1'
            cursor.execute(sql,(string))
            row = cursor.fetchone()
        if row == None:
            return 'pass'
        else:
            return 'fail'
    else:
        return 'pass'


@bp.route('/reload_page',methods=['POST'])
def reload_page():
    print('reload_page()')
    page_id = request.json['page_id']
    try:
        page_id = int(page_id)
    except:
        print('error converting parameters')
        return 'fail'

    try:
        result = scrape_page(page_id=page_id,sitebrand_id=None,sku_id=None,refresh=1)
    except:
        print('error scraping page')
        return 'fail'

    if result == 'fail':
        print('scrape page result fail')
        return 'fail'

    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT p.page_id AS `page_id`, sb.site_id AS `site_id`,sk.sku_id AS `sku_id`, sk.name AS `sku_name` FROM `pages` p LEFT JOIN `skus` sk ON p.sku_id = sk.sku_id LEFT JOIN `sitebrands` sb ON p.sitebrand_id = sb.sitebrand_id WHERE page_id = %s LIMIT 1'
            cursor.execute(sql,(page_id))
            row = cursor.fetchone()
    except:
        print('querying page info error')
        connection.close()
        return 'fail'

    if row == None:
        print('querying page info no results')
        connection.close()
        return 'fail'
    try:
        sku_id = int(row['sku_id'])
        site_id = int(row['site_id'])
        sku_name = row['sku_name']
    except:
        print('unpacking page error')
        connection.close()
        return 'fail'
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT sk.sku_id AS `sku_id`,sk.name AS `sku_name`,p.modified AS `modified`, p.page_id AS `page_id`, s.name AS `site_name` FROM pages p LEFT JOIN sitebrands sb ON p.sitebrand_id = sb.sitebrand_id LEFT JOIN sites s ON sb.site_id = s.site_id LEFT JOIN skus sk ON p.sku_id = sk.sku_id WHERE sk.sku_id = %s AND s.site_id = %s ORDER BY p.created DESC LIMIT 1'
            cursor.execute(sql,(sku_id,site_id))
            page = cursor.fetchone()
    except:
        page = None
    finally:
        connection.close()

    if page == None:
        print('error querying page')
        return 'fail'
    else:
        return page


def submit_reset_password(output):
    print('submit_reset_password()')
    psw = output['psw']
    code = str(output['code'])

    psw = generate_password_hash(psw)

    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT `user_id` FROM `psw_reset` WHERE `code` = %s ORDER BY `psw_reset_id` DESC LIMIT 1'
            cursor.execute(sql,(code))
            result = cursor.fetchone()
    except:
        print('query psw_reset error!')
        connection.close()
        return 'fail'

    try:
        user_id = result['user_id']
    except:
        print('get user_id error!')
        connection.close()
        return 'fail'

    try:
        with connection.cursor() as cursor:
            sql = 'UPDATE `users` SET `psw` = %s WHERE `user_id` = %s'
            cursor.execute(sql,(psw,user_id))
            connection.commit()
    except:
        print('reset password error!')
        connection.close()
        return 'fail'
    return 'pass'


def submit_forgot_password(output):
    print('submit_forgot_password()')
    # print(output)
    email = output['email']
    user = get_email(email)
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    # print('User id: '+str(user['user_id']))
    # print('Code: '+str(code))
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'INSERT INTO `psw_reset` (`user_id`,`code`) VALUES (%s,%s)'
            cursor.execute(sql,(user['user_id'],str(code)))
        connection.commit()
    except:
        print('insert psw_reset fail!')
        return 'fail'
    finally:
        connection.close()

    send_email(subject='[SKU Perfect] Reset password!',
                sender='admin@skuperfect.com',
                recipients=email.split(),
                text_body=render_template('forgot_password.txt',first_name=user['first_name'],code=code),
                html_body=render_template('forgot_password.html',first_name=user['first_name'],code=code))
    return {'result':'pass','id':email}

def submit_brand(output):
    print('submit_brand()')
    print(output)
    site_list = ['walmart','amazon']

    name = output['name']
    name = " ".join(w.capitalize() for w in name.split())

    brand_id = scrape_brand(name=name)

    sites = output['site_id']
    sites = sites[1:-1]
    sites = sites.split(',')

    #first load search query
    #get url
    for x in range(len(sites)):
        site_id = sites[x]
        site_id = site_id.strip("\'")
        print('Site ID: '+str(site_id))
        site_id = int(site_id)
        url = get_query_url(site=site_id,string=name,page=1)

        if url:
            try:
                search_page_html = Scraper(url=url)
            except:
                search_page_html = 'fail'
            if search_page_html == 'fail':
                print('Scraper fail')
                return 'fail'
            try:
                page_foreign_ids = search_page_skus(html=search_page_html,site_id=site_id,brand_name=name)
            except:
                page_foreign_ids = None
            if page_foreign_ids == None or len(page_foreign_ids) == 0:
                print('no page_foreign_ids found fail')
                return 'fail'

            try:
                sitebrand_id = new_sitebrands(site_id,brand_id)
            except:
                sitebrand_id = None

            if sitebrand_id == None:
                print('new sitebrands fail')
                return 'fail'

            #check if page_foreign_id / sitebrand_id combo exists



            try:
                print('try to scrape pages')
                for x in range(len(skus)):
                    print('page: '+str(x))
                    foreign_id = skus[x]
                    print('sku_id: '+str(sku_id))
                    print('sitebrand_id: '+str(sitebrand_id))

                    try:
                        page_id = scrape_page(page_id=None,sitebrand_id=sitebrand_id,sku_id=sku_id,refresh=1)['id']
                    except:
                        page_id = 'fail'

                    if page_id == 'fail':
                        print('upload sku '+str(x)+' failed!')
                        return 'fail'
            except:
                print('handle skus fail')
                return 'fail'
    return {'result':'pass','id':brand_id}




def search_page_skus(html,site_id,brand_name):
    print('search_page_item_count()')
    brand_name = brand_name.lower()
    print('brand name: '+str(brand_name))
    print('site id: '+str(site_id))
    print('html: '+str(html))
    matches = None
    if site_id == 1:
        regex = r'data-item-id="[A-Z0-9]*".*?href="\/ip\/(.*?)\/(\d*)'
        matches = re.findall(regex,html)
    print('matches: '+str(matches))
    sku_ids = []
    if matches:
        for x in range(len(matches)):
            match = matches[x]
            sku_id = match[1]
            sku_name = match[0]
            sku_name = sku_name.replace('-',' ')
            sku_name = sku_name.lower()
            if brand_name in sku_name and sku_id not in sku_ids:
                sku_ids.append(sku_id)

    return sku_ids


def get_query_url(site,string,page=1):
    string = "+".join(w.capitalize() for w in string.split())
    page = str(page)

    url = None
    if site == 1:
        url = "https://www.walmart.com/search?q="+string+"&page="+page

    return url

def new_sitebrands(site_id,brand_id):
    print('new_sitebrands()')
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT `sitebrand_id` AS `sitebrand_id` FROM `sitebrands` WHERE `site_id` = %s AND `brand_id` = %s ORDER BY sitebrand_id DESC LIMIT 1'
            cursor.execute(sql,(site_id,brand_id))
            existing_sitebrand = cursor.fetchone()
    except:
        connection.close()
        print('existing sitebrand fail')
        return 'fail'

    if existing_sitebrand:
        print('brand already exists')
        connection.close()
        return existing_sitebrand['sitebrand_id']

    try:
        with connection.cursor() as cursor:
            sql = 'INSERT INTO `sitebrands` (`site_id`,`brand_id`) VALUES (%s,%s)'
            cursor.execute(sql,(site_id,brand_id))
        connection.commit()
    except:
        print('insert new sitebrand fail')
        connection.close()
        return 'fail'

    try:
        with connection.cursor() as cursor:
            sql = 'SELECT `sitebrand_id` AS `sitebrand_id` FROM `sitebrands` WHERE `site_id` = %s AND `brand_id` = %s ORDER BY sitebrand_id DESC LIMIT 1'
            cursor.execute(sql,(site_id,brand_id))
            row = cursor.fetchone()
            sitebrand_id = row['sitebrand_id']
    except:
        print('get new sitebrand id fail')
        return 'fail'
    finally:
        connection.close()
    return sitebrand_id

def scrape_brand(name):
    print('scrape_brand()')
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT `brand_id` as `brand_id` FROM `brands` WHERE `user_id` = %s AND `name` = %s ORDER BY `created` DESC LIMIT 1'
            cursor.execute(sql,(current_user.id,name))
            existing_brand = cursor.fetchone()
    except:
        connection.close()
        print('existing brand fail')
        return 'fail'

    if existing_brand:
        print('brand already exists')
        connection.close()
        return existing_brand['brand_id']

    try:
        with connection.cursor() as cursor:
            sql = 'INSERT INTO `brands` (`user_id`,`name`) VALUES (%s,%s)'
            cursor.execute(sql,(current_user.id,name))
        connection.commit()
    except:
        print('insert new brand fail')
        connection.close()
        return 'fail'

    try:
        with connection.cursor() as cursor:
            sql = 'SELECT `brand_id` AS `brand_id` FROM `brands` WHERE user_id = %s AND `name` = %s ORDER BY `brand_id` DESC LIMIT 1'
            cursor.execute(sql,(current_user.id,name))
            row = cursor.fetchone()
            brand_id = row['brand_id']
    except:
        print('get new brand id fail')
        return 'fail'
    finally:
        connection.close()
    return brand_id


def submit_dashboard(output):
    print('submit_dashboard()')
    print('Output: '+str(output))


def submit_walmart(output):
    print('submit_walmart()')
    print('Output: '+str(output))
    foreign_id = output['foreign_id']
    current_page_id = output['page_id']

    return scrape_site(site_id=1,item_id=foreign_id,current_page_id=current_page_id)


def submit_admin(output):
    user_id = output['user_id']
    action = output['action']

    connection = getConnection()

    try:
        if action == '0':
            with connection.cursor() as cursor:
                sql = 'UPDATE `users` SET `approved` = %s WHERE `user_id` = %s'
                cursor.execute(sql,(action,user_id))
                connection.commit()
        elif action == '1':
            grant_access(user_id)
    finally:
        connection.close()

    return 'pass'

def submit_register(output):
    username = output['username']
    psw = output['psw']
    code = output['code']

    psw = generate_password_hash(psw)

    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'UPDATE `users` SET `username` = %s,`psw` = %s WHERE `access_code` = %s'
            cursor.execute(sql,(username,psw,code))
            connection.commit()
    except:
        return 'fail'
    return 'pass'

def submit_login(output):
    connection = getConnection()
    username = output['username']
    psw = output['psw']

    try:
        # Try loggin in with email
        with connection.cursor() as cursor:
            sql = 'SELECT `user_id`, `psw` FROM `users` WHERE `email` = %s ORDER BY `user_id` ASC LIMIT 1'
            cursor.execute(sql,(username))
            row = cursor.fetchone()

        #if user not found, try with username
        if row == None:
            with connection.cursor() as cursor:
                sql = 'SELECT `user_id`, `psw` FROM `users` WHERE `username` = %s ORDER BY `user_id` ASC LIMIT 1'
                cursor.execute(sql,(username))
                row = cursor.fetchone()
    except:
        row = None
    finally:
        connection.close()
        #user is unkown
        if row == None:
            return 'user unknown'
        elif check_password_hash(pwhash=row['psw'],password=psw) != True:
            return 'invalid_password'
        else:
            user = User(row['user_id'])
            login_user(user)
            return 'pass'

def submit_change_password(output):
    print('submit_change_password running')
    try:
        psw = str(output['psw'])
        pwhash = generate_password_hash(psw)
    except:
        print('fail hashing psw')
        return 'fail'
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'UPDATE `users` SET `psw` = %s WHERE `user_id` = %s'
            cursor.execute(sql,(pwhash,current_user.id))
        connection.commit()
        connection.close()
        return 'pass'
    except:
        print('fail updating psw')
        connection.close()
        return 'fail'



def submit_access(output):
    connection = getConnection()
    keys = ', '.join(['`{}`'.format(w) for w in list(output.keys())])
    place_holders = ', '.join(['%s']*len(list(output.values())))
    try:
        with connection.cursor() as cursor:
            sql = 'INSERT INTO `users` ('+keys+') VALUES ('+place_holders+')'
            cursor.execute(sql,(list(output.values())))
        connection.commit()

        text_body = ', '.join(['{}'.format(w) for w in [output['first_name'],output['last_name'],output['email']]])
        text_response = text(text_body)

        return 'pass'
    except:
        return 'fail'
    finally:
        connection.close()

def grant_access(user_id):
    connection = getConnection()

    try:
        with connection.cursor() as cursor:
            sql = 'SELECT `user_id`, `email`, `first_name`, `last_name`, `company_name` FROM `users` WHERE user_id = %s'
            cursor.execute(sql,(user_id))
            row = cursor.fetchone()

        if row is None:
            return 'user_id unkown'

        code = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        with connection.cursor() as cursor:
            sql = 'UPDATE `users` SET `access_code` = %s, `approved` = %s WHERE `user_id` = %s'
            cursor.execute(sql,(code,1,user_id))
            connection.commit()

        send_email(subject='[SKU Perfect] Welcome!',
                sender='admin@skuperfect.com',
                recipients=row['email'].split(),
                text_body=render_template('welcome.txt',first_name=row['first_name'],code=code),
                html_body=render_template('welcome.html',first_name=row['first_name'],code=code))

    finally:
        connection.close()


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

def Scraper(url):
    print('Scraper()')
    print(url)

    payload = {'api_key': '******', 'url':url, 'render': 'true'}
    start_time = time.time()
    try:
        r = requests.get('http://api.scraperapi.com', params=payload)
    except:
        print('scraper fail')
        return 'fail'

    try:
        duration = round(time.time()-start_time,2)
    except:
        print('timer fail')
        return 'fail'

    try:
        html = r.text
    except:
        print('get text fail')
        return 'fail'


    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'INSERT INTO `scraper` (`user_id`,`duration`) VALUES (%s,%s)'
            cursor.execute(sql,(current_user.id,duration))
            connection.commit()
    except:
        print('insert scraper fail')
        return 'fail'
    finally:
        connection.close()
    print('html is a go')
    return html

def walmart_images(html):
    print('walmart_images()')
    print('HTML Length: '+str(len(html)))
    start_section = '<div class="ma2'
    start = html.find(start_section)

    if start == -1:
        print('start not found')
        return 'fail'

    print('start: '+str(start))
    html = html[start:]
    end_section = '<div class="mr3'
    end = html.find(end_section)
    print('end: '+str(end))

    if end == -1:
        print('end not found')
        return 'fail'

    html = html[:end]
    print('html: '+str(html))
    images = re.findall('(src=")(.*?)(.jpeg)', html)
    print('Images: '+str(images))
    if len(images) < 1:
        print('missing files')
        return 'fail'

    urls = []
    for image in images:
        image = image[1]
        urls.append(image)

    return urls

site_list = ['walmart']

def get_page_id(sku_id,sitebrand_id):
    print('get_page_id()')
    print('sku_id: '+str(sku_id))
    print('sitebrand_id: '+str(sitebrand_id))
    connection = getConnection()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT page_id FROM pages p WHERE p.sku_id = %s AND p.sitebrand_id = %s ORDER BY `page_id` DESC LIMIT 1'
            cursor.execute(sql(sku_id,sitebrand_id))
            page = cursor.fetchone()
    except:
        print('get page id function query fail!')
        connection.close()
        return 'fail'

    if page_id == None:
        return 'fail'
    else:
        return page_id


def scrape_page(page_id=None,sitebrand_id=None,sku_id=None,refresh=1):
    print('scape_page()')
    page = None
    # check if the page exists
    if page_id is not None and sitebrand_id is None and sku_id is None:
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT sb.site_id AS `site_id`, sb.sitebrand_id AS `sitebrand_id`, p.foreign_id AS `item_id` FROM `pages` p LEFT JOIN sitebrands sb ON sb.sitebrand_id = p.sitebrand_id WHERE p.page_id = %s'
                cursor.execute(sql,(page_id))
            page = cursor.fetchone()
        except:
            print('querying page fail')
            connection.close()
            return 'fail'
        if page:
            try:
                sitebrand_id = page['sitebrand_id']
                sku_id = page['sku_id']
                item_id = page['item_id']
                site_id = page['site_id']
            except:
                print('scrape page by page_id fail')
                connection.close()
                return 'fail'
    elif page_id is None and sitebrand_id is not None and sku_id is not None:
        print('sku_id: '+str(sku_id))
        print('sitebrand_id: '+str(sitebrand_id))
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT p.page_id, p.foreign_id AS `item_id`, sb.site_id FROM pages p LEFT JOIN sitebrands sb ON sb.sitebrand_id = p.sitebrand_id WHERE p.sku_id = %s AND p.sitebrand_id = %s ORDER BY p.page_id DESC LIMIT 1'
                cursor.execute(sql(sku_id,sitebrand_id))
                page = cursor.fetchone()
        except:
            print('get page id query fail!')
            connection.close()
            return 'fail'
        if page:
            try:
                page_id = page['page_id']
                item_id = page['item_id']
                site_id = page['site_id']
            except:
                print('scrape page by sitebrand_id and sku_id fail')
                connection.close()
                return 'fail'
    else:
        print('paramaters failed ya')

    # if page does not exist, create it
    if page == None:
        age = 'new'
        try:
            modified = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            with connection.cursor() as cursor:
                sql = 'INSERT INTO `pages` (`sitebrand_id`,`foreign_id`,`modified`) VALUES (%s,%s,%s)'
                cursor.execute(sql,(sitebrand_id,item_id,modified))
                connection.commit()
        except:
            print('new page error')
            connection.close()
            return 'fail'

        #and then define page_id
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT p.page_id as `page_id`, p.foreign_id AS `item_id`, sb.site_id AS `site_id` FROM pages p LEFT JOIN sitebrands sb ON sb.sitebrand_id = p.sitebrand_id WHERE `sitebrand_id` = %s AND `foreign_id` = %s ORDER BY page_id DESC LIMIT 1'
                cursor.execute(sql,(sitebrand_id,item_id))
                page = cursor.fetchone()
        except:
            print('find page id error')
            connection.close()
            return 'fail'

        if page == None:
            print('query define page fail!')
            connection.close()
            return 'fail'
        else:
            try:
                page_id = page['page_id']
                item_id = page['item_id']
                site_id = page['site_id']
            except:
                print('scrape defined fail!')
                connection.close()
                return 'fail'
    else:
        age = 'duplicate'

    if site_id == 1:
        print('scrape walmart page')
        item_id = str(item_id)
        url = 'https://www.walmart.com/ip/'+item_id
        image_size = '250'
    else:
        print('no site specified')
        connection.close()
        return 'fail'

    # if not, scrape!
    if age == 'new':
        print('age -- new')
        #scrape!
        try:
            try:
                html = Scraper(url)
            except:
                print('Scraper func fail')
                return 'fail'
            print('test')
            print('great success')
            print('Site List: '+str(site_list))
            print('Site ID: '+str(site_id))
            site = site_list[int(site_id)-1]
            print('Site: '+str(site))
            site_func = site+'_images'
            print('Site function: '+site_func)
            urls = globals()[site_func](html=html)
            if urls == 'fail':
                print('urls fail')
                return 'fail'
            print('URLs :'+str(urls))
        except:
            print('scrape fail')
            return 'fail'

        try:
            if len(urls) < 1:
                print('no images')
                return 'fail'
        except:
            print('count images fail')
            return 'fail'
        image_count = 0
    elif age == 'duplicate':
        print('age -- duplicate')
        page_id = int(page_id)

        if refresh == 0:
            result = {'result':'pass','id':page_id}
            print('duplicate -- stop')
            connection.close()
            return result

        #scrape!
        try:
            print('test 1')
            html = Scraper(url)
            if html == 'fail':
                print('scraper function fail')
                return 'fail'
            print('Site list: '+str(site_list))
            print('Site ID: '+str(site_id))
            site = site_list[int(site_id)-1]
            print('Site: '+str(site))
            site_func = site+'_images'
            urls = globals()[site_func](html=html)

            if urls == 'fail':
                print('urls fail')
                return 'fail'

        except:
            print('scrape fail')
            return 'fail'

        try:
            if len(urls) < 1:
                print('no images')
                return 'fail'
        except:
            print('count images fail')
            return 'fail'

        #if created update modified to current time
        modified = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with connection.cursor() as cursor:
                sql = 'UPDATE `pages` SET `modified` = %s WHERE `page_id` = %s'
                cursor.execute(sql,(modified,page_id))
                connection.commit()
        except:
            print('update page error')
            return 'fail'

    #delete existing images
    try:
        print('PAGE ID: '+str(page_id))
        with connection.cursor() as cursor:
            sql = 'DELETE FROM `images` WHERE `page_id` = %s'
            cursor.execute(sql,(page_id))
            connection.commit()
    except:
        print('delete existing images error')
        connection.close()
        return 'fail'

    #insert new images
    try:
        print(urls)
        for x in range(len(urls)):
            url = urls[x]
            with connection.cursor() as cursor:
                sql = 'INSERT INTO `images` (`page_id`,`url`) VALUES (%s,%s)'
                print(sql)
                cursor.execute(sql,(page_id,url))
                connection.commit()
    except:
        print('insert new images error')
        connection.close()
        return 'fail'


    #get image_ids
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT i.image_id AS `image_id`, i.url AS `url` FROM `images` i LEFT JOIN `pages` p ON p.page_id=i.page_id WHERE p.page_id = %s'
            cursor.execute(sql,(page_id))
            rows = cursor.fetchall()
    finally:
        connection.close()

    print('Image Rows: '+str(rows))

    try:
        for x in range(len(rows)):
            image_id = rows[x]['image_id']
            url = rows[x]['url']
            try:
                final_url = url+'.jpeg?'+'odnWidth='+image_size+'&odnHeight='+image_size+'&odnBg=ffffff'
                print(final_url)
            except:
                connection.close()
                print('error pasting url')
                return 'fail'
            try:
                file_name = str(image_id)+'.jpg'
                print(file_name)
                file_location = 'app/static/images/'+file_name
            except:
                print('file naming pasting url')
                return 'fail'

            try:
                img_data = requests.get(final_url).content
                with open(file_location, 'wb') as handler:
                    handler.write(img_data)
            except:
                print('failed to write: '+str(x))
                return 'fail'
    except:
        print('failed writing section')
        return 'fail'

    result = {'result':'pass','id':page_id}
    print(result)

    return result



#scraping iphone
@bp.route('/iphone/<section>',methods=['GET','POST'])
@bp.route('/iphone',methods=['GET','POST'],defaults={'section':None})
def iphone(section):
    return render_template('iphone.html',section=section)

@bp.route('/scrape_apple',methods=['POST'])
def scrape_apple():
    zip_code = str(request.json['zip'])
    color = str(request.json['color'])
    gb = str(request.json['gb'])
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    try:
        url = "https://www.apple.com/shop/buy-iphone/iphone-13-pro/6.7-inch-display-"+gb+"gb-"+color+"-verizon"
        print('URL: '+url)
        driver.get(url)
        #print('page loaded')
        try:
            trade_in_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "noTradeIn_label")))
            #print('located trade in element')
        except:
            print('error locating trade in element')
            driver.quit()
            return 'fail'

        try:
            trade_in_element.click()
            #print('clicked trade in element')
        except:
            print('error clicking trade in element')
            driver.quit()
            return 'fail'

        try:
            pickup_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[5]/div[4]/div[2]/div[3]/div[2]/div[6]/div[1]/div/div[2]/div/div/div[2]/div/div/span[2]/button")))
            #print('located pickup element')
        except:
            print('error locating pickup element')
            driver.quit()
            return 'fail'

        try:
            pickup_element.click()
            #print('clicked pickup element')
        except:
            print('error clicking pickup element')
            driver.quit()
            return 'fail'

        try:
            zip_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.rf-productlocator-form-textinput")))
            #print('zip element found')
        except:
            print('error clicking zip element')
            driver.quit()
            return 'fail'

        try:
            zip_element.send_keys(zip_code)
            zip_element.send_keys(Keys.RETURN)
        except:
            print('error entering zip')
            driver.quit()
            return 'fail'

        try:
            locator_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div/div/div/div/div[2]/div[2]/div[1]/div[1]/div[2]/div[2]/button/span[1]")))
        except:
            print('error locating locator element')
            driver.quit()
            return 'fail'

        try:
            result = 0
            if locator_element.text != 'Not available today at 12 nearest stores.':
                result = 1
            #print('Modal availability: '+locator_element.text)
        except:
            print('error getting locator text')
            driver.quit()
            return 'fail'
        finally:
            driver.quit()
            return result
    except:
        print('error loading page')
        driver.quit()
        return 'fail'

#!/usr/bin/env python3

import sqlite3
import wptools  # WikiPage Tools lib
import re
from bs4 import BeautifulSoup


class CrawlWikipedia:
    def __init__(self, db_file):
        """ 
        Initialize the crawler class for getting data from Wikipedia.
        Setup a small SQLite DB in file.

            Wikipedia pages are "members" of "categories"
        """        
        self.categories = []
        # Create DB
        print('Use DB file {}'.format(db_file))
        self.conn = sqlite3.connect(db_file)
        cursor = self.conn.cursor()
        # Create Table for Pages
        cursor.execute('CREATE TABLE IF NOT EXISTS content (pageid text, category text, url text, content text)')    
        self.conn.commit()
        self.cursor = self.conn.cursor()


    def save_page_content(self, category, pageid, url, content):
        self.cursor.execute('INSERT INTO content VALUES (?, ?, ?, ?)', (pageid, category, url, content))
        self.conn.commit()

    def get_page_urls(self):
        return [url for url in self.cursor.execute('SELECT url FROM content')]

    def get_page_ids(self):
        return [pageid for pageid in self.cursor.execute('SELECT pageid FROM content')]

    def get_categories_and_members(self, category, depth):
        """
        Start with the defined category and download Wikipedia content
        up to a set depth of categories.
        """
        print(u'Checking for subcategories of {} at depth {}'.format(category, depth))

        if depth:
            # Get Details and Members of this Category
            cat = wptools.category(category) 
            cat_members = cat.get_members()

            print(u'cat_members: {}'.format(cat_members.data))
            print(u'cat_members_keys: {}'.format(cat_members.data.keys()))

            # 1 - save any pages (members) for this category
            if 'members' in cat_members.data.keys():
                for cat_member in cat_members.data['members']:
                    print(u'member: {}'.format(cat_member))
                    # IF NOT already saved...
                    if cat_member['pageid'] not in self.get_page_ids():
                        # Get the page Content
                        page = wptools.page(pageid=cat_member['pageid']).get_parse()
                        
                        url = page.get_query().data['url']
                        # CLEAN: remove HTML syntax and <ref>
                        text = BeautifulSoup(page.data['wikitext'], 'html.parser').get_text()
                        # CLEAN: remove markup such as [[...]] and {{...}}
                        clean_text = re.sub(r'\s*{.*}\s*|\s*[.*]\s*', '', text)

                        # Save/storethe page
                        print('Saving pageid {} / url {}'.format(cat_member['pageid'], url))
                        self.save_page_content(category, cat_member['pageid'], url, clean_text)

            # 2 - iterate through any subcategories
            if 'subcategories' in cat_members.data.keys():
                subcats = cat_members.data['subcategories']

                for subcat in subcats:
                    self.categories.append(subcat)

                    # RECURSE: Until depth reached on pages
                    self.get_categories_and_members(subcat['title'], depth - 1)

            # INFO
            for cat in self.categories:
                print(u'Category: {}'.format(cat))
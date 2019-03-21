import glob
import ntpath
import datetime
import os
from pymongo import MongoClient
from bs4 import BeautifulSoup 
import re

def load_malts_hops_list():
    tmp_hops_list=[]
    tmp_malts_list=[]
    with open('/home/bcarter/DSI/capstones/machine_learning/hops_list.txt') as f:
        for row in f.read().split('\n'):
            if len(row) > 0:
                tmp_hops_list.append(row)
    with open('/home/bcarter/DSI/capstones/machine_learning/malts_list3.txt') as f:
        for row in f.read().split('\n'):
            if len(row) > 0:
                tmp_malts_list.append(row)
    
    return tmp_hops_list, tmp_malts_list
    
def load_mongo(recipe_name, beer_style, recipe_ingredients, recipe_instructions,malts,hops,yeast, keywords):
    post = {"recipe": recipe_name,
            "style": beer_style,
            "ingredients": ''.join(map(str, recipe_ingredients)),
            "instructions": recipe_instructions,
            "malts": malts,
            "hops": hops,
            "yeast": yeast,
            "keywords": keywords,
            "date": datetime.datetime.utcnow()}   
    print('Inserting into Mongo')
    db["beer_recipes_keywords4"].insert_one(post)
    
def process_html_files(contents):
            soup = BeautifulSoup(contents, 'html.parser')
            beer_style=str(soup.find_all('h3')).split('"recipeCuisine">')[1].split('</a></h3>')[0]
            if re.search('mead', beer_style, re.IGNORECASE):
                return None
            if re.search('cider', beer_style, re.IGNORECASE):
                return None
            recipe_name=str(soup.find_all('h3')).split('|')[0].split('<h3>')[1]
            if re.search('mead',recipe_name, re.IGNORECASE):
                return None
            if re.search('cider',recipe_name, re.IGNORECASE):
                return None
            recipe_ingredients=str(soup.find('div', itemprop="ingredients").get_text()).strip().replace('|','')
            recipe_instructions=soup.find('div',itemprop="recipeInstructions").get_text()
            specifications= soup.find(class_="specs").get_text()
            malts=[]
            hops=[]
            other_ingredients=[]
            yeast=[]
            keywords=[]
            for row in recipe_ingredients.split('\n'):
            
                if 'malt' in row.lower() or 'barley' in row.lower():
                    row=re.sub('flaked wheat', 'flaked_wheat', row, re.IGNORECASE)
                    row=re.sub('flaked oats', 'flaked_oats', row, re.IGNORECASE)
                    row=re.sub('rice flakes', 'rice_flakes', row, re.IGNORECASE)
                    for malt in malts_list:
                        if re.search(malt, row.lower(), re.IGNORECASE):
                            if malt not in malts:
                                malts.append(malt)
                                keywords.append(malt)
                elif 'hop' in row.lower() or 'pellets,' in row.lower() or 'min)' in row.lower():
                    for hop in hops_list:
                        if re.search(hop, row, re.IGNORECASE):
                            if hop not in hops:
                                hops.append(hop.replace(' ','_'))
                                keywords.append(hop.replace(' ','_'))
                elif 'yeast' in row.lower() or 'White Labs' in row or 'Wyeast' in row:
                    if 'YEAST' in row:
                        continue
                    if len(row) > 1:
                        match=re.search('Wyeast.....', row)
                        if match:
                            yeast.append(row[match.start():match.end()])
                            keywords.append(row[match.start():match.end()])
                        match=re.search('WLP...', row)
                        if match:
                            yeast.append(row[match.start():match.end()])
                            keywords.append(row[match.start():match.end()])  
                        match=re.search('Wyeast No......',row) 
                        if match:
                            yeast.append(row[match.start():match.end()])
                            keywords.append(row[match.start():match.end()]) 
                        match=re.search('Wyeast B..*', row)
                        if match:
                            row=re.sub(r'\([^)]*\)', '', row, re.IGNORECASE)
                            yeast.append(row[match.start():match.end()])
                            keywords.append(row[match.start():match.end()]) 

                else:
                      if row not in other_ingredients:    
                        other_ingredients.append(row)
                    
            load_mongo(recipe_name, beer_style, recipe_ingredients, recipe_instructions,malts,hops,yeast, keywords)

if __name__ == '__main__':
    hops_list=[]
    malts_list=[]
    hops_list, malts_list=load_malts_hops_list()
    client = MongoClient('localhost', 27017)
    db = client.beer_recipes
    file_list=[]
    file_list=glob.glob("/mnt/c/Users/bcarter/Downloads/beer_recipes/xml/recipes2/*")
    for fn in file_list:
        dir_path,file_name=ntpath.split(fn)
        with open(fn) as f:
            contents = f.read()
            process_html_files(contents)

   

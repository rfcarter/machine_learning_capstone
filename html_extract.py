import glob
import ntpath
import datetime
import os
from pymongo import MongoClient
from bs4 import BeautifulSoup 
import re
from nltk.stem import PorterStemmer 
from nltk.tokenize import word_tokenize 
from nltk.stem import WordNetLemmatizer 
from nltk.corpus import stopwords 
import string
    
def build_stop_words():
    stop_words = stopwords.words('english') + list(string.punctuation)
    with open ('../data/grains/manufactors.txt','r') as fn:
        for line in fn:
            tmp_str=str(line).lower().replace('\n','')
            stop_words.append(tmp_str)
    return(stop_words)

def load_mongo(recipe_name, beer_style, recipe_ingredients, recipe_ingredients_stemmed, recipe_ingredients_spacy, recipe_instructions,recipe_specifications,ABV, IBU, SRM, keywords):
    post = {"recipe": recipe_name,
            "style": beer_style,
            "ingredients": ''.join(map(str, recipe_ingredients)),
            "ingredients_stemmed" : recipe_ingredients_stemmed,
            "ingredients_spacy" : recipe_ingredients_spacy,
            "instructions": recipe_instructions,
            "specifications": recipe_specifications,
            "ABV": ABV,
            "IBU": IBU,
            "SRM": SRM,
            "keywords": keywords,
            "date": datetime.datetime.utcnow()}   
    print('Inserting into Mongo')
    db["beer_recipes_abv"].insert_one(post)
    
def connect_mongo():
    client = MongoClient('localhost', 27017)
    return client.beer_recipes
                
def stem_words(input_text):
    return_list=[]
    ps = PorterStemmer() 
    lm = WordNetLemmatizer() 
    words = word_tokenize(input_text) 
    for w in words: 
        if w.lower() not in stop_words: 
            return_list.append(lm.lemmatize(ps.stem(w)))
    return return_list
    
def spacy(input_text):
    import spacy
    doc=''
    nlp = spacy.load('en', disable=['parser', 'ner'])
    for w in input_text.split(): 
        if w.lower() not in stop_words: 
            doc = doc + ' ' + w
    doc_spacy = nlp(doc)

    # Extract the lemma for each token and join
    return " ".join([token.lemma_ for token in doc_spacy])
    
def process_html_files(contents):
    ABV=''
    IBU=''
    SRM=''
    keywords=[]
    specifications=[]
    soup = BeautifulSoup(contents, 'html.parser')
    beer_style=str(soup.find_all('h3')).split('"recipeCuisine">')[1].split('</a></h3>')[0]
    if re.search('mead', beer_style, re.IGNORECASE):
        return None
    if re.search('cider', beer_style, re.IGNORECASE):
        return None
    recipe_name=str(soup.find('h3')).split('|')[0].replace('<h3>','').strip()
    if re.search('mead',recipe_name, re.IGNORECASE):
        return None
    if re.search('cider',recipe_name, re.IGNORECASE):
        return None
    recipe_ingredients=str(soup.find('div', itemprop="ingredients").get_text()).strip().replace('|','')
    recipe_ingredients_stemmed=stem_words(recipe_ingredients)
    recipe_ingredients_spacy=spacy(recipe_ingredients)
    recipe_instructions=soup.find('div',itemprop="recipeInstructions").get_text()
    recipe_specifications= soup.find(class_="specs").get_text()
    recipe_specifications=re.sub(r' ', '', recipe_specifications)
    recipe_specifications=re.sub(r'n/a', ' n/a ', recipe_specifications)
    recipe_specifications=re.sub(r'ABV', ' ABV ', recipe_specifications)
    recipe_specifications=re.sub(r'IBU', ' IBU ', recipe_specifications)
    recipe_specifications=re.sub(r'SRM', ' SRM ', recipe_specifications)
    recipe_specifications=re.sub(r'Boil', ' Boil ', recipe_specifications)
    recipe_specifications=re.sub(r'Efficiency',' Efficiency', recipe_specifications)
    recipe_specifications=re.sub(r'byvolume', ' byvolume', recipe_specifications)
    specifications=recipe_specifications.split()
    if specifications:
        for idx,row in enumerate(specifications):
            if 'ABV' in row:
                ABV=specifications[idx+1].replace(':','').replace('%','')
            if 'IBU' in row:
                IBU=specifications[idx+1].replace(':','')
            if 'SRM' in row:
                SRM=specifications[idx+1].replace(':','')
        if ABV and IBU and SRM:
            keywords.append(ABV)
            keywords.append(IBU)
            keywords.append(SRM)
            keywords.append(beer_style)
            load_mongo(recipe_name, beer_style, recipe_ingredients, recipe_ingredients_stemmed, recipe_ingredients_spacy, recipe_instructions,recipe_specifications, ABV, IBU, SRM, keywords)

if __name__ == '__main__':
    db = connect_mongo()
    file_list=[]
    file_list=glob.glob("/mnt/c/Users/bcarter/Downloads/beer_recipes/xml/recipes2/index.html*")
    stop_words=build_stop_words()
    for fn in file_list:
        with open(fn) as f:
            contents = f.read()
            process_html_files(contents)
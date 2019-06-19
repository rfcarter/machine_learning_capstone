from flask import Flask, render_template, request, jsonify
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.beer_recipes
styles_list=db["beer_recipes_keywords4"].distinct("style")

with open('data/cosine_sim.pickle', 'rb') as f:
    cosine_sim = pickle.load(f)

with open('data/indices.pickle', 'rb') as f:
    indices = pickle.load(f)

recipe_list=[]
coll = db.beer_recipes_keywords4
for x in coll.find({}, {"recipe": 1 , "keywords": 1 , "ingredients" :1, "instructions" :1, "_id": 0}):
   recipe_list.append((x['recipe'], str(x['keywords']).strip('[]'),x['ingredients'],x['instructions']))
labels = ['recipe', 'keywords', 'ingredients', 'instructions']
df = pd.DataFrame.from_records(recipe_list, columns=labels)

def get_recommendations(recipe, cosine_sim=cosine_sim):
    
    idx = indices[recipe]
    sim_scores = list(enumerate(cosine_sim[idx]))
    if len(sim_scores) >= 5:
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:5]
    else:
        return('No Matches')
    beer_indices = [i[0] for i in sim_scores]
    return beer_indices
    
@app.route('/', methods=['GET'])
def index():
    return render_template('form/index.html')

@app.route('/beer', methods=['GET'])
def beer():
    return render_template('form/beer.html',styles_list=styles_list)
    
@app.route('/get_recipes')
def get_recipes():
    beer_style = request.args.get('beer_style')
    recipe_list=[]
    recipes_dict=db["beer_recipes_keywords4"].find({"style" : beer_style},{"recipe":1, "_id":0})
    for recipe in recipes_dict:
        recipe_list.append(recipe['recipe'])
    return (jsonify(['Select a Recipe...'] + sorted(recipe_list)))    

@app.route('/recommendations',methods=['GET','POST'])
def recommendations():
    recipe_name = request.form['recipe']
    recommend_list_idx=get_recommendations(recipe_name)
    recipe_list=[]
    for idx in recommend_list_idx:
               recipe_list.append(df.recipe.iloc[idx])
    return render_template('form/recommedations.html', recipe_list=recipe_list)
    
@app.route('/recipe',methods=['GET','POST'])
def recipe():
    recipe_name = request.form.get('recipe_name')
    idx=indices[recipe_name]
    ingredients_list=[]
    instruction_list=[]
    recipe_str = ''
    recipes_dict=db["beer_recipes_keywords4"].find({"recipe": recipe_name},{"ingredients":1, "_id":0})
    for value in recipes_dict:
        recipe_str += str(value)
    for row in recipe_str.split('\\n'):
        if len(row) > 2:
            ingredients_list.append(row.replace("{'ingredients': '","").replace("'}","").replace(".",""))
    recipes_dict=db["beer_recipes_keywords4"].find({"recipe": recipe_name},{"instructions":1, "_id":0})
    recipe_str = ''
    for value in recipes_dict:
        recipe_str += str(value)
    for row in recipe_str.split('\\n'):
        if len(row) > 2:
            instruction_list.append(row.replace("{'instructions': '","").replace("'}","").replace(".",""))
        return render_template('form/recipe.html',recipe_name=recipe_name,ingredients_list=ingredients_list,instruction_list=instruction_list)
    
    

if __name__ == '__main__':
    app.run(host='127.0.0.1',port=5002, debug=True)

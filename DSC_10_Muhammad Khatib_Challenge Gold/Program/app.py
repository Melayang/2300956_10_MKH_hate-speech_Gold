import re 
import pandas as pd 
import json
import sqlite3

from flask import Flask, jsonify, request, send_file
from flasgger import Swagger, LazyString, LazyJSONEncoder 
from flasgger import swag_from 


#read csv file, lalu di ubah ke list
df1 = pd.read_csv('new_kamusalay.csv')
dict1 = df1.to_dict('list') 
df2 = pd.read_csv('abusive.csv')
dict2 = df2.to_dict('list')

#Flask and swagger
app = Flask(__name__) 

swagger_config = { 
    "headers": [], 
    "specs": [ { "endpoint": 'docs', 
                 "route": '/docs.json'} ],
    "static_url_path": "/flasgger_static", 
    "swagger_ui": True, 
    "specs_route": "/docs/" 
} 
swagger = Swagger(app, config=swagger_config) 

def create_json_response(description, data):
    return {
        "status code": 200,
        "description": description,
        "data": data
    }


#metode get
@swag_from("docs/hello_world.yml", methods=['GET']) 
@app.route('/', methods=['GET']) 
def hello_world(): 
    json_response = create_json_response (description="menyapa hello wolrd",data="hello world2")
    response_data = jsonify(json_response) 
    return response_data

#Text processing 
@swag_from("docs/text_processing.yml", methods=['POST']) 
@app.route('/text-processing', methods=['POST']) 
def text_processing():
    text = request.args.get('text')
    text = re.sub(r'[^a-zA-Z0-9!.\s]', ' ', text)
    text = re.sub(r'\\+n', ' ', text)
    text = re.sub('user', ' ', text)
    text = re.sub(r'\n', " ", text)
    text = re.sub(r'(rt)', ' ', text)
    text = re.sub(r'((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))', ' ', text)
    text = re.sub(r'&amp;', 'dan', text)
    text = re.sub(r'&', 'dan', text)
    text = re.sub(r'%', ' persen ', text)
    text = re.sub(r'[^a-z ]', ' ', text)
    text = re.sub(r'  +', ' ', text)
    text = text.rstrip().lstrip()
    for typo, rev, abusive in zip(dict1['KATA'], dict1['REVISI'], dict2['ABUSIVE']):
            text  = re.sub(r'\b{}\b'.format(typo), rev, text)
            text  = re.sub(r'\b{}\b'.format(abusive), '', text)
            #save to sqlite
            conn = sqlite3.connect("cdatabase.db")
            conn.execute("CREATE TABLE if not exists text(text VARCHAR)")
            conn.execute("INSERT INTO text VALUES (?)", (json.dumps(text),))
            conn.commit()
            conn.close()
    json_response = create_json_response (description="text yang sudah di proses",data=text)
    response_data = jsonify(json_response) 
    return response_data

#data_cleansing
@swag_from("docs/data_cleansing.yml", methods=['POST']) 
@app.route('/data-cleansing', methods=['POST'])
def data_cleansing():
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        df = pd.read_csv(file)
        for typo, rev, abusive in zip(dict1['KATA'], dict1['REVISI'], dict2['ABUSIVE']):
            df['Tweet'] = df['Tweet'].str.replace('user', ' ', regex=True)
            df['Tweet'] = df['Tweet'].str.replace('USER', ' ', regex=True)
            df['Tweet'] = df['Tweet'].str.replace(r'\b{}\b'.format(typo), rev, regex=True)
            df['Tweet'] = df['Tweet'].str.replace(r'\b{}\b'.format(abusive), '', regex=True)
            df['Tweet'] = df['Tweet'].str.replace(r'\\+n', ' ', regex=True)
            df['Tweet'] = df['Tweet'].str.replace('user', ' ', regex=True)
            df['Tweet'] = df['Tweet'].str.replace(r'\n', " ", regex=True)
            df['Tweet'] = df['Tweet'].str.replace(r'(rt)', ' ', regex=True)
            df['Tweet'] = df['Tweet'].str.replace(r'((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))', ' ', regex=True)
            df['Tweet'] = df['Tweet'].str.replace(r'&amp;', 'dan', regex=True)
            df['Tweet'] = df['Tweet'].str.replace(r'&', 'dan', regex=True)
            df['Tweet'] = df['Tweet'].str.replace(r'%', ' persen ', regex=True)
            df['Tweet'] = df['Tweet'].str.replace(r'[^a-zA-Z]', ' ', regex=True)
            df['Tweet'] = df['Tweet'].str.replace(r'  +', ' ', regex=True)
            dicts = df.to_dict(orient='records')
            #save to sqlite
            conn = sqlite3.connect("cdatabase.db")
            conn.execute("CREATE TABLE if not exists tweet(text VARCHAR)")
            conn.execute("INSERT INTO tweet VALUES (?)", (json.dumps(dicts),))
            conn.commit()
            conn.close()
    json_response = create_json_response (description="Hasil file yang telah di bersihkan", data=dicts)
    response_data = jsonify(json_response)
    return response_data

if __name__ == '__main__':
    app.run()
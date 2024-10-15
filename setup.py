from pymongo import MongoClient
import pandas as pd

# MongoDB connection
client = MongoClient('mongodb://mongoadmin:password@localhost:27017/')
db = client['netflix_movies']  # Replace with your database name
collection = db['movies']  # Replace with your collection name

def fetch_data(filter_field=None, filter_value=None):
    query = {}
    if filter_field and filter_value:
        query = {filter_field: filter_value}
    
    data = list(collection.find(query))
    df = pd.DataFrame(data)
    return df


df = fetch_data(filter_field='release_year', filter_value = 2000)
print(df.head())

from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# MongoDB connection using your credentials
mongodb_service = os.environ.get('MONGODB_SERVICE', '172.21.102.166')
mongodb_username = os.environ.get('MONGODB_USERNAME', 'root')
mongodb_password = os.environ.get('MONGODB_PASSWORD', 'ThZdtHoGm61WEBDmctoSVe0R')
mongodb_port = os.environ.get('MONGODB_PORT', '27017')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

# Construct MongoDB connection URL
url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}:{mongodb_port}"

print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
    # Test the connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")
    sys.exit(1)
except Exception as e:
    app.logger.error(f"Connection error: {str(e)}")
    sys.exit(1)

db = client.songs
collection = db.songs

# Initialize database with sample data (only if empty)
if collection.count_documents({}) == 0:
    collection.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# HEALTH ENDPOINT - EXERCISE 1
######################################################################

@app.route("/health")
def health():
    return jsonify({"status": "OK"}), 200

######################################################################
# COUNT ENDPOINT - EXERCISE 1
######################################################################

@app.route("/count")
def count():
    """return count of all songs"""
    try:
        count = collection.count_documents({})
        return jsonify({"count": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

######################################################################
# GET ALL SONGS - EXERCISE 2
######################################################################

@app.route("/song", methods=["GET"])
def get_songs():
    """GET /song - Return all songs in format {'songs': list_of_songs}"""
    try:
        # Get all songs from MongoDB
        songs_cursor = collection.find({})
        songs_list = list(songs_cursor)
        
        # Return in the required format: {"songs": list_of_songs}
        return jsonify({"songs": parse_json(songs_list)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

######################################################################
# GET SONG BY ID - EXERCISE 3
######################################################################

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    """GET /song/<id> - Return specific song by ID"""
    try:
        song = collection.find_one({"id": id})
        if song:
            return jsonify(parse_json(song)), 200
        else:
            return jsonify({"message": "song with id not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

######################################################################
# CREATE A SONG - EXERCISE 4
######################################################################

@app.route("/song", methods=["POST"])
def create_song():
    """POST /song - Create a new song"""
    try:
        song_data = request.get_json()
        
        if not song_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Check if song with same ID already exists
        if "id" in song_data:
            existing_song = collection.find_one({"id": song_data["id"]})
            if existing_song:
                return jsonify({"Message": f"song with id {song_data['id']} already present"}), 302
        
        # Insert new song
        result = collection.insert_one(song_data)
        
        # Return the inserted ID as shown in the example
        return jsonify({"inserted id": parse_json(result.inserted_id)}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

######################################################################
# UPDATE A SONG - EXERCISE 5
######################################################################

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    """PUT /song/<id> - Update an existing song"""
    try:
        song_data = request.get_json()
        
        if not song_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Check if song exists
        existing_song = collection.find_one({"id": id})
        if not existing_song:
            return jsonify({"message": "song not found"}), 404
        
        # Update the song
        result = collection.update_one(
            {"id": id},
            {"$set": song_data}
        )
        
        # Check if anything was actually modified
        if result.modified_count > 0:
            # Return the updated song with 201 status for first update
            updated_song = collection.find_one({"id": id})
            return jsonify(parse_json(updated_song)), 201
        else:
            # Return message if nothing was updated
            return jsonify({"message": "song found, but nothing updated"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

######################################################################
# DELETE A SONG - EXERCISE 6
######################################################################

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    """DELETE /song/<id> - Delete a song by ID"""
    try:
        result = collection.delete_one({"id": id})
        
        if result.deleted_count == 0:
            return jsonify({"message": "song not found"}), 404
        
        # Return empty body with 204 status - NO CONTENT
        return "", 204
        
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
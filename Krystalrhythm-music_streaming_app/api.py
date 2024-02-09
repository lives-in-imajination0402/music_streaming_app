from flask_restful import Resource, reqparse,marshal_with,fields
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import  UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from flask import make_response
import json

db = SQLAlchemy()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///databaseapi.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your secret key'
api=Api(app)
CORS(app)
db.init_app(app)
app.app_context().push()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_creator = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_blacklisted = db.Column(db.Boolean, default=False)
    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    


class Album(db.Model):
    __tablename__ = 'album'
    id = db.Column(db.Integer, primary_key=True)
    album_name = db.Column(db.String(64), nullable=False)
    artist_name = db.Column(db.String(64), nullable=False)
    date = db.Column(db.String, nullable=False)
    
class NotFoundError(HTTPException):
    def __init__(self, status_code, message=''):
        self.response = make_response(message, status_code)

class NotGivenError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {"error_code": error_code, "error_message": error_message}
        self.response = make_response(json.dumps(message), status_code)


playlist = db.Table('playlist_songs',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id'), primary_key=True)
)

class Playlist(db.Model):
    __tablename__ = 'playlist'
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    songs = db.relationship('Songs', secondary=playlist, backref='playlist')
    playlist_name = db.Column(db.String,nullable=False)

class Songs(db.Model):
    __tablename__ = 'songs'
    id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(64), nullable=False)
    artist_name = db.Column(db.String(64), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    audio_data = db.Column(db.String)
    ratings = db.Column(db.Integer)
    genre = db.Column(db.String(64), nullable=False)
    lyrics = db.Column(db.String, nullable=False)
    flagged= db.Column(db.Boolean, default=False)
    album = db.relationship('Album', backref='songs')
    duration = db.Column(db.String, nullable=False)
    users_rated_count = db.Column(db.Integer, default=0)
    average_ratings = db.Column(db.Float, default=0.0)
    image_data = db.Column(db.String)

user_fields = {
    'id': fields.Integer,
    'username': fields.String,
    'email': fields.String,
    'is_creator': fields.Boolean,
    'is_admin': fields.Boolean,
    'is_blacklisted': fields.Boolean,
    'is_subscribed': fields.Boolean
}

album_fields = {
    'id': fields.Integer,
    'album_name': fields.String,
    'artist_name': fields.String,
    'date': fields.String
}

playlist_fields = {
    'id': fields.Integer,
    'author': fields.Integer,
    'playlist_name': fields.String
}

songs_fields = {
    'id': fields.Integer,
    'song_name': fields.String,
    'artist_name': fields.String,
    'album_id': fields.Integer,
    'user_id': fields.Integer,
    'audio_data': fields.String,
    'ratings': fields.Integer,
    'genre': fields.String,
    'lyrics': fields.String,
    'flagged': fields.Boolean,
    'duration': fields.String,
    'users_rated_count': fields.Integer,
    'average_ratings': fields.Float,
    'image_data': fields.String
}



user_parser = reqparse.RequestParser()
user_parser.add_argument('username')
user_parser.add_argument('email')
user_parser.add_argument('password')
user_parser.add_argument('is_creator')
user_parser.add_argument('is_admin')
user_parser.add_argument('is_blacklisted')




class UserAPI(Resource):

    @marshal_with(user_fields)
    def get(self, id):
        user = User.query.filter_by(id=id).first()
        if not user:
            raise NotFoundError(404, 'User not found')
        return user
    
    @marshal_with(user_fields)
    def put(self, id):
        args = user_parser.parse_args()
        user = User.query.filter_by(id=id).first()
        user.username = args['username']
        user.email = args['email']
        user.password_hash = generate_password_hash(args['password'])
        db.session.commit()
        return user
    
    @marshal_with(user_fields)
    def post(self):
        args = user_parser.parse_args()
        user = User(username=args['username'], email=args['email'],password_hash=generate_password_hash(args['password']))
        db.session.add(user)
        db.session.commit()
        return user, 201
    
    def delete(self, id):
        user = User.query.filter_by(id=id).first()
        db.session.delete(user)
        db.session.commit()
        return 'deleted', 200
    


api.add_resource(UserAPI, '/api/user/<int:id>', '/api/user')
    
album_parser = reqparse.RequestParser()
album_parser.add_argument('album_name')
album_parser.add_argument('artist_name')
album_parser.add_argument('date')

class AlbumAPI(Resource):
    @marshal_with(album_fields)
    def get(self, id):
        album = Album.query.filter_by(id=id).first()
        if not album:
            raise NotFoundError(404, 'Album not found')
        return album
    
    @marshal_with(album_fields)
    def put(self, id):
        args = album_parser.parse_args()
        album = Album.query.filter_by(id=id).first()
        album.album_name = args['album_name']
        album.artist_name = args['artist_name']
        album.date = args['date']
        db.session.commit()
        return album
    
    @marshal_with(album_fields)
    def post(self):
        args = album_parser.parse_args()
        album = Album(album_name=args['album_name'], artist_name=args['artist_name'],date=args['date'])
        db.session.add(album)
        db.session.commit()
        return album, 201
    
    def delete(self, id):
        album = Album.query.filter_by(id=id).first()
        db.session.delete(album)
        db.session.commit()
        return 'deleted', 200
    
api.add_resource(AlbumAPI, '/api/album/<int:id>', '/api/album')


playlist_parser = reqparse.RequestParser()
playlist_parser.add_argument('author')
playlist_parser.add_argument('playlist_name')

class PlaylistAPI(Resource):
    @marshal_with(playlist_fields)
    def get(self, id):
        playlist = Playlist.query.filter_by(id=id).first()
        if not playlist:
            raise NotFoundError(404, 'Playlist not found')
        return playlist
    
    @marshal_with(playlist_fields)
    def put(self, id):
        args = playlist_parser.parse_args()
        playlist = Playlist.query.filter_by(id=id).first()
        playlist.author = args['author']
        playlist.playlist_name = args['playlist_name']
        db.session.commit()
        return playlist
    
    @marshal_with(playlist_fields)
    def post(self):
        args = playlist_parser.parse_args()
        playlist = Playlist(author=args['author'], playlist_name=args['playlist_name'])
        db.session.add(playlist)
        db.session.commit()
        return playlist, 201
    
    def delete(self, id):
        playlist = Playlist.query.filter_by(id=id).first()
        db.session.delete(playlist)
        db.session.commit()
        return 'deleted', 200
    
api.add_resource(PlaylistAPI, '/api/playlist/<int:id>', '/api/playlist')

songs_parser = reqparse.RequestParser()
songs_parser.add_argument('song_name')
songs_parser.add_argument('artist_name')
songs_parser.add_argument('album_id')
songs_parser.add_argument('user_id')
songs_parser.add_argument('audio_data')
songs_parser.add_argument('ratings')
songs_parser.add_argument('genre')
songs_parser.add_argument('lyrics')
songs_parser.add_argument('flagged')
songs_parser.add_argument('duration')
songs_parser.add_argument('users_rated_count')
songs_parser.add_argument('average_ratings')
songs_parser.add_argument('image_data')

class SongsAPI(Resource):
    @marshal_with(songs_fields)
    def get(self, id):
        songs = Songs.query.filter_by(id=id).first()
        if not songs:
            raise NotFoundError(404, 'Songs not found')
        return songs
    
    @marshal_with(songs_fields)
    def put(self, id):
        args = songs_parser.parse_args()
        songs = Songs.query.filter_by(id=id).first()
        songs.song_name = args['song_name']
        songs.artist_name = args['artist_name']
        songs.album_id = args['album_id']
        songs.user_id = args['user_id']
        songs.audio_data = args['audio_data']
        songs.ratings = args['ratings']
        songs.genre = args['genre']
        songs.lyrics = args['lyrics']
        songs.flagged = False if args['flagged'] == "0" else True
        songs.duration = args['duration']
        songs.users_rated_count = args['users_rated_count']
        songs.average_ratings = args['average_ratings']
        songs.image_data = args['image_data']
        db.session.commit()
        return songs
    
    @marshal_with(songs_fields)
    def post(self):
        args = songs_parser.parse_args()
        
        songs = Songs(song_name=args['song_name'], artist_name=args['artist_name'],album_id=args['album_id'],user_id=args['user_id'],audio_data=args['audio_data'],ratings=args['ratings'],genre=args['genre'],lyrics=args['lyrics'],flagged=False,duration=args['duration'],users_rated_count=args['users_rated_count'],average_ratings=args['average_ratings'],image_data=args['image_data'])
        db.session.add(songs)
        db.session.commit()
        return songs, 201
    
    def delete(self, id):
        songs = Songs.query.filter_by(id=id).first()
        db.session.delete(songs)
        db.session.commit()
        return 'deleted', 200

api.add_resource(SongsAPI, '/api/songs/<int:id>', '/api/songs')


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
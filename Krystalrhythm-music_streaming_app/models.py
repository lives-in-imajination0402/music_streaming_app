from flask_sqlalchemy import SQLAlchemy
from flask_login import  UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()



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
    
    

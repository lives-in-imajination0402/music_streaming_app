from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import User, Songs, Album, Playlist, db
from decimal import Decimal
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your secret key'

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)

app.app_context().push()




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')



        
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'admin':
            
            admin_user = User.query.filter_by(username='admin').first()

            if admin_user:
                flash('Logged in successfully!', category='success')
                login_user(admin_user)
                return redirect(url_for('admin_dashboard'))

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            flash('Logged in successfully!', category='success')
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Incorrect username or password, try again!', category='error')

    return render_template("login.html", user=current_user)

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(username=username).first()
        if user:
            flash('username is already taken, try another username.', category='error')
        elif len(username) < 3 or len(email) < 6 or len(password1) < 7:
            flash('Invalid input. Please check your username, email, and password.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password1)
            db.session.add(new_user)
            db.session.commit()
            flash('Successfully signed up.', category='success')
            return redirect(url_for('login'))

    return render_template("register.html", user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/home',methods=['GET','POST'])
@login_required
def home():
    songs = Songs.query.order_by(Songs.id.desc()).limit(5).all()    
    genres = db.session.query(Songs.genre.distinct()).all()
    playlists = Playlist.query.filter_by(author=current_user.id).all()
    albums = Album.query.all()

    genre_songs = {}
    for genre in genres:
        genre_name = genre[0]
        genre_songs[genre_name] = Songs.query.filter_by(genre=genre_name).all()

    playlist_songs = {}
    for playlist in playlists:
        playlist_name = playlist.playlist_name
        playlist_songs[playlist_name] = Songs.query.join(Playlist.songs).filter(Playlist.id == playlist.id).all()
    
    album_songs = {}
    for album in albums:
        album_name = album.album_name
        album_songs[album_name] = Songs.query.filter_by(album_id=album.id).all()
    
    return render_template('dashboard.html',user=current_user,songs=songs,genre_songs=genre_songs,playlists=playlists,album_songs=album_songs)

@app.route('/all_songs',methods=['GET','POST'])
@login_required
def all_songs():
    songs = Songs.query.all()

    return render_template('all_songs.html',user=current_user,songs=songs)

@app.route('/become_creator',methods=['GET','POST'])
@login_required
def become_creator():
    return render_template('agreement.html')

@app.route('/become_creator/agree', methods=['POST'])
@login_required
def agree_to_creator():
    agreed = request.form.get('agree')

    if agreed:
        # Update user role to 'creator' or set a flag in the database
        current_user.is_creator = True 
        db.session.commit()

        flash('Congratulations! You are now a creator.')
        return redirect(url_for('creator_dashboard'))
    else:
        flash('You must agree to the terms to become a creator.')
        return redirect(url_for('become_creator'))
    


@app.route('/creator_dashboard')
@login_required
def creator_dashboard():
    if not current_user.is_creator:
        flash('You are not authorized to access the creator dashboard.', category='error')
        return redirect(url_for('home'))

    creator_songs = Songs.query.filter_by(user_id=current_user.id).all()
    return render_template('creator_dashboard.html', user=current_user, creator_songs=creator_songs)

@app.route('/create_song', methods=['GET', 'POST'])
@login_required
def create_song():
    if not current_user.is_creator:
        flash('You are not authorized to create songs.', category='error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        
        song_name = request.form.get('song_name')
        artist_name = request.form.get('artist_name')
        album_name = request.form.get('album_name')
        genre = request.form.get('genre')
        date = request.form.get('date')
        lyrics = request.form.get('lyrics')
        audio_data = request.files['audio_data']
        duration = request.form.get('duration')
        image_data = request.files['image_data']

        
        album = Album.query.filter_by(album_name=album_name).first()
        if not album:
            album = Album(album_name=album_name, artist_name=artist_name, date=date)
            db.session.add(album)
            db.session.commit()

        filename=audio_data.filename
        audio_data.save('static/songs_upload/'+filename)

        filename1=image_data.filename
        image_data.save('static/images/'+filename1)
        
        
        new_song = Songs(
            song_name=song_name,
            artist_name=artist_name,
            album_id=album.id,
            user_id=current_user.id,
            audio_data=filename,
            ratings=0, 
            lyrics = lyrics,
            genre = genre,
            duration = duration,
            image_data=filename1
        )

        db.session.add(new_song)
        db.session.commit()

        flash('Song created successfully!', category='success')
        return redirect(url_for('creator_dashboard'))

    return render_template('create_song.html', user=current_user)

@app.route('/edit_song/<int:song_id>', methods=['GET', 'POST'])
@login_required
def edit_song(song_id):
    
    song = Songs.query.get(song_id)
    if request.method == 'GET':
        return render_template('edit_song.html', song=song, user=current_user)


    if not current_user.is_creator or song.user_id != current_user.id:
        flash('You are not authorized to edit this song.', category='error')
        return redirect(url_for('creator_dashboard'))
    
    

    if request.method == 'POST':
        # Update song details based on form data
        song.song_name = request.form.get('song_name')
        song.artist_name = request.form.get('artist_name')
        song.album_name = request.form.get('album_name')
        song.genre = request.form.get('genre')
        song.date = request.form.get('date')
        song.lyrics = request.form.get('lyrics')
        song.duration = request.form.get('duration')
        song.image_data = request.form.get('image_data')
        song.audio_data = request.form.get('audio_data')
        
        # Check if there's a new audio file uploaded
        if 'audio_data' in request.files:
            audio_data = request.files['audio_data'].read()
            filename=audio_data.filename
            audio_data.save('static/songs_upload/'+filename)
            song.audio_data = filename

        # Check if there's a new image file uploaded
        if 'image_data' in request.files:
            image_data = request.files['image_data'].read()
            filename1=image_data.filename1
            image_data.save('static/images/'+filename1)
            song.image_data = filename1
        
              

        db.session.commit()

        flash('Song updated successfully!', category='success')
        return redirect(url_for('creator_dashboard'))

    

@app.route('/delete_song/<int:song_id>')
@login_required
def delete_song(song_id):
    # Find the song by ID
    song = Songs.query.get(song_id)

    if not song or not current_user.is_creator or song.user_id != current_user.id:
        flash('You are not authorized to delete this song.', category='error')
        return redirect(url_for('creator_dashboard'))

    # Delete the song
    db.session.delete(song)
    db.session.commit()

    flash('Song deleted successfully!', category='success')
    return redirect(url_for('creator_dashboard'))

@app.route('/admin')
def admin():
    return render_template('admin_check.html')

@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    print(f"Current user: {current_user}")  
    if request.method == 'POST':
        print("Form submitted:", request.form)  
    if not current_user.is_admin:
        flash('You are not authorized to access the admin dashboard.', category='error')
        print("User is not an admin.")  
        return redirect(url_for('home'))
    
    songs = Songs.query.all()
    creators = User.query.filter_by(is_creator=True).all()
    

    total_users = User.query.count()
    total_creators = User.query.filter_by(is_creator=True).count()
    total_albums = Album.query.count()

    genres = Songs.query.all()

    genre_counts = Counter(song.genre for song in genres)

    genre_names = list(genre_counts.keys())
    song_counts = list(genre_counts.values())

    # Plotting
    plt.figure(figsize=(10, 6))

    # Bar chart for distribution of songs across genres
    plt.barh(genre_names, song_counts, color='coral')  # Use barh for horizontal bar chart
    plt.title('Distribution of Songs Across Genres')
    plt.xlabel('Number of Songs')
    plt.ylabel('Genres')

    plt.xticks(range(1, len(genre_names) + 1))

    # Save the plot to a file or display it
    plt.tight_layout()
    plt.savefig('static/songs_per_genre_bar_chart.png')  
    # plt.show()  
    
    # Calculate the number of songs created by each creator
    creator_song_counts = Counter(song.user_id for song in songs)
    
    # Plotting
    plt.figure(figsize=(10, 6))

    # Bar chart for the number of songs created by each creator
    creator_ids = [creator.id for creator in creators]
    song_counts_by_creator = [creator_song_counts[creator_id] for creator_id in creator_ids]
    creator_username = [creator.username for creator in creators]
    

    plt.barh(range(len(creator_ids)), song_counts_by_creator, color='skyblue')  # Use barh for horizontal bar chart
    plt.title('Number of Songs Created by Each Creator')
    plt.ylabel('Creator Username')
    plt.xlabel('Number of Songs Created')

    plt.yticks(range(len(creator_ids)), creator_username, rotation=0, ha='right')  # Set the tick positions and labels

# Save the plot to a file or display it
    plt.tight_layout()
    chart_filename = 'static/songs_per_creator_bar_chart.png'
    plt.savefig(chart_filename)
    
   

    return render_template('admin_dashboard.html', user=current_user, total_users=total_users,
                           total_creators=total_creators, total_albums=total_albums,
                           genres=genres, song_counts=song_counts, songs=songs,creators=creators,chart_filename=chart_filename)




@app.route('/admin_flag_song/<int:song_id>', methods=['POST','GET'])
@login_required
def admin_flag_song(song_id):
    if not current_user.is_admin:
        flash('You are not authorized to perform this action.', category='error')
        return redirect(url_for('home'))

    song = Songs.query.get(song_id)

    if not song:
        flash('Song not found.', category='error')
    else:
        
        song.flagged = True  
        db.session.commit()
        flash('Song flagged successfully!', category='success')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin_unflag_song/<int:song_id>', methods=['POST','GET'])
@login_required
def admin_unflag_song(song_id):
    if not current_user.is_admin:
        flash('You are not authorized to perform this action.', category='error')
        return redirect(url_for('home'))

    song = Songs.query.get(song_id)

    if not song:
        flash('Song not found.', category='error')
    else:
        
        song.flagged = False 
        db.session.commit()
        flash('Song unflagged successfully!', category='success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_remove_song/<int:song_id>', methods=['POST','GET'])
@login_required
def admin_remove_song(song_id):
    if not current_user.is_admin:
        flash('You are not authorized to perform this action.', category='error')
        return redirect(url_for('home'))

    song = Songs.query.get(song_id)

    if not song:
        flash('Song not found.', category='error')
    else:
        # Perform the action to remove the song 
        db.session.delete(song)
        db.session.commit()
        flash('Song removed successfully!', category='success')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin_blacklist_creator/<int:creator_id>', methods=['POST'])
@login_required
def admin_blacklist_creator(creator_id):
    if not current_user.is_admin:
        flash('You are not authorized to perform this action.', category='error')
        return redirect(url_for('dashboard'))

    creator = User.query.get(creator_id)

    if not creator or not creator.is_creator:
        flash('Creator not found or is not registered as a creator.', category='error')
    else:
        creator.is_blacklisted = True

        # Flag the songs created by the blacklisted creator
        songs_to_flag = Songs.query.filter_by(user_id=creator_id).all()
        for song in songs_to_flag:
            song.flagged = True

        db.session.commit()
        flash('Creator blacklisted successfully! Songs flagged.', category='success')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin_whitelist_creator/<int:creator_id>', methods=['POST'])
@login_required
def admin_whitelist_creator(creator_id):
    if not current_user.is_admin:
        flash('You are not authorized to perform this action.', category='error')
        return redirect(url_for('home'))

    creator = User.query.get(creator_id)

    if not creator or not creator.is_creator:
        flash('Creator not found or is not registered as a creator.', category='error')
    else:
        # Perform the action to whitelist the creator (update the database accordingly)
        creator.is_blacklisted = False  
        
        songs_to_unflag = Songs.query.filter_by(user_id=creator_id).all()
        for song in songs_to_unflag:
            song.flagged = False
        
        db.session.commit()
        flash('Creator whitelisted successfully!', category='success')

    return redirect(url_for('admin_dashboard'))

@app.route('/create_playlist', methods=['GET', 'POST'])
@login_required
def create_playlist():
    if request.method == 'POST':
        playlist_name = request.form.get('playlist_name')
        selected_song_ids = request.form.getlist('selected_songs')

        
        if not playlist_name:
            flash('Playlist name is required.', category='error')
            return redirect(url_for('create_playlist'))

        # Create a new playlist
        new_playlist = Playlist(playlist_name=playlist_name, author=current_user.id)
        db.session.add(new_playlist)
        db.session.commit()

        # Add selected songs to the playlist
        for song_id in selected_song_ids:
            song = Songs.query.get(song_id)
            if song:
                new_playlist.songs.append(song)

        db.session.commit()

        flash('Playlist created successfully!', category='success')
        return redirect(url_for('home', new_playlist = new_playlist))

    # Get all songs from the database
    all_songs = Songs.query.all()

    return render_template('create_playlist.html', user=current_user, all_songs=all_songs)

@app.route('/edit_playlist/<int:playlist_id>', methods=['GET', 'POST'])
@login_required
def edit_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    all_songs = Songs.query.all()

    if request.method == 'POST':
        # Update playlist name
        playlist.playlist_name = request.form.get('playlist_name')

        # Update playlist songs
        selected_song_names = request.form.getlist('selected_songs')
        updated_songs = []

        for song_name in selected_song_names:
            song = Songs.query.filter_by(song_name=song_name).first()
            if song:
                updated_songs.append(song)

        playlist.songs = updated_songs

        db.session.commit()

        flash('Playlist updated successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('edit_playlist.html', user=current_user, playlist=playlist, all_songs=all_songs)

@app.route('/delete_playlist/<int:playlist_id>', methods=['POST','GET'])
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    db.session.delete(playlist)
    db.session.commit()
    flash('Playlist deleted successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/view_playlist/<int:playlist_id>', methods=['GET','POST'])
@login_required
def view_playlist(playlist_id):
    playlist = Playlist.query.get(playlist_id)   

    return render_template('playlist_detail.html', user=current_user, playlist=playlist)


#create a route for search
from sqlalchemy import or_

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        search_query = request.form.get('search_query')

        matched_albums = Album.query.join(Songs).filter(
            (Album.album_name.ilike(f'%{search_query}%')) |
            (Album.artist_name.ilike(f'%{search_query}%')) |
            (Songs.genre.ilike(f'%{search_query}%'))
        ).distinct().all()

        # Use 'or_' to combine multiple ILIKE conditions for partial matching
        matched_songs = Songs.query.join(Album).filter(
            or_(
                Songs.song_name.ilike(f'%{search_query}%'),
                Album.artist_name.ilike(f'%{search_query}%'),
                Songs.genre.ilike(f'%{search_query}%'),
                (
                    (Songs.average_ratings >= Decimal(search_query)) &
                    (Songs.average_ratings < Decimal(search_query) + 1)
                ) if search_query and (search_query.isdigit() or (search_query.count('.') == 1 and search_query.replace('.', '').isdigit()))
                else False
            )
        ).all()

        print("Search Query:", search_query)
        print("Matched Albums:", matched_albums)
        print("Matched Songs:", matched_songs)

        return render_template('search_results.html', albums=matched_albums, songs=matched_songs, search_query=search_query)

    return redirect(url_for('home'))






@app.route('/lyrics/<int:song_id>')
def lyrics(song_id):
    
    song = Songs.query.get(song_id)  

    
    lyrics_data = {
        'title': song.song_name,
        'artist': song.artist_name,
        'lyrics': song.lyrics,
        
    }

    return render_template('lyrics.html', lyrics_data=lyrics_data)

@app.route('/rate_song/<int:id>', methods=['POST'])
@login_required
def rate_song(id):
    new_ratings = int(request.form.get('rating'))

    song = Songs.query.get(id)

    if song:
        # Check if the user has already rated the song
        user_rating = Songs.query.filter_by(id=song.id).first()
        
        if user_rating:
            # Add the new ratings to the existing ratings
            user_rating.ratings += new_ratings
            song.users_rated_count += 1
            song.average_ratings = user_rating.ratings/song.users_rated_count
            
        else:
            # Create a new rating entry for the user and song
            song.ratings = new_ratings
            
            song.average_ratings = new_ratings
            
        db.session.add(song)
        db.session.commit()

    return redirect(url_for('all_songs'))
    
    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin',password_hash='admin',is_admin=True,email='admin@example.com')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
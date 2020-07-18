#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form, CSRFProtect
from forms import *
from flask_migrate import Migrate
from sqlalchemy.ext.hybrid import hybrid_property

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    genres = db.Column(db.String(120), nullable=True)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(120), nullable=False)
    seeking_talent = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String(), nullable=True)

    # Eager load to count upcoming/passed shows
    shows = db.relationship('Show', backref='venue', lazy='select')

    @hybrid_property
    def upcoming_shows(self):
      return list(filter(lambda show: show.start_time >= datetime.now(), self.shows))
  
    @hybrid_property
    def upcoming_shows_count(self):
      return len(self.upcoming_shows)

    @hybrid_property
    def past_shows(self):
      return list(filter(lambda show: show.start_time < datetime.now(), self.shows))

    @hybrid_property
    def past_shows_count(self):
      return len(self.past_shows)

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=True)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(120), nullable=True)
    seeking_venue = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String(), nullable=True)

    shows = db.relationship('Show', backref='artist', lazy=True)

    @hybrid_property
    def upcoming_shows(self):
      return list(filter(lambda show: show.start_time >= datetime.now(), self.shows))
  
    @hybrid_property
    def upcoming_shows_count(self):
      return len(self.upcoming_shows)

    @hybrid_property
    def past_shows(self):
      return list(filter(lambda show: show.start_time < datetime.now(), self.shows))

    @hybrid_property
    def past_shows_count(self):
      return len(self.past_shows)

class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime, nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

  @hybrid_property
  def venue_name(self):
    return self.venue.name

  @hybrid_property
  def venue_image_link(self):
    return self.venue.image_link

  @hybrid_property
  def artist_name(self):
    return self.artist.name

  @hybrid_property
  def artist_image_link(self):
    return self.artist.image_link

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  # date = dateutil.parser.parse(value)
  # NOTE: I'm saving the date as DateTime in db so no need to parse it first
  date = value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.order_by('id').all()

  venues_by_city_and_state = dict()
  for venue in venues:
    venues_list_for_city_state = venues_by_city_and_state.get((venue.city, venue.state), [])
    venues_list_for_city_state.append(venue)
    venues_by_city_and_state[(venue.city, venue.state)] = venues_list_for_city_state

  data = []
  for city_state_key, venues in venues_by_city_and_state.items():
    data.append({
      'city': city_state_key[0],
      'state': city_state_key[1],
      'venues': venues
    })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  matched_artists = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  response = {
    "count": len(matched_artists),
    "data": matched_artists
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data = Venue.query.get(venue_id)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()

  if not form.validate():
    flash(f'Following Errors Occurred: {form.errors} ')
    return render_template('forms/new_venue.html', form=form)

  data = {
    'name': form.name.data,
    'city': form.city.data,
    'state': form.state.data,
    'address': form.address.data,
    'phone': form.phone.data,
    'genres': ','.join(form.genres.data),
    'image_link': form.image_link.data,
    'facebook_link': form.facebook_link.data,
    'website': form.website.data,
    'seeking_talent': form.seeking_talent.data,
    'seeking_description': form.seeking_description.data,
  }

  try:
    new_venue = Venue(**data)

    db.session.add(new_venue)
    db.session.commit()

    flash('Venue ' + new_venue.name + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + new_venue.name + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  veneue = Venue.query.get(venue_id)
  db.session.remove(venue)

  try:
    db.session.commit()
    flash('Venue ' + veneue.name + ' was successfully deleted!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + veneue.name + ' could not be deleted.')
  finally:
    db.session.close()

  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.order_by('id').all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  matched_artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  response = {
    "count": len(matched_artists),
    "data": matched_artists
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)

  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data = artist.name
  form.phone.data = artist.phone
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.genres.data = artist.genres.split(',')
  form.city.data = artist.city
  form.city.state = artist.state
  form.image_link.data = artist.image_link
  form.facebook_link.data = artist.facebook_link
  form.website.data = artist.website

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  artist.name = form.name.data
  artist.city = form.city.data
  artist.state = form.state.data
  artist.phone = form.phone.data
  artist.genres = ','.join(form.genres.data),
  artist.image_link = form.image_link.data
  artist.facebook_link = form.facebook_link.data
  artist.website = form.website.data
  artist.seeking_venue = form.seeking_venue.data
  artist.seeking_description = form.seeking_description.data

  try:
    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + artist.name + ' could not be updated.')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  venue = Venue.query.get(venue_id)
  
  form.name.data = venue.name
  form.phone.data = venue.phone
  form.address.data = venue.address
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.genres.data = venue.genres.split(',')
  form.city.data = venue.city
  form.city.state = venue.state
  form.image_link.data = venue.image_link
  form.facebook_link.data = venue.facebook_link
  form.website.data = venue.website

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  venue.name = form.name.data
  venue.city = form.city.data
  venue.state = form.state.data
  venue.address = form.address.data
  venue.phone = form.phone.data
  venue.genres = ','.join(form.genres.data),
  venue.image_link = form.image_link.data
  venue.facebook_link = form.facebook_link.data
  venue.website = form.website.data
  venue.seeking_talent = form.seeking_talent.data
  venue.seeking_description = form.seeking_description.data

  try:
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be updated.')
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()

  if not form.validate():
    flash(f'Following Errors Occurred: {form.errors} ')
    return render_template('forms/new_artist.html', form=form)

  data = {
    'name': form.name.data,
    'city': form.city.data,
    'state': form.state.data,
    'phone': form.phone.data,
    'genres': ','.join(form.genres.data),
    'image_link': form.image_link.data,
    'facebook_link': form.facebook_link.data,
    'website': form.website.data,
    'seeking_venue': form.seeking_venue.data,
    'seeking_description': form.seeking_description.data,
  }

  try:
    new_artist = Artist(**data)

    db.session.add(new_artist)
    db.session.commit()

    flash('Artist ' + new_artist.name + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + new_artist.name + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = Show.query.order_by('id').all()

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm()

  if not form.validate():
    flash(f'Following Errors Occurred: {form.errors} ')
    return render_template('forms/new_show.html', form=form)

  data = {
    'artist_id': form.artist_id.data,
    'venue_id': form.venue_id.data,
    'start_time': form.start_time.data
  }

  try:
    new_show = Show(**data)
    db.session.add(new_show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('Something went wrong, Show was not successfuly listed!')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

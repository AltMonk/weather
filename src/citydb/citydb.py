"""Module to manage a local SQLite database of city geo info."""
import codecs
import csv
import datetime
from peewee import *
import sys

# Constants
DATE_FORMAT = '%Y-%m-%d'
GEONAME_KEYS = (
    'geonameid',
    'name',
    'asciiname',
    'alternatenames',
    'latitude',
    'longitude',
    'feature_class',
    'feature_code',
    'country_code',
    'cc2',
    'admin1',
    'admin2',
    'admin3',
    'admin4',
    'population',
    'elevation',
    'dem',
    'timezone',
    'modification_date'
    )

# Use SqliteDatabase
db = SqliteDatabase('cities.db')


class City(Model):
    """Database model to hold city geo information."""
    geonameid = IntegerField(primary_key=True)
    name = CharField(max_length=200)
    asciiname = CharField(max_length=200, null=True)
    alternatenames = TextField(null=True)
    latitude = FloatField()
    longitude = FloatField()
    feature_class = CharField(max_length=1)
    feature_code = CharField(max_length=10)
    country_code = CharField(max_length=2)
    cc2 = CharField(max_length=60, null=True)
    admin1 = CharField(max_length=20, null=True)
    admin2 = CharField(max_length=80, null=True)
    admin3 = CharField(max_length=20, null=True)
    admin4 = CharField(max_length=20, null=True)
    population = IntegerField()
    elevation = IntegerField(null=True)
    dem = IntegerField(null=True)
    timezone = CharField(max_length=40)
    modification_date = DateField()

    class Meta:
        database = db


def unicode_csv_reader(unicode_csv_data, **kwargs):
    """csv.py doesn't do Unicode; encode temporarily as UTF-8.
    Source: Python documentation.
    """
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data), **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]


def utf_8_encoder(unicode_csv_data):
    """Decode UTF-8 back to Unicode.
    Source: Python documentation.
    """
    for line in unicode_csv_data:
        yield line.encode('utf-8')


def load_file(geoname_file):
    """Load 'geoname' cities tab-delimited text file into a list of.
    cities (dict).
    """
    # Avoid field limit (131072) csv error by expanding size limit
    csv.field_size_limit(sys.maxsize)

    with codecs.open(geoname_file, 'r', 'utf_8') as geo_file:
        reader = unicode_csv_reader(geo_file, delimiter='\t')
        cities = []
        num_cities = 0
        for count, city in enumerate(reader):

            # Fixes PeeWee error with '' for ints.
            city = [i if i != '' else None for i in city]
            city[-1] = datetime.datetime.strptime(city[-1], DATE_FORMAT).date()

            # Dict for each city, list
            cities.append(dict(zip(GEONAME_KEYS, city)))
            num_cities += 1
    print "%d cities loaded from %s." % (num_cities, geoname_file)
    return cities


def load_db(data):
    """Delete any existing data, then load the database. data is list of
    cities (dict). Each city is a new row in the db.
    """
    # Insert rows 500 at a time
    # 1000 per time suggestion from peewee documentation fails:
    # "too many terms in compound SELECT"
    with db.transaction():
        for idx in range(0, len(data), 500):
            City.insert_many(data[idx:idx+500]).execute()
    print "%d cities loaded into database." % City.select().count()


def create_tables():
    """Small helper function to create the tables in the database."""
    db.connect()
    db.create_tables([City])
    db.close()


if __name__ == '__main__':
    db.connect()
    City.delete().execute()
    load_db(load_file('geonames/cities5000.txt'))
    db.close()

# app.py
import os

from flask import Flask
from flask_caching import Cache

APP_ROOT = os.path.dirname(os.path.realpath(__file__))
DEBUG = False

class CustomFlask(Flask):
  jinja_options = Flask.jinja_options.copy()
  jinja_options.update(dict(
    block_start_string='(%',
    block_end_string='%)',
    variable_start_string='((',
    variable_end_string='))',
    comment_start_string='(#',
    comment_end_string='#)',
  ))

app = CustomFlask(__name__)
app.config.from_object(__name__)

cache = Cache(app, config={
    'CACHE_TYPE': "RedisCache",
    'CACHE_REDIS_URL': 'redis://externalstructureproxy-redis',
    'CACHE_DEFAULT_TIMEOUT': 84600,
})
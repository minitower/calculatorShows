from http import server
from waitress import serve
import server
import os
from dotenv import load_dotenv

load_dotenv()

serve(server.app, port=os.environ.get('PORT'), url_scheme='http')
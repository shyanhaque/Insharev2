from flask import Flask, session
import os 
from dotenv import load_dotenv
import logging 
from logging.handlers import RotatingFileHandler
  

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'cR8vY5_fG3q2XwTbN7zUkAe6QhSdL1iJ9oPm4WlEp0O')

# Configure logging
logger = logging.getLogger(__name__)
log_handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

# Register routes
from flask_project import routes
app.register_blueprint(routes.bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
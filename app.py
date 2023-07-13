try:
    import sigvar
except ImportError as ex:
    print(ex)
from logging import debug
from flask import Flask, render_template, jsonify
from items_factory import items_factory
from user_factory import user_factory
from media_factory import media_factory
from flask_migrate import Migrate
from models.data_models import db
from models.data_models import api, ma
import os
from flask_cors import CORS
from celery_service.celery_factory import make_celery
from graph_factory import graph_factory
from graph_factory import schema
from search_factory import search_factory
from offers_factory import offers_factory
from flask_graphql import GraphQLView
from flask_session import Session
from loggers import get_logger


def create_app():

    app_logger = get_logger("application")
    app_logger.debug(f"creating application level logger with name application")

    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("RDS_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_RECORD_QUERIES'] = True

    app.config['CELERY_BROKER_URL'] = f'redis://{os.getenv("REDIS_URI")}/0'
    app.config['CELERY_RESULT_BACKEND'] = f'redis://{os.getenv("REDIS_URI")}/0'
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

    app.config["SESSION_PERMANENT"] = True
    app.config["SESSION_TYPE"] = "filesystem"
    app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")

    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    CORS(app, supports_credentials=True)
    Migrate(app, db, compare_type=True)
    db.init_app(app)
    api.init_app(app)
    ma.init_app(app)
    
    app.register_blueprint(items_factory, url_prefix="")
    app.register_blueprint(user_factory, url_prefix="")
    app.register_blueprint(media_factory, url_prefix="")
    app.register_blueprint(search_factory, url_prefix="")
    app.register_blueprint(graph_factory, url_prefix="/graphapi")
    app.register_blueprint(offers_factory, url_prefix="")

    @app.route('/')
    def home():
        return render_template("base.html")

    app.add_url_rule(
        '/graphql-api',
        view_func=GraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=True # for having the GraphiQL interface
        )
    )

    @app.errorhandler(500)
    def internal_server_error(e):
        # note that we set the 500 status explicitly
        return jsonify({"message": f"500 {str(e)}"})

    return app


app = create_app()
celery = make_celery(app)
#!/usr/bin/env python3

from flask import Flask, request, make_response
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Newsletter

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletters.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

ma = Marshmallow(app)  # Initialize Marshmallow for serialization with HATEOAS support

class NewsletterSchema(ma.SQLAlchemySchema):  # Define schema for Newsletter model serialization

    class Meta:
        model = Newsletter  # Map this schema to the Newsletter model
        load_instance = True  # Deserialize to model instances instead of plain dictionaries

    title = ma.auto_field()  # Automatically map the title field from the model
    published_at = ma.auto_field()  # Automatically map the published_at field from the model

    url = ma.Hyperlinks(  # Add hyperlink URLs for HATEOAS navigation
        {
            "self": ma.URLFor(  # URL for the individual newsletter record
                "newsletterbyid",
                values=dict(id="<id>")),
            "collection": ma.URLFor("newsletters"),  # URL for the full collection of newsletters
        }
    )

newsletter_schema = NewsletterSchema()  # Schema instance for serializing a single newsletter
newsletters_schema = NewsletterSchema(many=True)  # Schema instance for serializing multiple newsletters

api = Api(app)

class Index(Resource):

    def get(self):
        
        response_dict = {
            "index": "Welcome to the Newsletter RESTful API",
        }
        
        response = make_response(
            response_dict,
            200,
        )

        return response

api.add_resource(Index, '/')

class Newsletters(Resource):

    def get(self):
        
        newsletters = Newsletter.query.all()  # Retrieve all newsletters from the database

        response = make_response(
            newsletters_schema.dump(newsletters),  # Serialize multiple records with Marshmallow schema
            200,
        )

        return response

    def post(self):
        
        new_record = Newsletter(  # Create a new Newsletter instance from request data
            title=request.form['title'],
            body=request.form['body'],
        )

        db.session.add(new_record)  # Add to database session
        db.session.commit()  # Persist the new record to the database

        response = make_response(
            newsletter_schema.dump(new_record),  # Serialize single record with Marshmallow schema
            201,
        )

        return response

api.add_resource(Newsletters, '/newsletters')

class NewsletterByID(Resource):

    def get(self, id):

        newsletter = Newsletter.query.filter_by(id=id).first()  # Query for newsletter by ID

        response = make_response(
            newsletter_schema.dump(newsletter),  # Serialize single record with full details
            200,
        )

        return response

    def patch(self, id):

        record = Newsletter.query.filter_by(id=id).first()  # Find the newsletter to update
        for attr in request.form:  # Iterate through all submitted form fields
            setattr(record, attr, request.form[attr])  # Update the attribute with new value

        db.session.add(record)  # Stage the changes
        db.session.commit()  # Persist the updates to the database

        response = make_response(
            newsletter_schema.dump(record),  # Serialize updated record with Marshmallow
            200
        )

        return response

    def delete(self, id):

        record = Newsletter.query.filter_by(id=id).first()
        
        db.session.delete(record)
        db.session.commit()

        response_dict = {"message": "record successfully deleted"}

        response = make_response(
            response_dict,
            200
        )

        return response

api.add_resource(NewsletterByID, '/newsletters/<int:id>')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
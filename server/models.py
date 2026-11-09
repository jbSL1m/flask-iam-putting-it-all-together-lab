from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow import Schema, fields

from config import db, bcrypt

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String)
    image_url = db.Column(db.String)
    bio = db.Column(db.String)
    recipes = db.relationship(
        'Recipe', back_populates='user', cascade='all, delete-orphan'
    )

    @validates('username')
    def validate_username(self, key, username):
        if not isinstance(username, str) or not username.strip():
            raise ValueError('Username is required')
        return username

    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hash is not readable")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))

    

class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', back_populates='recipes')

    @validates('title')
    def validate_title(self, key, title):
        if not isinstance(title, str) or not title.strip():
            raise ValueError('Title is required')
        return title

    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if (
            not isinstance(instructions, str)
            or len(instructions.strip()) < 50
        ):
            raise ValueError("Instructions must be at least 50 characters long")
        return instructions

    @validates('minutes_to_complete')
    def validate_minutes_to_complete(self, key, minutes):
        if not isinstance(minutes, int) or isinstance(minutes, bool):
            raise ValueError('Minutes to complete must be an integer')
        return minutes

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    image_url = fields.Str()
    bio = fields.Str()

class RecipeSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    instructions = fields.Str(required=True)
    minutes_to_complete = fields.Int(required=True)
    user = fields.Nested(UserSchema, dump_only=True)
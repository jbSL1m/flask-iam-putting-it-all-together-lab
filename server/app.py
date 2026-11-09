#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema


def _session_user():
    user_id = session.get('user_id')
    return db.session.get(User, user_id) if user_id else None


def _error(message, status):
    return {'errors': [message]}, status


class Signup(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        password = data.get('password')
        if not isinstance(password, str) or not password:
            return _error('Password is required', 422)

        try:
            new_user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio'))

            new_user.password_hash = password
            db.session.add(new_user)
            db.session.commit()
        except ValueError as error:
            db.session.rollback()
            return _error(str(error), 422)
        except IntegrityError:
            db.session.rollback()
            return _error('Username is required and must be unique', 422)

        session['user_id'] = new_user.id
        return UserSchema().dump(new_user), 201

class CheckSession(Resource):
    def get(self):
        user = _session_user()
        if user is None:
            return _error('Unauthorized', 401)
        return UserSchema().dump(user), 200

class Login(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username).first()

        if (
            user is None
            or not isinstance(password, str)
            or not user.authenticate(password)
        ):
            return _error('Invalid username or password', 401)

        session['user_id'] = user.id
        return UserSchema().dump(user), 200

class Logout(Resource):
    def delete(self):
        if not session.get('user_id'):
            return _error('Unauthorized', 401)
        session.pop('user_id', None)
        return '', 204

class RecipeIndex(Resource):
    def get(self):
        if _session_user() is None:
            return _error('Unauthorized', 401)
        recipes = Recipe.query.all()
        return RecipeSchema(many=True).dump(recipes), 200

    def post(self):
        user = _session_user()
        if user is None:
            return _error('Unauthorized', 401)

        data = request.get_json(silent=True) or {}
        minutes = data.get('minutes_to_complete')
        try:
            if isinstance(minutes, bool):
                raise ValueError('Minutes to complete must be an integer')
            if isinstance(minutes, str):
                minutes = int(minutes)
            elif not isinstance(minutes, int):
                raise ValueError('Minutes to complete must be an integer')
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=minutes,
                user=user,
            )
            db.session.add(recipe)
            db.session.commit()
        except (TypeError, ValueError) as error:
            db.session.rollback()
            return _error(str(error), 422)
        except IntegrityError:
            db.session.rollback()
            return _error('Recipe is invalid', 422)
        return RecipeSchema().dump(recipe), 201

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from os import path
if path.exists("env.py"):
    import env

# add confiqurations
app = Flask(__name__)
app.config["MONGO_DBNAME"] = 'book_review'
app.config["MONGO_URI"] = os.environ.get('MONGO_URI')
mongo = PyMongo(app)


@app.route('/')
@app.route('/get_books')
def get_books():
    return render_template("books.html", books=list(mongo.db.books.find()),
                           categories=mongo.db.categories.find())


@app.route('/reviews/<book_id>')
def reviews(book_id):
    the_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return render_template('reviews.html',
                           book=the_book,
                           reviews=mongo.db.reviews.find())


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)

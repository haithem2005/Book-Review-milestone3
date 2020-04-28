import os
from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
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
                           categories=list(mongo.db.categories.find()))


@app.route('/reviews/<book_id>')
def reviews(book_id):
    the_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return render_template('reviews.html',
                           book=the_book,
                           reviews=mongo.db.reviews.find())


@app.route('/add_book')
def add_book():
    return render_template("addbook.html",
                           categories=list(mongo.db.categories.find()))


@app.route('/insert_book', methods=['POST'])
def insert_book():
    book_doc = {'book_name': request.form.get('book_name'),
                'book_year': request.form.get('year'),
                'image_source': request.form.get('image_source'),
                'book_author': request.form.get('author'),
                'book_category': request.form.get('book_category'),
                'book_rating': request.form.get('rating')}
    review_doc = {'book_name': request.form.get('book_name'),
                  'review': request.form.get('review')}
    mongo.db.books.insert_one(book_doc)
    mongo.db.reviews.insert_one(review_doc)
    return redirect(url_for('get_books'))


@app.route('/view_by_cat/<category_id>')
def view_by_cat(category_id):
    the_category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template('viewby.html',
                           category=the_category,
                           books=list(mongo.db.books.find()),
                           categories=list(mongo.db.categories.find()))


@app.route('/insert_review', methods=['POST'])
def insert_review():
    the_book = mongo.db.books.find_one({
                        'book_name': request.form.get('book_name')})
    book_id = the_book['_id']
    now = datetime.now().strftime("%Y-%M-%D")
    review_doc = {'name': request.form.get('your_name'),
                  'book_name': request.form.get('book_name'),
                  'date': now,
                  'review': request.form.get('review')}
    mongo.db.reviews.insert_one(review_doc)
    return redirect(url_for('reviews', book_id=book_id))

# add a review function we use book_id so that we can use the book name
# as a value in the book name field
@app.route('/add_review/<book_id>')
def add_review(book_id):
    the_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return render_template('addreview.html', book=the_book)


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)

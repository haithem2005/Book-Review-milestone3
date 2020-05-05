import os
from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from flask_paginate import Pagination, get_page_args
from os import path
if path.exists("env.py"):
    import env


# add confiqurations
app = Flask(__name__)
# defining the collection name as in mongodb
app.config["MONGO_DBNAME"] = 'book_review'
# getting the uri which connecting python with mongodb from locat file
app.config["MONGO_URI"] = os.environ.get('MONGO_URI')
# creating instance of pymongo
mongo = PyMongo(app)

#              ######################################################


@app.route('/')
def get_books():
    categories = list(mongo.db.categories.find())
    booksbycat = []
    for cat in categories:
        books = list(mongo.db.books.
                     find({"book_category": cat['category_name']}).limit(3))
        _books = {
            'books': books,
            'cat': cat
        }
        for book in books:
            book['rating'] = rating(book['_id'])
        booksbycat.append(_books)
    return render_template("books.html", page_title="Your Book",
                           booksbycat=booksbycat,

                           categories=list(mongo.db.categories.find()))

#              ######################################################


@app.route('/reviews/<book_id>')
def reviews(book_id):
    the_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return render_template('reviews.html',
                           book=the_book,
                           reviews=mongo.db.reviews.find(),
                           categories=list(mongo.db.categories.find()),
                           page_title=the_book['book_name']+" Reviews")

#              ######################################################


@app.route('/add_book')
def add_book():
    return render_template("addbook.html",
                           categories=list(mongo.db.categories.find()),
                           page_title="Add Book")

#              ######################################################


@app.route('/insert_book', methods=['POST'])
def insert_book():
    book_doc = {'book_name': request.form.get('book_name'),
                'book_year': request.form.get('year'),
                'image_source': request.form.get('image_source'),
                'book_author': request.form.get('author'),
                'book_category': request.form.get('book_category'),
                'book_rating': request.form.get('rating'),
                'book_link': request.form.get('book_link')}
    review_doc = {'book_name': request.form.get('book_name'),
                  'review': request.form.get('review')}
    mongo.db.books.insert_one(book_doc)
    mongo.db.reviews.insert_one(review_doc)
    return redirect(url_for('get_books'))

#              ######################################################


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

#              ######################################################


# add a review function we use book_id so that we can use the book name
# as a value in the book name field

@app.route('/add_review/<book_id>')
def add_review(book_id):
    the_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return render_template('addreview.html', book=the_book,
                           categories=list(mongo.db.categories.find()),
                           page_title="Add Review")

#              ######################################################


# this function used to view books by their category
# by selecting the required category from the dropdown list
# the result is displayed using pagination 10 books per page

@app.route('/view_by_cat/<category_id>')
def view_by_cat(category_id):
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
# finding the selected category from the dropdown list
    the_category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
# finding the books with category name matched to the selected category
    books = list(mongo.db.books.
                 find({"book_category": the_category['category_name']}))
# calling the rating( ) function to calculate the total rating of books
    for book in books:
        book['rating'] = rating(book['_id'])
# finding the length of the list for pagination
    total = len(books)
# adding offset to the list for pagination
    the_books = books[offset: offset + per_page]
# defining the pagination parameters
    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap4',
                            format_total=True,   # format total. example 1,024
                            format_number=True,  # turn on format flag
                            record_name='Books', alignment='center')
# rendering the template with pagination
    return render_template('viewby.html',
                           category=the_category,
                           books=the_books,
                           categories=list(mongo.db.categories.find()),
                           page=page,
                           per_page=per_page,
                           offset=offset,
                           pagination=pagination,
                           page_title=the_category['category_name'])

#              ######################################################


@app.route('/rating/<book_id>')
def rating(book_id):
    ratings = []
    the_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    rating_list = list(mongo.db.rating.
                       find({"book_name": the_book['book_name']}))
    for book in rating_list:
        ratings.append(book['rating'])
    rating_sum = 0
    final_rating = "No Rating"
    if len(ratings) > 0:
        for rating in ratings:
            rating_sum += int(rating)
            final_rating = (rating_sum / len(ratings))
    return final_rating


# this function takes the book name from the search bar
# and search all the books name then display the result
# if more than one book have the same names all the books will be displayed
# this function also convert the name in search bar to lower and
# the book names in mongo to lower then compare the name
# from the search bar to the names of all the books in mogo db
# this function use pagination to display the searched books 10 books per page

@app.route('/find_book', methods=['POST'])
def find_book():
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')

# getting the required book name from search bar and lower it
    required_book = request.form.get('search').lower()
    result_books = []
    the_books = list(mongo.db.books.find())

# search for the required book name in all the books found in db
# after lowering the books name in db then adding the matched names in a list

    for book in the_books:
        if book['book_name'].lower() == required_book:
            result_books.append(book)

# the length of the list for pagination info
    total = len(result_books)

# adding offset for the pagination
    the_required_books = result_books[offset: offset + per_page]

# defining the pagination parameters
    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap4',
                            format_total=True,   # format total. example 1,024
                            format_number=True,  # turn on format flag
                            record_name='Books', alignment='center')

# rendering the template with the pagination
    return render_template('search.html', books=the_required_books,
                           page=page,
                           per_page=per_page,
                           offset=offset,
                           pagination=pagination,
                           categories=list(mongo.db.categories.find()),
                           page_title="Search Result")

#              ######################################################


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from flask import session
from flask_paginate import Pagination, get_page_args
import bcrypt
from os import path
if path.exists("env.py"):
    import env


# add confiqurations

app = Flask(__name__)

# defining the collection name as in mongodb
app.config["MONGO_DBNAME"] = 'book_review'
# getting the uri which connecting python with mongodb from locat file
app.config["MONGO_URI"] = os.environ.get('MONGO_URI')
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY')

# creating instance of pymongo
mongo = PyMongo(app)


#              ######################################################
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('get_books'))

    return render_template('login.html', page_title="login")

#              ######################################################


@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name': request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.
                         form['pass'].encode('utf-8'),
                         login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            return redirect(url_for('index'))

    return render_template("login.html", error="invalid username or password")

#              ######################################################


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].
                                     encode('utf-8'), bcrypt.gensalt())
            users.insert({'name': request.form['username'],
                          'password': hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))

        return 'That username already exists!'

    return render_template('register.html', page_title="register")

#              ######################################################


@app.route('/logout',  methods=['POST', 'GET'])
def logout():
    if 'username' in session:
        session.clear()
        return redirect(url_for('index'))

#              ######################################################


@app.route('/get_books')
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
    return render_template("books.html", page_title="all Books",
                           booksbycat=booksbycat,

                           categories=list(mongo.db.categories.find()))

#              ######################################################


@app.route('/user_books')
def user_books():
    if 'username' in session:

        page, per_page, offset = get_page_args(page_parameter='page',
                                               per_page_parameter='per_page')
        user = mongo.db.users.find_one({"name": session['username']})
        books = list(mongo.db.books.find({"user_id": user['_id']}))

        for book in books:
            book['rating'] = rating(book['_id'])

        total = len(books)

        the_books = books[offset: offset + per_page]

        pagination = Pagination(page=page, per_page=per_page, total=total,
                                css_framework='bootstrap4',
                                format_total=True,
                                format_number=True,  # turn on format flag
                                record_name='Books', alignment='center')

        return render_template("userbooks.html", page_title="your books",
                               categories=list(mongo.db.categories.find()),
                               books=the_books,
                               page=page,
                               per_page=per_page,
                               offset=offset,
                               pagination=pagination,)
    else:
        return redirect(url_for('index'))
#              ######################################################


@app.route('/manage_book/<book_id>')
def manage_book(book_id):
    the_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return render_template("managebook.html",
                           categories=list(mongo.db.categories.find()),
                           book=the_book,
                           page_title="manage book")

#              ######################################################


@app.route('/update_book/<book_id>', methods=['Post'])
def update_book(book_id):
    category = mongo.db.categories.find_one({"category_name": request
                                            .form.get('book_category')})
    user = mongo.db.users.find_one({"name": session['username']})
    mongo.db.books.update_one({'_id': ObjectId(book_id)}, {
                           'book_name': request.form.get('book_name'),
                           'book_year': request.form.get('year'),
                           'image_source': request.form.get('image_source'),
                           'book_author': request.form.get('author'),
                           'book_category': request.form.get('book_category'),
                           'book_link': request.form.get('book_link'),
                           'book_description': request
                           .form.get('description'),
                           'user_id': user['_id'],
                           'category_id': category['_id']})
    return redirect(url_for('user_books'))

#              ######################################################


@app.route('/delete_book/<book_id>')
def delete_book(book_id):
    mongo.db.books.remove({'_id': ObjectId(book_id)})
    return redirect(url_for('user_books'))

#              ######################################################


@app.route('/add_book')
def add_book():
    return render_template("addbook.html",
                           categories=list(mongo.db.categories.find()),
                           page_title="Add Book")

#              ######################################################


@app.route('/insert_book', methods=['POST'])
def insert_book():
    user = mongo.db.users.find_one({"name": session['username']})
    category = mongo.db.categories.find_one({"category_name": request
                                            .form.get('book_category')})
    book_doc = {'book_name': request.form.get('book_name'),
                'book_year': request.form.get('year'),
                'image_source': request.form.get('image_source'),
                'book_author': request.form.get('author'),
                'book_category': request.form.get('book_category'),
                'book_link': request.form.get('book_link'),
                'book_description': request.form.get('description'),
                'user_id': user['_id'],
                'category_id': category['_id']}

    mongo.db.books.insert_one(book_doc)

    return redirect(url_for('get_books'))

#              ######################################################


@app.route('/insert_review/<book_id>', methods=['POST'])
def insert_review(book_id):
    user = mongo.db.users.find_one({"name": session['username']})
    the_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})

    now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    review_doc = {'name': request.form.get('your_name'),
                  'book_name': request.form.get('book_name'),
                  'date': now,
                  'review': request.form.get('review'),
                  'book_id': the_book['_id'],
                  'user_id': user['_id']}

    mongo.db.reviews.insert_one(review_doc)

    return redirect(url_for('display_book', book_id=the_book['_id']))

#              ######################################################


# add a review function we use book_id so that we can use the book name
# as a value in the book name field

@app.route('/add_review/<book_id>')
def add_review(book_id):
    the_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})

    return render_template('addreview.html', book=the_book,
                           categories=list(mongo.db.categories.find()),
                           book_id=the_book['_id'],
                           page_title="Add Review")

#              ######################################################


@app.route('/add_rating/<book_id>/<int:rating>')
def add_rating(book_id, rating):
    user = mongo.db.users.find_one({"name": session['username']})
    the_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    rating_doc = {'book_name': the_book['book_name'],
                  'book_id': the_book['_id'],
                  'rating': rating,
                  'user_id': user['_id']}
    mongo.db.rating.insert_one(rating_doc)
    return redirect(url_for('display_book', book_id=the_book['_id']))

#              ######################################################


@app.route('/display_book/<book_id>')
def display_book(book_id):
    the_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    book_reviews = mongo.db.reviews.find({"book_id": the_book['_id']})
    the_book['rating'] = rating(the_book['_id'])

    if the_book['category_id']:
        the_book_category = the_book['category_id']
        related_books = list(mongo.db.books.
                             find({"category_id": the_book_category,
                                   "_id": {"$ne": ObjectId(book_id)}})
                             .limit(3))

    for book in related_books:
        book['rating'] = rating(the_book['_id'])

    related_books_author = list(mongo.db.books.
                                find({"book_author": the_book['book_author'],
                                      "_id": {"$ne": ObjectId(book_id)}})
                                .limit(3))
    for book in related_books_author:
        book['rating'] = rating(the_book['_id'])

    return render_template('displaybook.html',
                           categories=list(mongo.db.categories.find()),
                           related_books=related_books,
                           the_book=the_book,
                           reviews=book_reviews,
                           related_books_author=related_books_author,
                           page_title=the_book['book_name']
                           )

#              ######################################################


# this function used to view books by their category
# by selecting the required category from the dropdown list
# the result is displayed using pagination 10 books per page

@app.route('/view_by_cat/<category_id>')
def view_by_cat(category_id):
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    the_category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})

    books = list(mongo.db.books.
                 find({"book_category": the_category['category_name']}))

    for book in books:
        book['rating'] = rating(book['_id'])

    total = len(books)

    the_books = books[offset: offset + per_page]

    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap4',
                            format_total=True,   # format total. example 1,024
                            format_number=True,  # turn on format flag
                            record_name='Books', alignment='center')

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


@app.route('/view_by_author/<author>')
def view_by_author(author):
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    books = list(mongo.db.books.find({"book_author":
                                      {"$regex":  author, "$options": 'i'}}))

    for book in books:
        book['rating'] = rating(book['_id'])

    total = len(books)

    the_books = books[offset: offset + per_page]

    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap4',
                            format_total=True,   # format total. example 1,024
                            format_number=True,  # turn on format flag
                            record_name='Books', alignment='center')

    return render_template('viewbyauthor.html',
                           author=author,
                           books=the_books,
                           categories=list(mongo.db.categories.find()),
                           page=page,
                           per_page=per_page,
                           offset=offset,
                           pagination=pagination,
                           page_title="view by author")

#              ######################################################


@app.route('/rating/<book_id>')
def rating(book_id):
    rating_sum = 0
    rating_list = list(mongo.db.rating.
                       find({"book_id": book_id}))
    for book in rating_list:
        if book['rating']:
            _rating = book['rating']
            rating_sum += int(_rating)
    if len(rating_list) > 0:
        final_rating = round((rating_sum / len(rating_list)), 1)
    else:
        final_rating = "No Rating"
    return final_rating

#              ######################################################


# this function takes the book name from the search bar
# and search all the books name then display the result
# if more than one book have the same names all the books will be displayed
# this function also convert the name in search bar to lower and
# the book names in mongo to lower then compare the name
# from the search bar to the names of all the books in mogo db
# this function use pagination to display the searched books 10 books per page

@app.route('/find_book', methods=['GET', 'POST'])
def find_book():
    result = 0
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')

    if session.get('required_book'):
        if request.form.get('search'):
            required_book = request.form.get('search')
            session['required_book'] = required_book
        else:
            required_book = session['required_book']
    else:
        required_book = request.form.get('search')
        session['required_book'] = required_book

    result_books = list(mongo.db.books.
                        find({"book_name":
                             {"$regex":  required_book, "$options": 'i'}}))
    for book in result_books:
        book['rating'] = rating(book['_id'])
    total = len(result_books)

    if result_books:
        result = "Result Found: " + str(total)+" Books"
    else:
        result = "No Result Found"

    the_required_books = result_books[offset: offset + per_page]

    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap4',
                            format_total=True,   # format total. example 1,024
                            format_number=True,  # turn on format flag
                            record_name='Books', alignment='center')

    return render_template('search.html', books=the_required_books,
                           page=page,
                           per_page=per_page,
                           offset=offset,
                           pagination=pagination,
                           categories=list(mongo.db.categories.find()),
                           page_title="Search Result",
                           result=result)

#              ######################################################


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)

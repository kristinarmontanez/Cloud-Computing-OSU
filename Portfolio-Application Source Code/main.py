# _____________________________________________________________________________
# Name:             Kristina Montanez
# Date:             6/1/2022
# Class:            CS 493
# Project:          Portfolio Assignment
# File:             main.py
# Description:      Building and implementing an API with OAuth, deployed on
#                   Google App Engine. The web application will issue the
#                   relevant requests and processes responses so that the app
#                   can access protected resources on a user's Google account.
#                   Portfolio assignment building on prior assignment features.
# _____________________________________________________________________________
#
# _____________________________________________________________________________
#
#                   TABLE OF CONTENTS
#
#
#   1)      MODULE IMPORTS & SETUP
#   2)      CLIENT INFO
#   3)      ROOT ROUTE
#   4)      CREATE STATE & REDIRECT
#   5)      VERIFY STATE & RETRIEVE INFO
#   6)      VALIDATE ACCEPT HEADER
#   7)      VALIDATE OUR JWT
#   8)      GET USERS
#   9)      CREATE AND GET BOOKS
#   9.1)    POST /books
#   9.2)    GET /books
#   10)     GET/PUT/PATCH/DELETE SPECIFIC BOOK
#   10.1)   GET /books/:id
#   10.2)   PUT /books/:id
#   10.3)   PATCH /books/:id
#   10.4)   DELETE /books/:id
#   11)     CREATE AND GET REVIEWS
#   11.1)   POST /reviews
#   11.2)   GET /reviews
#   12)     GET/PUT/PATCH/DELETE SPECIFIC REVIEW
#   12.1)   GET /reviews/:id
#   12.2)   PUT /reviews/:id
#   12.3)   PATCH /reviews/:id
#   12.4)   DELETE /reviews/:id
#   13)     PUT/DELETE BOOK REVIEW RELATIONSHIP
#   13.1)   PUT /books/<book_id>/reviews/<review_id>
#   13.2)   DELETE /books/<book_id>/reviews/<review_id>
#   14)     RESETTING THE BOOKS LIST, REVIEW LIST, AND USER ACCOUNTS
#   14.1)   DELETE /reset/booksreviews
#   14.2)   DELETE /reset/users
# _____________________________________________________________________________



# _____________________________________________________________________________
#   1)      MODULE IMPORTS & SETUP
# _____________________________________________________________________________
from ftplib import error_temp
from google.cloud import datastore
# Grab our render template import as we are now using browser page.
from flask import Flask, render_template, request, redirect
# Per Ed Discussion #207, use the Requests library from Python.
from google.oauth2 import id_token
# Per Ed Discussion #207, use the Requests library from Python.
from google.auth.transport import requests
import requests as python_req
# needed for creating random state.
import string
import random
import constants
import json

app = Flask(__name__)
client = datastore.Client()



# _____________________________________________________________________________
#   2)      CLIENT INFO
# _____________________________________________________________________________
CLIENT_ID = '395905940165-pjjfiacebfimgsca8h5h885m4ughv556.apps.googleusercontent.com'
CLIENT_SECRET = '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'
REDIRECT_URI = 'https://montanek-portfolio.uw.r.appspot.com/oauth'
REDIRECT_URI_LOCAL = 'http://localhost:8080/oauth'



# _____________________________________________________________________________
#   3)      ROOT ROUTE
# _____________________________________________________________________________
# Root URL. Welcomes user and gives user a button to click to redirect
# to google account oauth login. Must of this code is provided on Google 
# Developer- "Using OAuth 2.0 for Web Server Applications".
# https://developers.google.com/identity/protocols/oauth2/web-server#httprest_5
@app.route('/', methods=['GET'])
def index():
    return render_template('Welcome.html')



# _____________________________________________________________________________
#   4)      CREATE STATE & REDIRECT
# _____________________________________________________________________________
@app.route('/get_state', methods=['GET'])
def get_state():
    # "How to generate a random string in Python" Found on Educative.io: 
    # https://www.educative.io/edpresso/how-to-generate-a-random-string-in-python
    # Note: Shows how to print a random ascii string of variable lengths. 
    letter = string.ascii_letters
    randomly_generated_state = ''.join(random.choice(letter) for i in range(15))
    # Create a user state, and save it in Datastore.
    user_state = datastore.Entity(client.key('states'))
    user_state.update({'state': randomly_generated_state})
    client.put(user_state)
    auth_uri = ('https://accounts.google.com/o/oauth2/auth?response_type=code'
                '&client_id={}&redirect_uri={}&scope=profile&state={}').format(CLIENT_ID, REDIRECT_URI, randomly_generated_state)
    return redirect(auth_uri)
    
    
    
# _____________________________________________________________________________
#   5)      VERIFY STATE & RETRIEVE INFO
# _____________________________________________________________________________
@app.route('/oauth', methods=['GET', 'POST'])
def oauth():
    # Search through our list in our datastore by creating a list. 
    # Grab the state provided in the request.
    query = client.query(kind='states')
    results = list(query.fetch())
    auth_state = request.args.get('state')
    # Next, check if the state provided in the request matches the 
    # state we find in our list. 
    matching_state = 0
    for e in results:
        if auth_state == e["state"]:
            state_to_delete = client.key('states', e.key.id)
            client.delete(state_to_delete)
            matching_state += 1
    # Once we search through the list, if we still do not find the 
    # matching state, we give the user an error warning.
    if matching_state is 0:
        return render_template('User Info.html',
                               user_error='ERROR: 401 Unauthorized',
                               user_status='STATUS: Invalid State Provided',
                               error_explanation='Click the "Home" button to refresh authorization.')
    # Next, grab the authorization code from the request to use for 
    # the token URL, as shown in the Google material: 
    # https://developers.google.com/identity/protocols/oauth2/web-server
    auth_code = request.args.get('code')
    data = {'code': auth_code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code',
            'access-type':'offline'}
    r = python_req.post('https://oauth2.googleapis.com/token', data=data)
    user_token = r.json()
    # We can now use the access token to get the user names from the
    # user's account filtered by "personFields"
    headers = {'Authorization': 'Bearer ' + user_token['access_token']}
    req_uri = 'https://people.googleapis.com/v1/people/me?personFields=names'
    r2 = python_req.get(req_uri, headers=headers)
    user_names = r2.json()
    # Render the User Info page with the user's account
    # first name, last name, and state. 
    # We can now use the access token to get the user names from the
    # user's account filtered by "personFields"
    grab_JWT = user_token['id_token']
    # our unique id from the jwt.
    get_unique_token = id_token.verify_oauth2_token(grab_JWT, requests.Request(), CLIENT_ID)
    # ID token is valid. Get the user's Google Account ID from the decoded token.
    unique_id_from_jwt = []
    unique_id_from_jwt.append(get_unique_token['sub'])
    # Check to make sure we do not have an old user who just needs to update their JWT.
    query = client.query(kind=constants.users)
    results = list(query.fetch())
    # Get the ids for each user.
    old_user = False
    for e in results:
        if get_unique_token['sub'] == e['PRIVATE ID']:
            old_user = True
    if old_user == False:
        # Create our user's account in the API.
        new_user = datastore.entity.Entity(key=client.key(constants.users))
        # add each attribute, including the extra 
        # attributes.
        new_user.update({"First Name": user_names['names'][0]['givenName'], 
                        "Last Name": user_names['names'][0]['familyName'], 
                        "PRIVATE ID": unique_id_from_jwt[0]})
        client.put(new_user)
        
    # Render the User Info page with the user's account
    # first name, last name, user_id, and JWT.
    return render_template('User Info.html',
                           hello_user_names="Hello " + user_names['names'][0]['givenName'] + " " +
                                                       user_names['names'][0]['familyName'] + "!",
                           unique_id="Your Unique I.D. is: " + str(get_unique_token['sub']),
                           id_token="Your JWT is: " + grab_JWT)



# _____________________________________________________________________________
#   6)      VALIDATE ACCEPT HEADER
# _____________________________________________________________________________
def Validate_Accept_Header(accept_header):
    if accept_header == None:
        error_message_missing_accept = (json.dumps({"Error": "The request is missing the Accept Header"}), 406) 
        return error_message_missing_accept
    elif (accept_header != "application/json") and (accept_header != "*/*"):
        error_message_wrong_accept = (json.dumps({"Error": "The request Accept Header must be 'application/json'"}), 406) 
        return error_message_wrong_accept
    else:
        return "true"



# _____________________________________________________________________________
#   7)      VALIDATE OUR JWT
# _____________________________________________________________________________
def Validate_JWT(user_token):
        # Similar to the python example code for "verify_jwt", 
        # Check for authorization header.
        if user_token == None:
            userid = (json.dumps({"Error": "The request is missing authorization"}), 401) 
            return userid
        # We need to get rid of the "Bearer" in front of the postman request.
        token = user_token.split(' ')
        # Grab our string in the second index, which should be the token itself.
        if len(token) == 2:
            token = token[1]
        try:
            # Specify the CLIENT_ID of the app that accesses the backend:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
            # ID token is valid. Get the user's Google Account ID from the decoded token.
            userid = []
            userid.append(idinfo['sub'])
            userid.append("User")
        except ValueError:
            # Invalid token
            userid = (json.dumps({"Error": "The request authorization is invalid"}), 401)
            return userid
        return userid




# _____________________________________________________________________________
#   8)      GET USERS
# _____________________________________________________________________________
# Endpoint for getting all users. Unprotected.
@app.route('/users', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def users():
    if request.method == 'GET':
        accept_header = request.headers.get("Accept")
        accept = Validate_Accept_Header(accept_header)
        if accept != "true":
            return accept
        query = client.query(kind=constants.users)
        results = list(query.fetch())
        for i in results:
            i["id"] = i.key.id
            del i["PRIVATE ID"]
        return (json.dumps(results), 200)
    elif (request.method == 'POST') or (request.method == 'PUT') or (request.method == 'PATCH') or (request.method == 'DELETE'):
      return (json.dumps({"The Request Method is not allowed. Please use 'GET' request method only"}), 405)





# _____________________________________________________________________________
#   9)      CREATE AND GET BOOKS
# _____________________________________________________________________________
# Endpoint for either creating a book or
# receiving a list of books. 
@app.route("/books", methods=['POST','GET', 'PUT', 'PATCH', 'DELETE'])
def books_get_post():
    if (request.method == 'PUT') or (request.method == 'PATCH') or (request.method == 'DELETE'):
        return (json.dumps({"The Request Method is not allowed. Please use 'POST' or 'GET' request methods only"}), 405)
    book_owner_id = None
    accept_header = request.headers.get("Accept")
    accept = Validate_Accept_Header(accept_header)
    if accept != "true":
        return accept
    user_token = request.headers.get("Authorization")
    valid = Validate_JWT(user_token)
    if valid[1] != "User":
        return valid
    if valid[1] == "User":
        query = client.query(kind=constants.users)
        results = list(query.fetch())
        # Get the ids for each book.
        
        for e in results:
            if e["PRIVATE ID"] == valid[0]:
                book_owner_id = e.key.id
        if book_owner_id == None:
            return (json.dumps({"Error": "No User Account exists for this login"}), 401)

    
    
    #   9.1)    POST /books
    # __________________________________________
    if request.method == 'POST':
            # Now let's grab our request body.
            content = request.get_json()
            # Check if we already have a book with this name: 
            query = client.query(kind=constants.books)
            results = list(query.fetch())
            # Check to see if our body has three
            # attributes.
            if (len(content) == 3):
                # Make sure the attributes are correct.
                if 'title' in content and 'author' in content and 'genre' in content:
                    new_book = datastore.entity.Entity(key=client.key(constants.books))
                    # add each attribute, including the extra 
                    # attributes.
                    owner = book_owner_id
                    new_book.update({"title": content["title"], 
                                    "author": content["author"], 
                                    "genre": content["genre"],
                                    "review_ids": [], 
                                    "owner_id": owner})
                    client.put(new_book)
                    new_book["id"] = new_book.key.id
                    new_book["self"] = request.host_url + 'books/' + str(new_book.key.id)
                    return (json.dumps(new_book), 201)
                else:
                    return (json.dumps({"Error": "The request object must use the required attributes"}), 403)
            else:
                return (json.dumps({"Error": "The request object is missing at least one of the required attributes"}), 403)
    
    
    
    #   9.2)    GET /books
    # __________________________________________
    elif request.method == 'GET':
        # Grab a list of our books.
        query = client.query(kind=constants.books)
        query.add_filter("owner_id", "=", book_owner_id)  
        total_result = list(query.fetch())
        # create our pagination, setting each
        # page to 3 books per page.
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        total = len(total_result)
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        # Get the ids for each book.
        for e in results:
            e["id"] = e.key.id
            # Place the correct direct url link.
            e["self"] = request.base_url + '/' + str(e["id"])
        # create our list of results.   
        output = {"books": results}
        if next_url:
            output["next"] = next_url
        return (json.dumps({"total items": total, "books": output}), 200)
    


# _____________________________________________________________________________
#   10)     GET/PUT/PATCH/DELETE SPECIFIC BOOK
# _____________________________________________________________________________    
@app.route('/books/<id>', methods=['GET', 'PUT', 'PATCH', 'DELETE', 'POST'])
def books_delete(id):
    if (request.method == 'POST'):
        return (json.dumps({"The Request Method is not allowed. Please use 'GET', 'PUT', 'PATCH', or 'DELETE' request methods only"}), 405)
    # Check Accept Header.
    book_owner_id = None
    accept_header = request.headers.get("Accept")
    accept = Validate_Accept_Header(accept_header)
    if accept != "true":
        return accept
    
    # Check Authorization Header.
    user_token = request.headers.get("Authorization")
    valid = Validate_JWT(user_token)
    if valid[1] != "User":
        return valid
    query = client.query(kind=constants.users)
    results = list(query.fetch())
    
    # Make sure the User Exists.
    for e in results:
        if e["PRIVATE ID"] == valid[0]:
            book_owner_id = e.key.id
    if book_owner_id == None:
        return (json.dumps({"Error": "No User Account exists for this login"}), 401)
    
    # Find our book by id.
    book_key = client.key(constants.books, int(id))
    book = client.get(key=book_key)   
    # If the book doesn't exist, let user know.
    if book == None:
        return (json.dumps({"Error": "No book with this book_id exists"}), 403)
    
    # Start to check through our "owner_ids" and make sure they own the book:
    owns_book = False
    if book["owner_id"] == book_owner_id:
        owns_book = True
    # If the user does not own the book.
    if owns_book == False:
        return (json.dumps({"Error": "The book is not owned by you"}), 403)
    
    
    
    
    #   10.1)   GET /books/:id
    # __________________________________________
    if request.method == 'GET':
        book["id"] = book.key.id
        # get our base URL.
        book["self"] = request.host_url + 'books/' + str(book.key.id)
        # Grab the ids and the "self" for each load.
        return(json.dumps(book), 200)
    
    
    
    #   10.2)   PUT /books/:id
    # __________________________________________
    if request.method == 'PUT':
        content = request.get_json()
        new_title = None
        new_author = None
        new_genre = None
        if 'title' in content:
            new_title = content["title"]
        if 'author' in content:
            new_author = content["author"]
        if 'genre' in content:
            new_genre = content["genre"]
        # Make sure our request keys are valid.
        # If all is valid, put our book.
        book.update({"title": new_title, 
                     "author": new_author,
                     "genre": new_genre})
        # Update the book, and get the updated
        # Version.
        client.put(book)
        return_book = client.get(key=book_key)
        return_book["id"] = return_book.key.id
        # get our base URL.
        return_book["self"] = request.host_url + 'books/' + str(return_book.key.id)
        # Grab the ids and the "self" for each load.
        return(json.dumps(return_book), 201)
    
    
    
    #   10.3)   PATCH /books/:id
    # __________________________________________
    if request.method == 'PATCH':
        content = request.get_json()
        new_title = book["title"]
        new_author = book["author"]
        new_genre = book["genre"]
        if 'title' in content:
            new_title = content["title"]
        if 'author' in content:
            new_author = content["author"]
        if 'genre' in content:
            new_genre = content["genre"]
        # Make sure our request keys are valid.
        # If all is valid, put our book.
        book.update({"title": new_title, 
                     "author": new_author,
                     "genre": new_genre})
        # Update the book, and get the updated
        # Version.
        client.put(book)
        return_book = client.get(key=book_key)
        return_book["id"] = return_book.key.id
        # get our base URL.
        return_book["self"] = request.host_url + 'books/' + str(return_book.key.id)
        # Grab the ids and the "self" for each load.
        return(json.dumps(return_book), 201)
    
    
    
    #   10.4)   DELETE /books/:id
    # __________________________________________
    elif request.method == 'DELETE':
        # Make sure to remove any book ids from reviews before deleting.
        if book["review_ids"] != []:
            for e in book["review_ids"]:
                review_key = client.key(constants.reviews, int(e))
                delete_review = client.get(key=review_key)
                # Check if the review has this book 
                # If the review has the book listed,
                # make the book_id empty.
                if delete_review["book_id"] != None:
                    delete_review["book_id"] = None
                    client.put(delete_review) 
        client.delete(book_key)
        # Finally, delete the book.
        return ('',204)



# _____________________________________________________________________________
#   11)     CREATE AND GET REVIEWS
# _____________________________________________________________________________
# Endpoint for either creating a review or
# receiving a list of reviews. 
@app.route("/reviews", methods=['POST','GET', 'PUT', 'PATCH', 'DELETE'])
def reviews_get_post():
    if (request.method == 'PUT') or (request.method == 'PATCH') or (request.method == 'DELETE'):
        return (json.dumps({"The Request Method is not allowed. Please use 'POST' or 'GET' request methods only"}), 405)
    review_owner_id = None
    accept_header = request.headers.get("Accept")
    accept = Validate_Accept_Header(accept_header)
    if accept != "true":
        return accept
    user_token = request.headers.get("Authorization")
    valid = Validate_JWT(user_token)
    if valid[1] != "User":
        return valid
    if valid[1] == "User":
        query = client.query(kind=constants.users)
        results = list(query.fetch())
        # Get the ids for each review.
        
        for e in results:
            if e["PRIVATE ID"] == valid[0]:
                review_owner_id = e.key.id
        if review_owner_id == None:
            return (json.dumps({"Error": "No User Account exists for this login"}), 401)

    
    
    #   11.1)   POST /reviews
    # __________________________________________
    if request.method == 'POST':
            # Now let's grab our request body.
            content = request.get_json()
            # Check if we already have a review with this name: 
            query = client.query(kind=constants.reviews)
            results = list(query.fetch())
            # Check to see if our body has three
            # attributes.
            if (len(content) == 3):
                # Make sure the attributes are correct.
                if 'date' in content and 'rating' in content and 'comment' in content:
                    new_review = datastore.entity.Entity(key=client.key(constants.reviews))
                    # add each attribute, including the extra 
                    # attributes.
                    owner = review_owner_id
                    new_review.update({"date": content["date"], 
                                    "rating": content["rating"], 
                                    "comment": content["comment"],
                                    "book_id": None, 
                                    "owner_id": owner})
                    client.put(new_review)
                    new_review["id"] = new_review.key.id
                    new_review["self"] = request.host_url + 'reviews/' + str(new_review.key.id)
                    return (json.dumps(new_review), 201)
                else:
                    return (json.dumps({"Error": "The request object must use the required attributes"}), 403)
            else:
                return (json.dumps({"Error": "The request object is missing at least one of the required attributes"}), 403)
    
    
    
    #   11.2)   GET /reviews
    # __________________________________________
    elif request.method == 'GET':
        # Grab a list of our reviews.
        query = client.query(kind=constants.reviews)
        query.add_filter("owner_id", "=", review_owner_id)  
        total_result = list(query.fetch())
        # create our pagination, setting each
        # page to 3 reviews per page.
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        total = len(total_result)
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        # Get the ids for each review.
        for e in results:
            e["id"] = e.key.id
            # Place the correct direct url link.
            e["self"] = request.base_url + '/' + str(e["id"])
        # create our list of results.   
        output = {"reviews": results}
        if next_url:
            output["next"] = next_url
        return (json.dumps({"total items": total, "reviews": output}), 200)
   

    
# _____________________________________________________________________________
#   12)     GET/PUT/PATCH/DELETE SPECIFIC REVIEW
# _____________________________________________________________________________    
@app.route('/reviews/<id>', methods=['GET', 'PUT', 'PATCH', 'DELETE', 'POST'])
def reviews_delete(id):
    if request.method == 'POST':
        return (json.dumps({"The Request Method is not allowed. Please use 'GET', 'PUT', 'PATCH', or 'DELETE' request methods only"}), 405)
    # Check Accept Header.
    review_owner_id = None
    accept_header = request.headers.get("Accept")
    accept = Validate_Accept_Header(accept_header)
    if accept != "true":
        return accept
    
    # Check Authorization Header.
    user_token = request.headers.get("Authorization")
    valid = Validate_JWT(user_token)
    if valid[1] != "User":
        return valid
    query = client.query(kind=constants.users)
    results = list(query.fetch())
    
    # Make sure the User Exists.
    for e in results:
        if e["PRIVATE ID"] == valid[0]:
            review_owner_id = e.key.id
    if review_owner_id == None:
        return (json.dumps({"Error": "No User Account exists for this login"}), 401)
    
    # Find our review by id.
    review_key = client.key(constants.reviews, int(id))
    review = client.get(key=review_key)  
    # If the review doesn't exist, let user know.
    if review == None:
        return (json.dumps({"Error": "No review with this review_id exists"}), 403)
    
    # Start to check through our "owner_ids" and make sure they own the review:
    owns_review = False
    if review["owner_id"] == review_owner_id:
        owns_review = True
    # If the user does not own the review.
    if owns_review == False:
        return (json.dumps({"Error": "The review is not owned by you"}), 403)
    
    
    
    #   12.1)   GET /reviews/:id
    # __________________________________________
    if request.method == 'GET':
        review["id"] = review.key.id
        # get our base URL.
        review["self"] = request.host_url + 'reviews/' + str(review.key.id)
        # Grab the ids and the "self" for each load.
        return(json.dumps(review), 200)
    
    
    
    #   12.2)   PUT /reviews/:id
    # __________________________________________
    if request.method == 'PUT':
        content = request.get_json()
        new_date = None
        new_rating = None
        new_comment = None
        if 'date' in content:
            new_date = content["date"]
        if 'rating' in content:
            new_rating = content["rating"]
        if 'comment' in content:
            new_comment = content["comment"]
        # Make sure our request keys are valid.
        # If all is valid, put our review.
        review.update({"date": new_date, 
                     "rating": new_rating,
                     "comment": new_comment})
        # Update the review, and get the updated
        # Version.
        client.put(review)
        return_review = client.get(key=review_key)
        return_review["id"] = return_review.key.id
        # get our base URL.
        return_review["self"] = request.host_url + 'reviews/' + str(return_review.key.id)
        # Grab the ids and the "self" for each load.
        return(json.dumps(return_review), 201)
    
    
    
    #   12.3)   PATCH /reviews/:id
    # __________________________________________
    if request.method == 'PATCH':
        content = request.get_json()
        new_date = review["date"]
        new_rating = review["rating"]
        new_comment = review["comment"]
        if 'date' in content:
            new_date = content["date"]
        if 'rating' in content:
            new_rating = content["rating"]
        if 'comment' in content:
            new_comment = content["comment"]
        # Make sure our request keys are valid.
        # If all is valid, put our review.
        review.update({"date": new_date, 
                     "rating": new_rating,
                     "comment": new_comment})
        # Update the review, and get the updated
        # Version.
        client.put(review)
        return_review = client.get(key=review_key)
        return_review["id"] = return_review.key.id
        # get our base URL.
        return_review["self"] = request.host_url + 'reviews/' + str(return_review.key.id)
        # Grab the ids and the "self" for each load.
        return(json.dumps(return_review), 201)
    
    
    
    #   12.4)   DELETE /reviews/:id
    # __________________________________________
    elif request.method == 'DELETE':
        # Make sure to remove any review ids from books before deleting.
        if review["book_id"] != None:
            review_to_delete = review["book_id"]
            book_key = client.key(constants.books, int(review_to_delete))
            book_to_change = client.get(key=book_key)
            for i in book_to_change["review_ids"]:
                if i == review["id"]:
                    book_to_change["review_ids"].remove(review["id"])
            client.put(book_to_change)
        
        # Finally, delete the review.
        client.delete(review_key)
        return ('',204)



# _____________________________________________________________________________
#   13)     PUT/DELETE BOOK REVIEW RELATIONSHIP
# _____________________________________________________________________________    
@app.route('/books/<book_id>/reviews/<review_id>', methods=['PUT', 'DELETE', 'POST', 'GET', 'PATCH'])
def books_reviews_put_delete(book_id, review_id):
    if (request.method == 'POST') or (request.method == 'GET') or (request.method == 'PATCH'):
        return (json.dumps({"The Request Method is not allowed. Please use 'PUT' or 'DELETE' request methods only"}), 405)
    # Check Accept Header.
    owner_id = None
    accept_header = request.headers.get("Accept")
    accept = Validate_Accept_Header(accept_header)
    if accept != "true":
        return accept
    
    # Check Authorization Header.
    user_token = request.headers.get("Authorization")
    valid = Validate_JWT(user_token)
    if valid[1] != "User":
        return valid
    query = client.query(kind=constants.users)
    results = list(query.fetch())
    
    # Make sure the User Exists.
    for e in results:
        if e["PRIVATE ID"] == valid[0]:
            owner_id = e.key.id
    if owner_id == None:
        return (json.dumps({"Error": "No User Account exists for this login"}), 401)
    
    # Find our book by id.
    book_key = client.key(constants.books, int(book_id))
    book = client.get(key=book_key) 
    book["id"] = book.key.id  
    # If the book doesn't exist, let user know.
    if book == None:
        return (json.dumps({"Error": "No book with this book_id exists"}), 403)
    
    # Start to check through our "owner_ids" and make sure they own the book:
    owns_book = False
    if book["owner_id"] == owner_id:
        owns_book = True
    # If the user does not own the book.
    if owns_book == False:
        return (json.dumps({"Error": "The book is not owned by you"}), 403)
    
    # Find our review by id.
    review_key = client.key(constants.reviews, int(review_id))
    review = client.get(key=review_key)    
    review["id"] = review.key.id
    # If the book doesn't exist, let user know.
    if review == None:
        return (json.dumps({"Error": "No review with this review_id exists"}), 403)
    
    # Start to check through our "owner_ids" and make sure they own the book:
    owns_review = False
    if review["owner_id"] == owner_id:
        owns_review = True
    # If the user does not own the book.
    if owns_review == False:
        return (json.dumps({"Error": "The review is not owned by you"}), 403)
    
    
    
    #   13.1)   PUT /books/<book_id>/reviews/<review_id>
    # __________________________________________
    if request.method == 'PUT':
        # Check to see if we already have the relationship.
        if review["book_id"] == book["id"]:
            return (json.dumps({"Error": "The book and review are already connected"}), 403)
        
        # Make sure we take care of the book that might already have the review id listed.
        if review["book_id"] != None:
            book_to_change = client.get(key=review["book_id"])
            book_to_change["review_ids"].remove(review["id"]) 
            client.put(book_to_change) 
        # Update the book.
        book["review_ids"].append(review["id"])
        client.put(book)
        
        # Update the review.
        review.update({"book_id": book["id"]})
        client.put(review)
        
        # Now create our updated book to show to the user.
        return_book = client.get(key=book_key)
        return_book["id"] = return_book.key.id
        # get our base URL.
        return_book["self"] = request.host_url + 'books/' + str(return_book.key.id)
        
        # Now create our updated review to show to the user.
        return_review = client.get(key=review_key)
        return_review["id"] = return_review.key.id
        # get our base URL.
        return_review["self"] = request.host_url + 'reviews/' + str(return_review.key.id)
        
        # Grab the ids and the "self" for each load.
        return(json.dumps({"book": return_book, "review": return_review}), 201)
    


    #   13.2)   DELETE /books/<book_id>/reviews/<review_id>
    # __________________________________________
    elif request.method == 'DELETE':
        # Check to see if we already have the relationship.
        if review["book_id"] == None:
            return (json.dumps({"Error": "The book and review are already disconnected"}), 403)
        
        # Update the book.
        book["review_ids"].remove(review["id"])
        client.put(book)
        
        # Update the review.
        review.update({"book_id": None})
        client.put(review)
        
        # Finally, send a success message.
        return ('',204)



# _____________________________________________________________________________
#   14)     RESETTING THE BOOKS LIST, REVIEW LIST, AND USER ACCOUNTS
# _____________________________________________________________________________
# For testing purposes only-reset all book lists.
# Does not require any protection, or header specification. 



    #   14.1)   DELETE /reset/booksreviews
    # __________________________________________
@app.route('/reset/booksreviews', methods=['DELETE'])
def books_reviews_delete():
    # Grab a list of our books.
    book_query = client.query(kind=constants.books)
    book_results = list(book_query.fetch())
    client.delete_multi([i.key for i in book_results])
    review_query = client.query(kind=constants.reviews)
    review_results = list(review_query.fetch())
    client.delete_multi(review_results)
    return ('',204)



    #   14.2)   DELETE /reset/users
    # __________________________________________
@app.route('/reset/users', methods=['DELETE'])
def user_accounts_delete():
    user_query = client.query(kind=constants.users)
    user_results = list(user_query.fetch())
    client.delete_multi(user_results)
    return ('',204)



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

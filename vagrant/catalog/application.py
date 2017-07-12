import random
import string
import json
import httplib2
import requests
from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_structure import Base, Category, Item, User
from oauth2client.client import FlowExchangeError, flow_from_clientsecrets
from functools import wraps

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog"

# Connect to Database and create database session
engine = create_engine('sqlite:///database.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

print (' * Database connected')


# Login - Logout - Start
# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '''
     "style = "width: 100px; height: 100px;border-radius:
    50px;-webkit-border-radius: 50px;-moz-border-radius: 150px;">
    '''
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url_string = (
        'https://graph.facebook.com/oauth/access_token?'
        'grant_type=fb_exchange_token'
        '&client_id=%s&client_secret=%s&fb_exchange_token=%s'
    )
    url = (url_string) % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
    Due to the formatting for the result from the server token exchange we
    have to split the token first on commas and select the first index which
    gives us the key : value for the server access token then we split it on
    colons to pull out the actual token value and replace the remaining quotes
    with nothing so that it can be used directly in the graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')
    url_string = (
        'https://graph.facebook.com/v2.8/me?access_token=%s'
        '&fields=name,id,email'
    )
    url = (url_string) % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url_string = (
        'https://graph.facebook.com/v2.8/me/picture?access_token=%s'
        '&redirect=0&height=200&width=200'
    )
    url = (url_string) % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '''
     " style = "width: 100px; height: 100px;border-radius: 150px;
    -webkit-border-radius: 50px;-moz-border-radius: 50px;">
    '''

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            # del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showAll'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showAll'))
# Login - Logout - End


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# JSON APIs to view Catalog Information
@app.route('/json')
def catalogJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=[c.serialize for c in categories])


@app.route('/category/<int:category_id>/json')
def categoryJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/category/<int:category_id>/<int:item_id>/json')
def itemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


# Show all categories and all items
@app.route('/')
def showAll():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).order_by(desc(Item.created_on))
    if 'user_id' not in login_session:
        return render_template(
            'public_catalog.html', categories=categories, items=items)
    else:
        return render_template(
            'catalog.html', categories=categories, items=items)


# Show a category
@app.route('/category/<int:category_id>/')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    creator = getUserInfo(category.created_by)

    if 'user_id' not in login_session or \
            login_session['user_id'] != creator.id:
        return render_template(
            'public_category.html', items=items,
            category=category, creator=creator)
    else:
        return render_template(
            'menu.html', items=items,
            category=category, creator=creator)


# Create a new category
@app.route('/category/new', methods=['GET', 'POST'])
@login_required
def newCategory():
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'], created_by=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showAll'))
    else:
        return render_template('newCategory.html')


# Edit a category
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if editedCategory.created_by != login_session['user_id']:
        script = (
            "<script>function myFunction() {alert('You are not authorized "
            "to edit this category');}</script><body onload='myFunction()'>"
        )
        return script
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % editedCategory.name)
            return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('editCategory.html', category=editedCategory)


# Delete a catalog
@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if categoryToDelete.created_by != login_session['user_id']:
        script = (
            "<script>function myFunction() {alert('You are not authorized to "
            "delete this category');}</script><body onload='myFunction()'>"
        )
        return script
    if request.method == 'POST':
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name)
        session.commit()
        return redirect(url_for('showAll'))
    else:
        return render_template(
            'deleteCategory.html', category=categoryToDelete)


# Create a new menu item
@app.route('/category/<int:category_id>/newitem', methods=['GET', 'POST'])
@login_required
def newItem(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    if category.created_by != login_session['user_id']:
        script = (
            "<script>function myFunction() {alert('You are not authorized to "
            "create new item for this category');}</script>"
            "<body onload='myFunction()'>"
        )
        return script
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=category_id,
            created_by=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Item Successfully Created')
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id)


# Edit an item
@app.route('/category/<int:category_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editItem(category_id, item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).all()

    if editedItem.created_by != login_session['user_id']:
        script = (
            "<script>function myFunction() {alert('You are not authorized "
            "to edit item for this category');}</script>"
            "<body onload='myFunction()'>"
        )
        return script
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template(
            'edititem.html', category_id=category_id,
            item_id=item_id, item=editedItem)


# Delete a menu item
@app.route('/category/<int:category_id>/<int:item_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteItem(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if itemToDelete.created_by != login_session['user_id']:
        script = (
            "<script>function myFunction() {alert('You are not authorized"
            " to delete item for this category');}</script>"
            "<body onload='myFunction()'>"
        )
        return script
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('deleteitem.html', category=category)


if __name__ == '__main__':
    app.secret_key = 'FRp2qNW?AQ^@e7J^9s6=+wgFtpY@Duyt&rf2?W7s'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)

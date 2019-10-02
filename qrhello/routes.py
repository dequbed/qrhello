from flask import make_response, request, redirect, url_for, render_template, flash
from validate_email import validate_email
from qrhello import app, db

import qrhello.dbfoo

@app.route('/l/hallo')
def hallo():
    if not request.cookies.get("name"):
        return redirect(url_for("register") + "?return_to=" + url_for("hallo"))
    else:
        name = request.cookies.get("name")
        email = request.cookies.get("email")
        return render_template("hallo.html", name=name, email=email)

@app.route('/l/goodbye')
def goodbye():
    # TODO: Abfragen der noch gehaltenen Items & Wiedergabe als Liste mit Wiki-Links.
    # Falls nichts mehr offen ist --> huldvolle Verabschiedung & Frage, ob alles okay war --> mailto:tasso.mulzer@beuth-hochschule.de.
    return render_template("goodbye.html")

@app.route('/l/i/<string:item_id>', methods=['GET', 'POST'])
def reserve_item(item_id):
    # In any case we need those cookies set
    if not request.cookies.get("name"):
        return redirect(url_for("register") + "?return_to=/l/i/" + item_id)

    db = qrhello.db
    by_me = False
    # Again, GET means trying to get the form
    if request.method == 'GET':
        claimant = db.claimed(item_id)
        if claimant is not None:
            reserved = True
            (reserved_by, cmail) = claimant

            email = request.cookies.get("email")
            # by_me :: Boolean
            by_me = email == cmail
        else:
            reserved = False
            reserved_by = None

        return render_template("reserveitem.html", item_id=item_id, reserved=reserved, reserved_by=reserved_by, by_me=by_me)
    else:
        name = request.cookies.get("name")
        email = request.cookies.get("email")

        claimant = db.claimed(item_id)
        if claimant:
            (_, cmail) = claimant
            email = request.cookies.get("email")
            is_self = email == cmail
            if is_self:
                db.return_now(item_id)
                return redirect(url_for('reserve_item', item_id=item_id))

        db.claim(item_id, name, email)

        # Method is POST, so they're either trying to reserve the item or take over the item.
        return redirect(url_for('reserve_item', item_id=item_id))

@app.route('/l/register', methods=['GET', 'POST'])
def register():
    # Check the req method first. POST means submitting form contents, GET means trying to get the form.
    if request.method == 'POST':
        try:
            # Valid form has both name and email.
            name = request.form['name']
            email = request.form['email']

            # Sanity checks...
            # Empty strings are 'falsy'
            if not name:
                raise ValueError("Name darf nicht leer sein")
            if not email:
                raise ValueError("Email darf nicht leer sein")
            if not validate_email(email):
                raise ValueError("Ungültiges Email-Format: %s" % email)

            # Most URLs set the 'return_to'.
            redirect_to = request.args.get('return_to')
            if redirect_to:
                response = redirect(redirect_to)
            else:
                # if there isn't a 'return_to' set, default to just sending to the hello page
                response = redirect(url_for("hallo"))

            # We need to set these cookies so people don't have to do this again
            response.set_cookie("name", name)
            response.set_cookie("email", email)
            return response

        except KeyError as e:
            # Invalid form; was either missing name or email
            abort(400)
        except ValueError as e:
            # Invalid values in the form
            abort(400)

    else:
        name = request.cookies.get("name")
        email = request.cookies.get("email")

        if name is None or email is None:
            # GET request => Send the register form
            return render_template("register.html", cookies_set=False)
        else:
            return render_template("register.html", cookies_set=True, name=name, email=email)

@app.route('/l/ueber')
def about():
    name = request.cookies.get("name")
    return render_template('about.html', name=name)

def reserved_by_item(item_id):
    return qrhello.dbfoo.sql_is_reserved(item_id)

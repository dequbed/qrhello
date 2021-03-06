# coding=utf-8
from flask import make_response, request, redirect, url_for, render_template
from validate_email import validate_email

from qrhello import app, db

import qrhello.dbfoo


@app.route('/')
@app.route('/l/hello')
@app.route('/l/hallo')
def hallo():
    if not request.cookies.get("name"):
        return redirect(url_for("register") + "?return_to=" + url_for("hallo"))
    else:
        db = qrhello.db
        name = request.cookies.get("name")
        email = request.cookies.get("email")
        db.hello(name, email)
        return render_template("hallo.html", name=name, email=email)


@app.route('/l/bye', methods=['GET', 'POST'])
@app.route('/l/goodbye', methods=['GET', 'POST'])
@app.route('/l/tschuess', methods=['GET', 'POST'])
@app.route('/l/wiedersehen', methods=['GET', 'POST'])
@app.route('/l/aufwiedersehen', methods=['GET', 'POST'])
def goodbye():
    # In any case we need those cookies set
    if not request.cookies.get("name"):
        return redirect(url_for("register") + "?return_to=/l/bye")

    name = request.cookies.get("name")
    email = request.cookies.get("email")
    db = qrhello.db
    sc = db.still_claimed(email)
    not_okay = len(sc) > 0

    # Again, GET means trying to get the form
    if request.method == 'GET':
        # Falls nichts mehr offen ist --> huldvolle Verabschiedung & Frage, ob alles okay war
        # --> mailto:tasso.mulzer@beuth-hochschule.de.
        return render_template("bye.html", name=name, items=sc, not_okay=not_okay)
    else:   # POST // Alles Zurueckgeben
        for item in sc:
            db.return_now(item[0], email)
        return redirect(url_for("goodbye"))


@app.route('/l/i/<string:item_id>', methods=['GET', 'POST'])
def use_item(item_id):
    # In any case we need those cookies set
    if not request.cookies.get("name"):
        return redirect(url_for("register") + "?return_to=/l/i/" + item_id)

    db = qrhello.db
    by_me = False
    # Again, GET means trying to get the form
    if request.method == 'GET':
        claimant = db.claimed(item_id)
        if claimant is not None:
            used = True
            (used_by, cmail) = claimant

            email = request.cookies.get("email")
            # by_me :: Boolean
            by_me = email == cmail
        else:
            used = False
            used_by = None

        return render_template("useitem.html", item_id=item_id, used=used, used_by=used_by, by_me=by_me)
    else:
        name = request.cookies.get("name")
        email = request.cookies.get("email")

        claimant = db.claimed(item_id)
        if claimant:
            (_, cmail) = claimant
            email = request.cookies.get("email")
            is_self = email == cmail
            if is_self:
                db.return_now(item_id, email)
                return redirect(url_for('use_item', item_id=item_id))

        db.claim(item_id, name, email)

        # Method is POST, so they're either trying to use the item or take over the item.
        return redirect(url_for('use_item', item_id=item_id))

@app.route('/l/return/<string:item_id>', methods=['GET'])
def return_item(item_id):
    if not request.cookies.get("name"):
        return redirect(url_for("register") + "?return_to=/l/return/" + item_id)
    name = request.cookies.get("name")
    # email = request.cookies.get("email")
    if name == 'Tasso' or name == 'Norbert':
        db.return_force(item_id)
    return redirect(url_for("reserved_overall"))

@app.route('/l/m/<string:item_id>', methods=['GET', 'POST'])
def use_multi_item(item_id):
    # In any case we need those cookies set
    if not request.cookies.get("name"):
        return redirect(url_for("register") + "?return_to=/l/m/" + item_id)
    if not request.cookies.get("email"):
        return redirect(url_for("register") + "?return_to=/l/m/" + item_id)

    name = request.cookies.get("name")
    email = request.cookies.get("email")

    db = qrhello.db
    by_me = False
    # Again, GET means trying to get the form
    if request.method == 'GET':
        claimed_by_me = db.claimed_by_me(item_id, email)
        if claimed_by_me is not None:
            used = True
            used_by = name
            by_me = True
        # claimed by someone else is of no interest for multi-items.
        else:   # not claimed
            used = False
            used_by = None

        return render_template("useitem.html", item_id=item_id, used=used, used_by=used_by, by_me=by_me)
    else:

        claimant = db.claimed_by_me(item_id, email)
        if claimant:
            db.return_now(item_id, email)
            return redirect(url_for('use_multi_item', item_id=item_id))
        else:
            db.claim(item_id, name, email)

        # Method is POST, so they're either trying to use the item or take over the item.
        return redirect(url_for('use_multi_item', item_id=item_id))


@app.route('/l/u/<string:item_id>', methods=['GET', 'POST'])
def item_use(item_id):
    iu = db.item_usage(item_id)
    return render_template('item_usage.html', items=iu)
    pass


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
            db.hello(name, email)
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

@app.route('/l/claimed')
@app.route('/l/reserved')
def reserved():
    # In any case we need those cookies set
    if not request.cookies.get("name"):
        return redirect(url_for("register") + "?return_to=/l/claimed")

    name = request.cookies.get("name")
    email = request.cookies.get("email")
    sc = db.still_claimed(email)
    return render_template('claimed.html', name=name, items=sc)

@app.route('/l/aufraeumen')
@app.route('/l/cleanup')
def reserved_overall():
    # # In any case we need those cookies set
    # if not request.cookies.get("name"):
    #     return redirect(url_for("register") + "?return_to=/l/claimed")

    # name = request.cookies.get("name")
    # email = request.cookies.get("email")
    sc = db.still_claimed(overall=True)
    name = request.cookies.get("name")
    priv = False
    if name == 'Tasso' or name == 'Norbert':
        priv = True
    return render_template('claimed_overall.html', items=sc, priv=priv)

@app.route('/l/anwesend')
def here_today():
    # In any case we need those cookies set
    if not request.cookies.get("name"):
        return redirect(url_for("register") + "?return_to=/l/anwesend")

    name = request.cookies.get("name")
    # email = request.cookies.get("email")
    if name == 'Tasso' or name == 'Norbert':
        ht = db.here_today()
    else:
        ht = (None,)

    return render_template('here_today.html', items=ht)
    pass

def used_by_item(item_id):
    return qrhello.dbfoo.sql_is_used(item_id)

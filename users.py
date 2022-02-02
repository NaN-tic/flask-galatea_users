#This file is part galatea_users blueprint for Flask.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from flask import (Blueprint, request, render_template, current_app, session,
    redirect, url_for, flash, g)
from galatea.tryton import tryton
from flask_babel import gettext as _, lazy_gettext
from flask_paginate import Pagination
from galatea.helpers import login_required, manager_required

users = Blueprint('users', __name__, template_folder='templates')

DISPLAY_MSG = lazy_gettext('Displaying <b>{start} - {end}</b> of <b>{total}</b>')

LIMIT_USERS = current_app.config.get('TRYTON_PAGINATION_USERS_LIMIT', 20)

Website = tryton.pool.get('galatea.website')
GalateaUser = tryton.pool.get('galatea.user')

@users.route('/users', methods=['GET', 'POST'], endpoint="users")
@login_required
@manager_required
@tryton.transaction()
def users_list(lang):
    try:
        user_id = (session['user2manager']
            if session.get('user2manager') else session['user'])
        domain = GalateaUser.users_domain(user_id)
    except AttributeError:
        domain = []

    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    # limit
    if request.args.get('limit'):
        try:
            limit = int(request.args.get('limit'))
            session['users'] = limit
        except:
            limit = LIMIT_USERS
    else:
        limit = session.get('users', LIMIT_USERS)

    if request.args.get('q'):
        domain.append(('rec_name', 'ilike', '%'+request.args.get('q')+'%'))
    if session.get('user2manager'):
        domain.append(('id', '=', session['user']))

    total = GalateaUser.search_count(domain)
    offset = (page-1)*limit

    order = [('party', 'ASC'), ('email', 'ASC')]
    users = GalateaUser.search(domain, offset, limit, order)

    pagination = Pagination(page=page, total=total, per_page=limit, display_msg=DISPLAY_MSG, bs_version='3')

    #breadcumbs
    breadcrumbs = [{
        'slug': url_for('admin', lang=g.language),
        'name': _('Admin'),
        }, {
        'slug': url_for('.users', lang=g.language),
        'name': _('Users'),
        },]

    return render_template('admin/users.html',
        users=users,
        q=request.args.get('q'),
        pagination=pagination,
        breadcrumbs=breadcrumbs)

@users.route('/login', methods=['GET', 'POST'], endpoint="login")
@login_required
@manager_required
@tryton.transaction()
def login(lang):
    try:
        user_id = (session['user2manager']
            if session.get('user2manager') else session['user'])
        domain = GalateaUser.users_domain(user_id)
    except AttributeError:
        domain = []

    email = request.args.get('email')
    if email and not session.get('user2manager'):
        domain.append(('email', '=', email))
        users = GalateaUser.search(domain, limit=1)
        if users:
            user, = users

            data = None
            try:
                data = GalateaUser.users_login(user)
            except AttributeError:
                pass
            session['user2manager'] = session['user']
            session['user'] = user.id
            session['display_name'] = user.display_name
            session['customer'] = user.party.id
            session['email'] = user.email
            if data:
                session.update(data)
            flash(_('Successfully login ' + user.display_name), 'success')
    return redirect(url_for('.users', lang=g.language))

@users.route('/logout', methods=['GET', 'POST'], endpoint="logout")
@login_required
@manager_required
@tryton.transaction()
def logout(lang):
    if session.get('user2manager'):
        user = GalateaUser(session['user2manager'])
        data = None
        try:
            data = GalateaUser.users_logout(user)
        except AttributeError:
            pass
        session['user'] = user.id
        session['display_name'] = user.display_name
        session['customer'] = user.party.id
        session['email'] = user.email
        session['user2manager'] = None
        if data:
            session.update(data)
        flash(_('Successfully logout.'), 'success')
    return redirect(url_for('.users', lang=g.language))

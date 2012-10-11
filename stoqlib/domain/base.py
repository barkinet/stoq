# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Base routines for domain modules """

# pylint: disable=E1101
from stoqlib.database.orm import ForeignKey
from stoqlib.database.orm import ORMObject, const, AND, ILIKE
from stoqlib.database.runtime import (StoqlibTransaction,
                                      get_current_user, get_current_station)
from stoqlib.domain.system import TransactionEntry


class Domain(ORMObject):
    """Base class for domain objects in Stoq.
    """

    te_created = ForeignKey('TransactionEntry', default=None)
    te_modified = ForeignKey('TransactionEntry', default=None)

    def __init__(self, *args, **kwargs):
        ORMObject.__init__(self, *args, **kwargs)

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.id)

    #
    # ORMObject
    #

    def _create(self, *args, **kwargs):
        if not isinstance(self._connection, StoqlibTransaction):
            raise TypeError(
                "creating a %s instance needs a StoqlibTransaction, not %s"
                % (self.__class__.__name__,
                   self._connection.__class__.__name__))
        # Don't flush right now. The object being created is not complete
        # yet!
        conn = self._connection
        conn.block_implicit_flushes()
        user = get_current_user(conn)
        station = get_current_station(conn)
        conn.unblock_implicit_flushes()

        for entry, entry_type in [('te_created', TransactionEntry.CREATED),
                                  ('te_modified', TransactionEntry.MODIFIED)]:
            kwargs[entry] = TransactionEntry(
                te_time=const.NOW(),
                user_id=user and user.id,
                station_id=station and station.id,
                type=entry_type,
                connection=conn)
        super(Domain, self)._create(*args, **kwargs)
        conn.add_created_object(self)

    def destroySelf(self):
        super(Domain, self).destroySelf()

        if isinstance(self._connection, StoqlibTransaction):
            self._connection.add_deleted_object(self)

    def on_object_changed(self):
        if self.sqlmeta._creating:
            return
        connection = self._connection
        if isinstance(connection, StoqlibTransaction):
            connection.add_modified_object(self)

    #
    # Public API
    #

    def on_create(self):
        """Called when *self* is about to be created on the database

        This hook can be overridden on child classes for improved functionality.

        A trick you may want to use: Use :meth:`ORMObject.get_connection` to get the
        :class:`transaction <stoqlib.database.runtime.StoqlibTransaction>` in which
        *self* lives and do your modifications in it.
        """

    def on_update(self):
        """Called when *self* is about to be updated on the database

        This hook can be overridden on child classes for improved
        functionality.

        A trick you may want to use: Use :meth:`ORMObject.get_connection` to get the
        :class:`transaction <stoqlib.database.runtime.StoqlibTransaction>` in which
        *self* lives and do your modifications in it.
        """

    def on_delete(self):
        """Called when *self* is about to be updated on the database

        This hook can be overridden on child classes for improved
        functionality.

        A trick you may want to use: Use :meth:`ORMObject.get_connection` to get the
        :class:`transaction <stoqlib.database.runtime.StoqlibTransaction>` in which
        *self* lives and do your modifications in it.

        Do not try to modify *self*, as it was marked as obsolete by
        :class:`stoqlib.database.orm.ORMObject` and it will result in errors.
        """

    def clone(self):
        """Get a persistent copy of an existent object. Remember that we can
        not use copy because this approach will not activate ORMObject
        methods which allow creating persitent objects. We also always
        need a new id for each copied object.
        """
        columns = self.sqlmeta.columnList

        kwargs = {}
        for column in columns:
            # FIXME: Make sure this is cloning correctly
            name = column.name
            if name == 'id' or name == 'identifier':
                continue
            if name.endswith('_id'):
                name = name[:-3]
            kwargs[name] = getattr(self, name)

        klass = type(self)
        return klass(connection=self._connection, **kwargs)

    def check_unique_value_exists(self, attribute, value,
                                  case_sensitive=True):
        """Returns True if we already have the given attribute
        and value in the database, but ignoring myself.

        :param attribute: the attribute that should be unique
        :param value: value that we will check if exists in the database
        :param case_sensitive: If the checking should be case sensitive or
            not.
        """
        if not value:
            return False

        if case_sensitive:
            query = getattr(self.q, attribute) == value
        else:
            query = ILIKE(getattr(self.q, attribute), value)

        # Remove ourself from the results.
        if hasattr(self, 'id'):
            query = AND(query, self.q.id != self.id)
        return self.select(query, connection=self.get_connection()).count() > 0

    @property
    def user(self):
        return self.te_modified.user

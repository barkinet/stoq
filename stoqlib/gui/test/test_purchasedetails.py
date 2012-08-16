# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
import unittest

import mock
from stoqlib.gui.uitestutils import GUITest
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.reporting.purchase import PurchaseOrderReport, PurchaseQuoteReport


class TestPurchaseDetailsDialog(GUITest):

    def testShow(self):
        date = datetime.date(2012, 1, 1)
        supplier = self.create_supplier()

        # New purchase
        order = self.create_purchase_order()
        order.identifier = 123
        order.supplier = supplier
        order.open_date = date

        # Product
        self.create_purchase_order_item(order)

        # Payments
        payment = self.add_payments(order, date=date)
        payment.identifier = 999
        payment.group.payer = supplier.person

        dialog = PurchaseDetailsDialog(self.trans, order)
        self.check_editor(dialog, 'dialog-purchase-details')

    @mock.patch('stoqlib.gui.dialogs.purchasedetails.SpreadSheetExporter.export')
    def testExportSpreadSheet(self, export):
        order = self.create_purchase_order()
        dialog = PurchaseDetailsDialog(self.trans, order)

        self.assertSensitive(dialog, ['export_csv'])
        dialog.export_csv.clicked()
        export.assert_called_once()

    @mock.patch('stoqlib.gui.dialogs.purchasedetails.print_report')
    def testPrintDetails(self, print_report):
        order = self.create_purchase_order()
        dialog = PurchaseDetailsDialog(self.trans, order)
        self.assertSensitive(dialog, ['print_button'])

        # Quote order
        dialog.print_button.clicked()
        print_report.assert_called_once_with(PurchaseQuoteReport, order)

        # Normal order
        print_report.reset_mock()
        order.status = PurchaseOrder.ORDER_PENDING
        dialog.print_button.clicked()
        print_report.assert_called_once_with(PurchaseOrderReport, order)


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()

from odoo import fields, models
import re
import pytz
from datetime import datetime


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type = fields.Selection(tracking=False)

    def write(self, vals):
        now = datetime.now()
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or "Asia/Phnom_Penh")
        date_today = pytz.utc.localize(now).astimezone(user_tz)
        current_time = date_today.strftime("%H:%M:%S")

        display_msg = """Edited at
                        """ + current_time + """
                        <ul>
                    """

        no_edited_field = 0

        for field in vals:
            if field == 'type':
                if self[field] != vals[field]:
                    display_msg += """
                                    <li>
                                        """ + self._fields[field].string + """:
                                        """ + str(dict(self._fields[field].selection).get(self.type)) + """
                                        <span style = "font-size:25px;">&#8594;</span>
                                        """ + str(dict(self._fields[field].selection).get(vals["type"])) + """
                                    </li>
                                    """
                    no_edited_field += 1

            elif field in ['categ_id', 'company_id', 'pos_categ_id', 'responsible_id',
                           'property_stock_inventory', 'property_stock_production', 'property_account_income_id',
                           'property_account_expense_id', 'asset_category_id', 'property_account_creditor_price_difference']:
                model_name = re.sub(r'\([^)]*\)', '', str(self[field]))
                if self[field]['name'] != self.env[model_name].browse(vals[field])['name']:
                    display_msg += """
                                    <li>
                                        """ + self._fields[field].string + """:
                                        """ + str(self[field]['name']) + """
                                        <span style = "font-size:25px;">&#8594;</span>
                                        """ + str(self.env[model_name].browse(vals[field])['name']) + """
                                    </li>
                                    """
                    no_edited_field += 1

            elif field == 'attribute_line_ids':
                attribute_line_messages = []
                for record in vals[field]:
                    if record[0] == 0:
                        values = []
                        for value_id in record[2]['value_ids'][0][2]:
                            values.append(self.env['product.attribute.value'].browse(value_id)['name'])
                        attribute_line_messages.append("""
                                        <li>Added New Attribute
                                            """ + self.env['product.attribute'].browse(record[2]['attribute_id'])['name'] + """: Values
                                            """ + str(values) + """
                                        </li>
                                        """)
                    elif record[0] == 1:
                        default_values = []
                        for value in self.env['product.template.attribute.line'].browse(record[1])['value_ids']:
                            default_values.append(value['name'])

                        edited_values = []
                        for value_id in record[2]['value_ids'][0][2]:
                            edited_values.append(self.env['product.attribute.value'].browse(value_id)['name'])
                        if str(default_values) == str(edited_values):
                            continue
                        attribute_line_messages.append("""
                                       <li>Edited Attribute
                                           """ + self.env['product.template.attribute.line'].browse(record[1])['attribute_id']["name"] + """: Values
                                           """ + str(default_values) + """
                                           <span style = "font-size:25px;">&#8594;</span>
                                           """ + str(edited_values) + """
                                       </li>
                                       """)
                    elif record[0] == 2:
                        values = []
                        for value in self.env['product.template.attribute.line'].browse(record[1])['value_ids']:
                            values.append(value['name'])
                        attribute_line_messages.append("""
                                        <li>Deleted Attribute
                                            """ + self.env['product.template.attribute.line'].browse(record[1])['attribute_id']['name'] + """: Values
                                            """ + str(values) + """
                                        </li>
                                        """)
                if len(attribute_line_messages) > 0:
                    no_edited_field += 1

                    display_msg += """
                                    <li>
                                        """ + self._fields[field].string + """:
                                        <ul>
                                    """

                    for message in attribute_line_messages:
                        display_msg += message

                    display_msg += """
                                        </ul>
                                    </li>
                                    """

            elif field == 'seller_ids':
                seller_message = []

                for record in vals[field]:
                    if record[0] == 0:
                        seller_message.append("""
                                        <li>Added New Vendor:
                                            """ + self.env['res.partner'].browse(record[2]['name'])['name'] + """
                                        </li>
                                        """)
                    if record[0] == 1:
                        edited_messages = []
                        edited_message = ''

                        for vendor_field in record[2]:
                            if vendor_field == 'name':
                                if self.env['product.supplierinfo'].browse(record[1])["name"]["name"] != self.env['res.partner'].browse(record[2][vendor_field])["name"]:
                                    edited_messages.append("""
                                                            <li>Vendor:
                                                                """ + self.env['product.supplierinfo'].browse(record[1])["name"]["name"] + """
                                                                <span style = "font-size:25px;">&#8594;</span>
                                                                """ + self.env['res.partner'].browse(record[2][vendor_field])["name"] + """
                                                            </li>
                                                            """)
                            elif vendor_field == 'company_id':
                                if self[field]["company_id"]["name"] != self.env['res.company'].browse(record[2][vendor_field])["name"]:
                                    edited_messages.append("""
                                                            <li>Company:
                                                                """ + self[field]["company_id"]["name"] + """
                                                                <span style = "font-size:25px;">&#8594;</span>
                                                                """ + self.env['res.company'].browse(record[2][vendor_field])["name"] + """
                                                            </li>
                                                            """)
                            elif vendor_field == 'product_id':
                                if str(self[field]["product_id"]["name"]) != str(self.env['product.product'].browse(record[2][vendor_field])["name"]):
                                    edited_messages.append("""
                                                    <li>Product Variant:
                                                        """ + str(self[field]["product_id"]["name"]) + """
                                                        <span style = "font-size:25px;">&#8594;</span>
                                                        """ + str(self.env['product.product'].browse(record[2][vendor_field])["name"]) + """
                                                    </li>
                                                    """)
                            else:
                                if str(self.env['product.supplierinfo'].browse(record[1])[vendor_field]) != str(record[2][vendor_field]):
                                    edited_messages.append("""
                                                            <li>
                                                                """ + self.env['product.supplierinfo']._fields[vendor_field].string + """:
                                                                """ + str(self.env['product.supplierinfo'].browse(record[1])[vendor_field]) + """
                                                                <span style = "font-size:25px;">&#8594;</span>
                                                                """ + str(record[2][vendor_field]) + """
                                                            </li>
                                                            """)
                        if len(edited_messages) > 0:
                            edited_message += """
                                            <li>Edited Vendor:
                                                """ + self.env['product.supplierinfo'].browse(record[1])["name"]["name"] + """
                                                <ul>
                                            """
                            for message in edited_messages:
                                edited_message += message

                            edited_message += """
                                                </ul>
                                            </li>
                                            """
                            seller_message.append(edited_message)

                    elif record[0] == 2:
                        seller_message.append("""
                                                <li>Deleted Vendor:
                                                    """ + self.env['product.supplierinfo'].browse(record[1])['name']['name'] + """
                                                </li>
                                                """)
                if len(seller_message) > 0:
                    display_msg += """
                                    <li>
                                        """ + self._fields[field].string + """:
                                        <ul>
                                    """
                    for message in seller_message:
                        display_msg += message
                    display_msg += """
                                        </ul>
                                    </li>
                                    """
                    no_edited_field += 1

            elif field in ['taxes_id', 'supplier_taxes_id', 'route_ids']:
                model_name = re.sub(r'\([^)]*\)', '', str(self[field]))
                default_values = []
                edited_values = []
                for record in self[field]:
                    default_values.append(record["name"])

                for record in self.env[model_name].browse(vals[field][0][2]):
                    edited_values.append(record["name"])
                display_msg += """
                                <li>
                                    """ + self._fields[field].string + """:
                                    """ + str(default_values) + """
                                    <span style = "font-size:25px;">&#8594;</span>
                                    """ + str(edited_values) + """
                                </li>
                                """
                no_edited_field += 1

            else:
                if str(self[field]) != str(vals[field]):
                    display_msg += """
                                    <li>
                                        """ + self._fields[field].string + """:
                                        """ + str(self[field]) + """
                                        <span style = "font-size:25px;">&#8594;</span>
                                        """ + str(vals[field]) + """
                                    </li>
                                    """
                    no_edited_field += 1

        display_msg += "</ul>"

        rtn = super(ProductTemplate, self).write(vals)

        if no_edited_field > 0:
            self.message_post(body=display_msg)

        return rtn


class ProductProduct(models.Model):
    _inherit = "product.product"

    def write(self, vals):
        if 'standard_price' in vals:
            now = datetime.now()
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or "Asia/Phnom_Penh")
            date_today = pytz.utc.localize(now).astimezone(user_tz)
            current_time = date_today.strftime("%H:%M:%S")

            display_msg = """Edited at
                               """ + current_time + """
                               <ul>
                                    <li>
                                        """ + self._fields['standard_price'].string + """:
                                        """ + str(self['standard_price']) + """
                                        <span style = "font-size:25px;">&#8594;</span>
                                        """ + str(vals['standard_price']) + """
                                    </li>
                                </ul>
                            """
            self.env['product.template'].browse(self.env.context.get('active_id')).message_post(body=display_msg)

        rtn = super(ProductProduct, self).write(vals)
        return rtn

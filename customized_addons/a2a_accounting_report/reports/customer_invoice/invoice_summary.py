from odoo import models
import json


class InvoiceSummary(models.AbstractModel):
  _inherit = "account.move"

  product_group = {}
  product_name = ''
  product_category = ''
  kh_name = ''

  def _get_item(self, line):
    # reset Product's name and Category, Example Bell tent King 001 -> Bell tent
    # For commercial package and tax package only
    self.kh_name = ''
    self.product_name = line.name
    self.product_category = line.product_id.categ_id.name
    categ = line.product_id.categ_id

    if line.product_id.name == "Sound System":
      self.product_category = 'Activity'

    elif line.product_id.is_alcohol_or_cigarette:
      self.product_category = 'Public Lighting'

    if line.product_id.categ_id.product_kh_name:
      self.kh_name = line.product_id.categ_id.product_kh_name

    # Loop back to check if the category is the child of Accommodation
    while categ.parent_id.name:
      if categ.parent_id.name == "Accommodation":
        self.product_name = categ.name
        self.product_category = categ.parent_id.name
        if categ.product_kh_name:
          self.kh_name = categ.product_kh_name
        break

      categ = categ.parent_id
    if line.discount_customize != 0:
      self.product_name += f" Disc\nDiscount: {line.discount_customize}%"
    return line

  def _get_product_group(self):
    # Combine product of the same category from invoice_line_ids into dictionary
    self.product_group = {}
    for line in self.invoice_line_ids:
      line = self._get_item(line)
      if self.product_name not in self.product_group:
        self.product_group[self.product_name] = {
          'name': self.product_name,
          'kh_name': self.kh_name,
          'category': self.product_category,
          'qty': line.quantity,
          'unit': line.product_uom_id.name if line.product_uom_id.name else "",
          'discount': line.discount_customize,
          'price_unit': line.price_unit,
          'amount': line.subtotal_customize,
          'tax': line.tax_ids,
        }
      else:
        self.product_group[self.product_name]['qty'] += line.quantity
        self.product_group[self.product_name]['amount'] += line.subtotal_customize

    return self.product_group

  def get_invoice_summary(self):
    if not len(self.product_group):
      self._get_product_group()
    sorted_product = {
      'main': {},
      'other': []
    }

    tax = {'Accommodation': {'label': 2, 'divisor': 1.02},
           'Activity': {'label': 10, 'divisor': 1.1},
           'Public Lighting': {'label': 3, 'divisor': 1.03}}

    # Loop and sort product into Tax-categories and untax-categories
    for line in self.product_group.values():
      product = line['name']
      sub_total = line['amount']
      category = line['category']
      if line['kh_name'] != '':
        line['kh_name'] += ' / '
      if category in tax:
        if category not in sorted_product['main']:
          sorted_product['main'][category] = {
            'list_item': [{'name': product, 'total_price': sub_total, 'kh_name': line['kh_name']}],
            'category': category,
            'total_amount_include_tax': sub_total,
            'label': {}
          }
        else:
          sorted_product['main'][category]['list_item'].append(
            {'name': product, 'total_price': sub_total, 'kh_name': line['kh_name']})
          sorted_product['main'][category]['total_amount_include_tax'] += sub_total

      else:
        sorted_product['other'].append({'name': product, 'total_price': sub_total})

    # Calculate total price, and set the label of the main Category(tax)
    for key, value in zip(sorted_product['main'], sorted_product['main'].values()):
      category = "Specific" if key == "Activity" else key
      tax_name = f"{category} Tax"
      PLT = ''
      total_amount = round(value['total_amount_include_tax'] / tax[key]['divisor'], 2)
      total_tax = round(value['total_amount_include_tax'] - total_amount, 2)
      total_amount_str = total_amount

      if key == 'Public Lighting':
        tax_name = "PLT"
        PLT = " (PLT)"
        total_amount_str = f"({total_amount} x 20%)"
        total_tax = round(total_amount * 0.006, 2)

      value['label'] = {
        'total_amount': {'string': f'Total {category} amount', 'value': total_amount},
        'total_tax': {'string': f'{category} Tax{PLT}: ({total_amount_str} x {tax[key]["label"]}%)',
                      'value': total_tax},
        'total_include_tax': {'string': "Total " + " / ".join(
          [item['name'].split('\n')[0] for item in value['list_item']]) + f" include {tax_name} :",
                              'value': value['total_amount_include_tax']}
      }
    return sorted_product

  def get_payment_data(self, payments_widget):
    if payments_widget == 'false':
      return
    content = json.loads(payments_widget)

    data = []
    for item in content['content']:
      date_reformat = item['date'][-2:] + "/" + item['date'][5:7] + "/" + item['date'][0:4]
      data.append({
        'journal': item['journal_name'],
        'date': date_reformat,
        'amount': round(item['amount'], 2),
        'remark': item['ref']
      })

    return data

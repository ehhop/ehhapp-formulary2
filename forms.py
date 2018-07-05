from flask_wtf import FlaskForm
from wtforms import TextField, SelectField, validators, FileField
import re

class DisabledTextField(TextField):
  '''for showing fields in the form a user should not edit'''
  def __call__(self, *args, **kwargs):
    kwargs.setdefault('disabled', True)
    return super(DisabledTextField, self).__call__(*args, **kwargs)

def filter_digits(value):			# remove other characters except for digits
	if value == None:
		return None
	sanitize = re.compile(r'[^\d]+')
	return str(sanitize.sub('', value))

class PersistentMedicationForm(FlaskForm):
	'''for handling updates to a PersistentMedication record'''
	pricetable_id = DisabledTextField("Pricetable ID")
	name = TextField('Formal name', 
	                 validators=[validators.Length(max=255)])
	common_name = TextField('Common name', 
	                 validators=[validators.Length(max=255)])
	dosage = TextField('Dosage', 
	                 validators=[validators.Length(max=100)])
	admin = TextField('Given by', 
	                 validators=[validators.Length(max=100)])
	cui = TextField('RxCUI identifier', 
	                 validators=[validators.Length(max=10)],
	                 filters=[lambda x: x, filter_digits])
	prescribable = SelectField('Prescribable', 
	                           choices=[(1, "Yes"), 
	                           (0, "No")], coerce=bool)
	category_name = TextField('Category name')

class CategoryForm(FlaskForm):
	name = TextField("Category name",validators=[validators.Length(min=2,max=255)])
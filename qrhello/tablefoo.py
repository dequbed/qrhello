from flask_table import Table, Col

# Declare your table
class ItemTable(Table):
    name = Col('Name')
    description = Col('Description')


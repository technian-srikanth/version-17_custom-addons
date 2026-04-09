{
    'name': 'EMPLOYEE TO USER',
    'version': '17.0',
    'depends': ['base', 'hr', 'hr_holidays', 'hr_attendance', 'hr_recruitment'],
    'data': [
        'security/ir.model.access.csv',
        'views/view_employee.xml',
        'wizards/view_wizard_user.xml',
    ]
}

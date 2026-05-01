{
    'name': 'Hr Interview',
    'version': '17.0.0.0.1',
    'depends': ['base', 'hr_recruitment', ],
    'data': [
        'security/ir.model.access.csv',
        'views/view_hr_interview.xml',
        'views/view_hr_applicant.xml',
        'data/ir_cron.xml',
        'views/menuitems.xml',
    ]
}

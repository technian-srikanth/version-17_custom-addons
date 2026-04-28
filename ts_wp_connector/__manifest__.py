{
    "name": "WP Connector",
    "version": "17.0",
    "author": "Nians",
    "depends": ["base", "hr", "website", "hr_recruitment", "payment", "website_blog", ],
    "data":
        [
            'security/ir.model.access.csv',
            'views/hr_job_view.xml',
            "views/hr_job_department.xml",
            "views/view_hr_work_location.xml",
            "data/ir_cron.xml",
        ],
}

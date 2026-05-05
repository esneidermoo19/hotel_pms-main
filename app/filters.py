from flask import Flask

def register_filters(app: Flask):
    @app.template_filter('currency')
    def currency_filter(value):
        """Format number as Colombian pesos"""
        if value is None:
            return "0"
        return "{:,}".format(int(value))
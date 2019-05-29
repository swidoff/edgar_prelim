import os
from functools import wraps

from flask import Flask, url_for
import pandas as pd
from sqlalchemy import text
from werkzeug.contrib.cache import SimpleCache


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    cache = SimpleCache()

    def cached(timeout):
        def decorate(func):
            @wraps(func)
            def wrapper():
                key = func.__name__
                rv = cache.get(key)
                if rv is None:
                    rv = func()
                    cache.set(key, rv, timeout=timeout)
                return rv

            return wrapper

        return decorate

    @app.route('/<cik>')
    def cik_data(cik):
        from edgar_db import prelim_engine
        data_df = pd.read_sql(text(
            "select cik, filing_date, fiscal_period, item, item_value from prelim_statement where cik = :cik"
        ).bindparams(cik=cik), prelim_engine)

        unstacked_df = data_df.set_index(['cik', 'filing_date', 'fiscal_period', 'item']).unstack()
        unstacked_df.columns = unstacked_df.columns.droplevel(0)
        return unstacked_df.reset_index().to_json(orient='records')

    @app.route('/companies')
    @cached(timeout=0)
    def companies():
        from edgar_db import prelim_engine
        cik_df = pd.read_sql(
            """
            select c.cik, c.sic, c.sic_description, c.company_name, max(s.filing_date) as last_filing_date 
            from cik c 
            join prelim_statement s on (
                c.cik = s.cik
            )
            group by c.cik, c.sic, c.sic_description, c.company_name
            order by last_filing_date desc, c.cik asc
            """, prelim_engine)
        return cik_df.to_json(orient='records')

    return app

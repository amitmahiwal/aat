import os
import os.path
from perspective import Table, PerspectiveManager, PerspectiveTornadoHandler
from tkp_utils.tornado import make_application
from ..persistence import User, APIKey
from ..utils import generate_cookie_secret


def serverApplication(trading_engine,
                      port='8080',
                      sessionmaker=None,
                      extra_handlers=None,
                      custom_settings=None,
                      debug=True,
                      cookie_secret=None,
                      basepath='/',
                      apipath='/api/v1',
                      wspath='ws:0.0.0.0:{}/'):
    root = custom_settings.pop("assets_path", os.path.join(os.path.dirname(__file__), 'assets'))
    static = custom_settings.pop("static_path", os.path.join(root, 'static'))

    # Perspectives
    manager = PerspectiveManager()

    # Accounts
    accounts = Table([a.to_dict(True) for ex in trading_engine.exchanges.values() for a in ex.accounts().values()])
    manager.host_table("accounts", accounts)

    cookie_secret = generate_cookie_secret() if not cookie_secret else cookie_secret

    handlers = extra_handlers + [
        (r"/api/v1/ws", PerspectiveTornadoHandler, {"manager": manager, "check_origin": True}),
    ]

    context = {}

    return make_application(
        port=port,
        debug=debug,
        assets_dir=root,
        static_dir=static,
        cookie_secret=cookie_secret,
        basepath=basepath,
        apipath=apipath,
        wspath=wspath,
        sqlalchemy_sessionmaker=sessionmaker,
        UserSQLClass=User,
        APIKeySQLClass=APIKey,
        user_id_field='id',
        apikey_id_field='id',
        user_apikeys_field='apikeys',
        apikey_user_field='user',
        user_admin_field='admin',
        user_admin_value=True,
        extra_handlers=handlers,
        extra_context=context,
    )

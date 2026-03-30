try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    # The dependency is optional until the project switches to MySQL.
    pass

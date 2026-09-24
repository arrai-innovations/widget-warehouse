# Deliberately empty. serve.py passes this file to gunicorn so that it does not load
# server/gunicorn.conf.py, which a developer may have configured for TLS locally. The
# end-to-end stack serves plain HTTP on loopback.

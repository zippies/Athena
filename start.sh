#! /bin/sh
python manager.py dbinit
#export C_FORCE_ROOT=true
#export OAUTHLIB_INSECURE_TRANSPORT=true
#nohup python -m celery -A tasks beat --loglevel=info &
#nohup python -m celery -A tasks worker --loglevel=info &
gunicorn -c config.py manager:app --log-level=info

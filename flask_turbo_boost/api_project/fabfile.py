# coding: utf-8
from fabric.api import run, env, cd, prefix, shell_env, local
from config import load_config

config = load_config()
host_string = config.HOST_STRING


def deploy():
    env.host_string = config.HOST_STRING
    with cd('/var/www/testupversion'):
        with shell_env(MODE='PRODUCTION'):
            run('git reset --hard HEAD')
            run('git pull')
            run('npm install')
            run('gulp')
            with prefix('source venv/bin/activate'):
                run('pip install -r requirements.txt')
                run('flask db upgrade')
            run('supervisorctl restart testupversion')


def restart():
    env.host_string = config.HOST_STRING
    run('supervisorctl restart testupversion')

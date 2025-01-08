from environs import Env

env = Env()
env.read_env()
TOKEN = env('BOT_TOKEN')
PAY_TOKEN = env('BOT_PAY_TOKEN')
ADMIN_IDS = env('BOT_ADMIN_IDS')
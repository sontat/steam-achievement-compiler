import os
from flask import Flask, jsonify, request

from exceptions import ProfileNotFoundException
from steam import SteamProxy


exporting_threads = {}
app = Flask(__name__)
VALID_INTERVALS = ("1", "10", "100")


def make_error(error_text):
    response = jsonify({"error": error_text})
    response.status_code = 400
    return response


@app.route('/steam')
def index():
    steam_id = request.args.get('steam_id')
    if not steam_id:
        return make_error("Please enter a Steam ID/username")
    req_interval = request.args.get('interval')
    interval = int(req_interval) if req_interval in VALID_INTERVALS else 10

    try:
        proxy = SteamProxy(steam_id, interval)
    except ProfileNotFoundException:
        return make_error("Could not locate Steam profile from the given input")
    key = os.urandom(8).hex()
    exporting_threads[key] = proxy
    exporting_threads[key].start()

    response = jsonify({"task_id": key})
    return response


@app.route('/steam/progress/<string:thread_id>')
def progress(thread_id):
    if thread_id not in exporting_threads:
        return make_error("Invalid task ID")
    thread = exporting_threads[thread_id]
    if isinstance(thread.exception, ProfileNotFoundException):
        return make_error("Cannot list games, profile is private")
    response = jsonify({
        "steam_id": thread.steam_id,
        "done": thread.is_done,
        "progress": round(thread.get_progress(), 2),
        "achievements": thread.achievements
    })
    return response


if __name__ == '__main__':
    app.run()

"""REST API for generate Image."""

import json
import os
from flask import Flask, jsonify, request, make_response
import ops

PORT = int(os.environ['PORT'])
DEBUG = os.environ['DEBUG'].lower() == 'true'
app = Flask('pdf creator')


@app.route('/api/v1/image/', methods=['GET'])
def image():
    try:
        size = int(request.args.get('size'))
        size_all = int(request.args.get('size_all'))
        num_child = int(request.args.get('num_child'))
    except Exception as e:
        return (jsonify({'error': "parameter error", 'code': 400, 'detail':str(e)}), 400)

    response = make_response()
    response.data = ops.get(size, size_all, num_child)
    response.headers[
      'Content-Disposition'] = 'attachment; filename=image.jpg'
    response.mimetype = 'image/jpeg'
    return response


@app.errorhandler(404)
def api_not_found_error(error):
    """General 404 error."""
    return (jsonify({'error': "api not found", 'code': 404}), 404)


@app.errorhandler(405)
def method_not_allowed_error(error):
    """General 405 error."""
    return (jsonify({'error': 'method not allowed', 'code': 405}), 405)


@app.errorhandler(500)
def internal_server_error(error):
    """General 500 error."""
    return (jsonify({'error': 'server internal error', 'code': 500}), 500)


app.run(debug=DEBUG, host='0.0.0.0', port=PORT)

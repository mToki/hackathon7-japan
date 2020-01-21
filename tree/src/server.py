"""REST API for generate PDF."""

import json
import os
from flask import Flask, jsonify, request, make_response
import ops

PORT = int(os.environ['PORT'])
DEBUG = os.environ['DEBUG'].lower() == 'true'
TG = ops.TreeGenerator()
app = Flask('pdf creator')

@app.route('/api/v1/tree/', methods=['GET', 'POST'])
def tree():
    def get():
        return (jsonify(TG.get_tree()), 200)

    def post():
        (success, _) = TG.create_tree()
        if success:
            return (jsonify({}), 200)
        else:
            return (jsonify({'error':'failed to start building tree', 'code': 400}), 400)

    fdict = {'GET':get, 'POST':post}
    return fdict[request.method]()

@app.route('/api/v1/tree/vm/<vm_uuid>', methods=['GET'])
def tree_vm(vm_uuid):
    (success, chain) = TG.get_vm_vdisk_chains(vm_uuid)
    if success:
        return (jsonify(chain), 200)
    else:
        return (jsonify({}), 400)

@app.route('/api/v1/tree/pd/<pd_name>', methods=['GET'])
def tree_pd(pd_name):
    (success, pd_chain) = TG.get_pd_vdisk_chains(pd_name)
    if success:
        return (jsonify(pd_chain), 200)
    else:
        return (jsonify({}), 400)
        
@app.route('/api/v1/tree/vdisks/', methods=['GET', 'PUT'])
def vdisks():
    def get():
        return (jsonify(TG.vdisk_list), 200)

    def put():
        try:
            body = request.get_data().decode().strip()
            d = json.loads(body)
        except Exception:
            return (jsonify({'error': "json load fail", 'code': 400}), 400)
        TG.set_vdisks(d)
        return (jsonify({}), 200)

    fdict = {'GET':get, 'PUT':put}
    return fdict[request.method]()


@app.route('/api/v1/tree/stats/', methods=['GET', 'PUT'])
def stats():
    def get():
        return (jsonify(TG.stats_list), 200)

    def put():
        try:
            body = request.get_data().decode().strip()
            d = json.loads(body)
        except Exception:
            return (jsonify({'error': "json load fail", 'code': 400}), 400)
        TG.set_stats(d)
        return (jsonify({}), 200)

    fdict = {'GET':get, 'PUT':put}
    return fdict[request.method]()


@app.route('/api/v1/tree/vms/', methods=['GET', 'PUT'])
def vms():
    def get():
        return (jsonify(TG.vm_list), 200)

    def put():
        try:
            body = request.get_data().decode().strip()
            d = json.loads(body)
        except Exception:
            return (jsonify({'error': "json load fail", 'code': 400}), 400)
        TG.set_vms(d)
        return (jsonify({}), 200)

    fdict = {'GET':get, 'PUT':put}
    return fdict[request.method]()


@app.route('/api/v1/tree/vms/<vm_uuid>', methods=['GET'])
def vm(vm_uuid):
    return ''


@app.route('/api/v1/tree/pds/', methods=['GET', 'PUT'])
def pds():
    def get():
        return (jsonify(TG.pd_list), 200)

    def put():
        try:
            body = request.get_data().decode().strip()
            d = json.loads(body)
        except Exception:
            return (jsonify({'error': "json load fail", 'code': 400}), 400)
        TG.set_pds(d)
        return (jsonify({}), 200)

    fdict = {'GET':get, 'PUT':put}
    return fdict[request.method]()


@app.route('/api/v1/tree/pds/<pd_uuid>', methods=['GET', 'PUT'])
def pd(pd_uuid):
    return ''


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

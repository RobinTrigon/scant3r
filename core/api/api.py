#!/usr/bin/env python3
from flask import Flask,abort,request,jsonify,render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from glob import glob
from importlib import import_module
from yaml import safe_load
from threading import Thread
from core.libs import http
import sys,os

app = Flask(__name__)

class Server:
    def __init__(self,opts):
        conf = safe_load(open('core/api/conf.yaml','r'))
        self.host = conf['host']
        self.port = conf['port']
        self.debug = conf['debug']
        self.opts = opts
        self.output = dict()
        limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=conf['limits']
        )
    def restart(self):
        python = sys.executable
        os.execl(python, python, * sys.argv)
        curdir = os.getcwd()
    def clearme(self):
        self.output = dict()
        return {'Done':True}
    def get_m(self):
        conf = glob('modules/*/api.py')
        al = dict()
        for c,i in enumerate(conf):
            al[c] = i.split('/')[1]
        return al
    def save_output(self,func,scanid,copts):
        v = func.main(copts,http(copts))
        scanid = str(scanid)
        if v:
            self.output[scanid].append(v)
    def index(self):
        return render_template('index.html',args=self.get_m())
    def getit(self):
        cc = {}
        for i,v in self.output.items():
            if self.output[i]:
                if v:
                    c = self.get_m()[int(i)]
                    cc[c] = v
        return jsonify(cc)
    def getme(self,mid):
        try:
            c = []
            for v in self.output[str(mid)]:
                c.append(v)
            return jsonify(c)
        except Exception as e:
            return {'Error':f'Not Found'},404
    def orgparams(self,d):
        v = self.opts.copy()
        for i,o in d.items():
            if o:
                v[i] = o
        return v
    def scanapi(self,scanid):
        req_params = request.get_json(force=True)
        self.url = None
        if 'url' in req_params.keys():
            self.url = req_params['url']
        if self.url:
            try:
                self.output[str(scanid)]
            except:
                self.output[str(scanid)] = list()
            copts = self.orgparams(request.get_json(force=True))
            if scanid in self.get_m().keys():
                try:
                    res = {'Results':[]}
                    try:
                        m = import_module(f'modules.{self.get_m()[scanid]}.api')
                    except Exception as e:
                        return jsonify({'Error':e}),500
                    p1 = Thread(target=self.save_output,args=(m,scanid,copts,))
                    p1.daemon = True
                    p1.start()
                    return {'Start':True}

                except Exception as e:
                    return jsonify({'Error':f'{e}'})
            else:
                return jsonify({'Scanid':'404'})
        else:
            return {'Error':'url paremter is required'},404
    def run(self):
        app.add_url_rule('/', view_func=self.index)
        app.add_url_rule('/scan/<int:scanid>',methods=['POST'],view_func=self.scanapi)
        app.add_url_rule('/scan/',view_func=self.getit)
        app.add_url_rule('/restart',view_func=self.restart)
        app.add_url_rule('/clear',view_func=self.clearme)
        app.add_url_rule('/scan/<int:mid>',view_func=self.getme)
        app.run(host=self.host,port=self.port,debug=self.debug)

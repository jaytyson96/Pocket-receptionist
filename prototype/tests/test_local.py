"""Run from repository root:
python -m unittest discover -s prototype/tests -v
No third-party dependencies and no paid services.
"""
import json, os, sys, tempfile, threading, unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pricing,database,server

EXAMPLE={'service':'driveway','surface':'block_paving','condition':'light','area_m2':'40','biocide':True,'resanding':False}
def sample(): return {'customer_name':'Fictional Client','postcode':'HA2','description':'Fictional driveway test job',
                       'job':EXAMPLE.copy(),'fictional_data_only':True}
class EngineTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(pricing.estimate(EXAMPLE,pricing.DEFAULT_RATES)['total_pence'],13500)
    def test_owner_approval_required(self):
        self.assertEqual(pricing.estimate(EXAMPLE,pricing.DEFAULT_RATES)['status'],'draft_requires_owner_review')
    def test_resanding_restricted(self):
        with self.assertRaises(pricing.InputError):
            pricing.estimate({**EXAMPLE,'service':'patio','surface':'patio_slabs','resanding':True},pricing.DEFAULT_RATES)
    def test_invalid_area(self):
        for area in ['-1','NaN','Infinity','0','2001','1.00001']:
            with self.subTest(area=area),self.assertRaises(pricing.InputError):
                pricing.estimate({**EXAMPLE,'area_m2':area},pricing.DEFAULT_RATES)
    def test_vat(self):
        r={**pricing.DEFAULT_RATES,'vat_enabled':True}
        e=pricing.estimate(EXAMPLE,r)
        self.assertEqual(e['subtotal_pence'],13500)
        self.assertEqual(e['vat_pence'],2700)
        self.assertEqual(e['total_pence'],16200)
    def test_price_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Path(directory)/'test.sqlite'
            database.init(db)
            one=database.add(db,pricing.validate_enquiry(sample()),pricing.estimate(EXAMPLE,database.rates(db)))
            r=database.rates(db);r['per_m2']='3.00'
            database.change_rates(db,r)
            self.assertEqual(one['estimate']['total_pence'],13500)
            self.assertEqual(database.get(db,one['id'])['estimate']['total_pence'],13500)

class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.srv=server.make_server(0,Path(cls.tmp.name)/'api.sqlite')
        cls.thread=threading.Thread(target=cls.srv.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.srv.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown();cls.srv.server_close();cls.thread.join(timeout=3);cls.tmp.cleanup()
    def request(self,method,path,body=None,origin=None):
        data=json.dumps(body).encode() if body is not None else None
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        req=Request(self.base+path,data=data,headers=headers,method=method)
        try:
            with urlopen(req,timeout=3) as res:return res.status,json.load(res)
        except HTTPError as e:return e.code,json.load(e)
    def test_health_and_page(self):
        code,payload=self.request('GET','/api/health')
        self.assertEqual(code,200)
        self.assertFalse(payload['ai'])
        req=Request(self.base+'/')
        with urlopen(req,timeout=3) as res:
            self.assertEqual(res.status,200)
            self.assertIn(b'Smart Quote V2',res.read())
    def test_save_review_and_double_review_blocked(self):
        code,data=self.request('POST','/api/enquiries',sample())
        self.assertEqual(code,201,data)
        row=data['enquiry']
        self.assertEqual(row['status'],'awaiting_owner')
        code,_=self.request('POST',f"/api/enquiries/{row['id']}/approve",{'approved_total_pence':14000,'note':'Reviewed'})
        self.assertEqual(code,200)
        code,_=self.request('POST',f"/api/enquiries/{row['id']}/approve",{'approved_total_pence':14000,'note':'Repeat'})
        self.assertEqual(code,409)
    def test_reject_real_data(self):
        sample_payload=sample();sample_payload['fictional_data_only']=False
        code,_=self.request('POST','/api/enquiries',sample_payload)
        self.assertEqual(code,400)
    def test_bad_origin(self):
        code,_=self.request('POST','/api/estimate',EXAMPLE,origin='https://example.com')
        self.assertEqual(code,403)
    def test_traversal_blocked(self):
        code,_=self.request('GET','/../pricing.py')
        self.assertEqual(code,404)

if __name__=='__main__':unittest.main()

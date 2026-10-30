#!/usr/bin/env python3
"""Local portfolio rebalancing website and read-only JSON API."""
import json, os, sqlite3
import hmac
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import auth_store

ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('PORTFOLIO_DB',ROOT/'data'/'portfolio.db'))
TABLES=('InvestorProfile','Portfolio','Instrument','Holding','MarketPrice','TargetAllocation','FeeSchedule','Constraint','RebalanceProposal','Trade','PostTradeAllocation')
def query(sql,args=()):
    if not DB.exists(): return []
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    try: return [dict(r) for r in c.execute(sql,args)]
    finally: c.close()
def first(sql,args=()):
    rows=query(sql,args); return rows[0] if rows else {}
def dataset_info():
    result={'counts':{t:first(f'SELECT COUNT(*) AS n FROM "{t}"').get('n',0) for t in TABLES},'manifest':{},'validation':{},'ground_truth':[],'edge_cases':[]}
    for file,key in [('manifest.json','manifest'),('validation_summary.json','validation'),('ground_truth.json','ground_truth'),('edge_cases.json','edge_cases')]:
        path=DB.parent/file
        if path.exists():
            try: result[key]=json.loads(path.read_text(encoding='utf-8'))
            except (OSError,ValueError): pass
    return result
class Handler(BaseHTTPRequestHandler):
    def send(self, body, kind='application/json; charset=utf-8', code=200, headers=None):
        data=body.encode() if isinstance(body,str) else body; self.send_response(code); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store')
        for name,value in {'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"}.items(): self.send_header(name,value)
        for name,value in (headers or {}).items(): self.send_header(name,value)
        self.end_headers(); self.wfile.write(data)
    def json(self,value,code=200,headers=None): return self.send(json.dumps(value,ensure_ascii=False),code=code,headers=headers)
    def cookie_token(self):
        for item in self.headers.get('Cookie','').split(';'):
            k,sep,v=item.strip().partition('=')
            if sep and k=='nivesh_session': return v
        return None
    def session(self): return auth_store.get_session(self.cookie_token())
    def same_origin(self):
        origin=self.headers.get('Origin'); host=self.headers.get('Host','')
        return bool(origin and urlparse(origin).netloc.lower()==host.lower())
    def payload(self):
        if self.headers.get_content_type()!='application/json': raise ValueError('Send the form as JSON.')
        n=int(self.headers.get('Content-Length','0'))
        if n<1 or n>20_000: raise ValueError('Request is empty or too large.')
        value=json.loads(self.rfile.read(n))
        if not isinstance(value,dict): raise ValueError('Invalid request.')
        return value
    def set_session_cookie(self,token):
        secure='; Secure' if os.environ.get('AUTH_COOKIE_SECURE')=='1' else ''
        return {'Set-Cookie':f'nivesh_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={auth_store.SESSION_SECONDS}{secure}'}
    def clear_session_cookie(self):
        secure='; Secure' if os.environ.get('AUTH_COOKIE_SECURE')=='1' else ''
        return {'Set-Cookie':f'nivesh_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0{secure}'}
    def auth_routes(self,path):
        if path=='/api/auth/me' and self.command=='GET':
            s=self.session()
            if not s:return self.json({'authenticated':False},401)
            plan,updated=auth_store.read_plan(s['user_id'])
            return self.json({'authenticated':True,'user':{'email':s['email'],'display_name':s['display_name']},'csrf_token':s['csrf_token'],'plan':plan,'updated_at':updated})
        if path not in ('/api/auth/register','/api/auth/login','/api/auth/logout','/api/my-plan'): return False
        if self.command=='GET' and path=='/api/my-plan':
            s=self.session()
            if not s:return self.json({'error':'Please sign in.'},401)
            plan,updated=auth_store.read_plan(s['user_id']);return self.json({'plan':plan,'updated_at':updated})
        if self.command!='POST':return self.json({'error':'Method not allowed.'},405)
        if not self.same_origin():return self.json({'error':'Request origin could not be verified. Reload the page and try again.'},403)
        try: body=self.payload()
        except (ValueError,TypeError,json.JSONDecodeError) as exc:return self.json({'error':str(exc) or 'Invalid request.'},400)
        if path in ('/api/auth/register','/api/auth/login'):
            try:
                if path.endswith('register'):
                    email=body.get('email',''); password=body.get('password',''); user=auth_store.create_user(email if isinstance(email,str) else '',str(body.get('display_name','')),password if isinstance(password,str) else '')
                else:
                    email=body.get('email','');password=body.get('password','')
                    if not isinstance(email,str) or not isinstance(password,str) or len(password)>128:raise ValueError('Invalid email or password.')
                    user=auth_store.authenticate(email,password)
                    if not user:return self.json({'error':'Email or password is incorrect.'},401)
            except ValueError as exc:return self.json({'error':str(exc)},400)
            token,csrf=auth_store.create_session(user['user_id']);plan,updated=auth_store.read_plan(user['user_id'])
            return self.json({'authenticated':True,'user':{'email':user['email'],'display_name':user['display_name']},'csrf_token':csrf,'plan':plan,'updated_at':updated},headers=self.set_session_cookie(token))
        s=self.session()
        if not s:return self.json({'error':'Please sign in to save your plan.'},401)
        if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),s['csrf_token']):return self.json({'error':'Security token expired. Reload and try again.'},403)
        if path=='/api/auth/logout':
            auth_store.revoke_session(self.cookie_token());return self.json({'ok':True},headers=self.clear_session_cookie())
        plan=body.get('plan')
        if not isinstance(plan,dict) or set(plan)-{'name','portfolio_value','scenario_value','target_plan','turnover_limit_pct','what_if','current_mix','entered_mix','target_mix','possible_changes','estimated_fees_inr','illustrative_after_mix'}:return self.json({'error':'Plan format is invalid.'},400)
        try: updated=auth_store.save_plan(s['user_id'],plan)
        except (ValueError,TypeError) as exc:return self.json({'error':str(exc)},400)
        return self.json({'ok':True,'updated_at':updated})
    def do_GET(self):
        parsed=urlparse(self.path); path=parsed.path; params=parse_qs(parsed.query)
        if self.auth_routes(path) is not False:return
        if path=='/docs/presentation_guide.md': return self.send((ROOT/'docs'/'presentation_guide.md').read_text(encoding='utf-8'),'text/markdown; charset=utf-8')
        static={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
        if path in static: return self.send((ROOT/'web'/static[path]).read_text(encoding='utf-8'),{'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8'}[path])
        if path=='/api/health': return self.json({'ok':DB.exists(),'database':DB.name})
        if not DB.exists() and path.startswith('/api/'): return self.json({'error':'Dataset not found. Run python generate_data.py first.'},503)
        if path=='/api/summary':
            status_rows=query('SELECT status,COUNT(*) n FROM RebalanceProposal GROUP BY status')
            risk_rows=query('SELECT i.risk_tolerance,COUNT(*) n FROM Portfolio p JOIN InvestorProfile i USING(investor_id) GROUP BY i.risk_tolerance ORDER BY i.risk_tolerance')
            exception_rows=query("SELECT exception_codes FROM RebalanceProposal WHERE exception_codes<>'[]'")
            exception_counts={}
            for row in exception_rows:
                for code in json.loads(row['exception_codes']): exception_counts[code]=exception_counts.get(code,0)+1
            return self.json({'portfolios':first('SELECT COUNT(*) n FROM Portfolio')['n'],'holdings':first('SELECT COUNT(*) n FROM Holding')['n'],'proposals':first('SELECT COUNT(*) n FROM RebalanceProposal')['n'],'review':first("SELECT COUNT(*) n FROM RebalanceProposal WHERE status='REVIEW'")['n'],'blocked':first("SELECT COUNT(*) n FROM Trade WHERE status='BLOCKED'")['n'],'fees':first('SELECT ROUND(SUM(estimated_fees),2) n FROM RebalanceProposal')['n'] or 0,'statuses':{r['status']:r['n'] for r in status_rows},'risk_profiles':risk_rows,'exceptions':exception_counts,'valuation_date':first('SELECT MAX(price_date) d FROM MarketPrice')['d']})
        if path=='/api/portfolios':
            where=[]; args=[]
            if params.get('search'):
                where.append('(p.portfolio_id LIKE ? OR i.display_name LIKE ?)'); term=f"%{params['search'][0]}%"; args.extend([term,term])
            if params.get('risk') and params['risk'][0] in ('Conservative','Balanced','Growth'):
                where.append('i.risk_tolerance=?'); args.append(params['risk'][0])
            if params.get('status') and params['status'][0] in ('READY','REVIEW','ON_TARGET'):
                where.append('b.status=?'); args.append(params['status'][0])
            clause=(' WHERE '+' AND '.join(where)) if where else ''
            total=first(f'SELECT COUNT(*) n FROM Portfolio p JOIN InvestorProfile i USING(investor_id) LEFT JOIN RebalanceProposal b ON b.portfolio_id=p.portfolio_id{clause}',args)['n']
            page=max(1,int(params.get('page',['1'])[0])); limit=min(100,max(1,int(params.get('limit',['20'])[0]))); args.extend([limit,(page-1)*limit])
            rows=query(f'''SELECT p.portfolio_id,i.display_name,i.risk_tolerance,p.base_currency,p.cash_balance,b.proposal_id,b.status,b.total_value,b.estimated_fees,b.exception_codes
              FROM Portfolio p JOIN InvestorProfile i USING(investor_id) LEFT JOIN RebalanceProposal b ON b.portfolio_id=p.portfolio_id{clause} ORDER BY p.portfolio_id LIMIT ? OFFSET ?''',args)
            return self.json({'items':rows,'total':total,'page':page,'limit':limit,'pages':(total+limit-1)//limit})
        if path.startswith('/api/portfolio/'):
            pid=path.rsplit('/',1)[-1]
            head=query('''SELECT p.*,i.display_name,i.risk_tolerance,b.proposal_id,b.status proposal_status,b.total_value,b.estimated_fees,b.exception_codes
              FROM Portfolio p JOIN InvestorProfile i USING(investor_id) LEFT JOIN RebalanceProposal b ON b.portfolio_id=p.portfolio_id WHERE p.portfolio_id=?''',(pid,))
            if not head: return self.json({'error':'Portfolio not found'},404)
            rows=query('''SELECT h.holding_id,h.quantity,h.as_of,i.instrument_id,i.ticker,i.name,i.asset_class,i.currency,i.eligible,
              m.close price,m.price_date,ta.target_pct FROM Holding h JOIN Instrument i USING(instrument_id)
              LEFT JOIN MarketPrice m ON m.instrument_id=i.instrument_id AND m.price_date=(SELECT MAX(price_date) FROM MarketPrice WHERE instrument_id=i.instrument_id)
              LEFT JOIN TargetAllocation ta ON ta.portfolio_id=h.portfolio_id AND ta.asset_class=i.asset_class AND ta.effective_to IS NULL
              WHERE h.portfolio_id=? ORDER BY i.asset_class''',(pid,))
            total=sum((r['quantity']*(r['price'] or 0)) for r in rows) or 1
            for row in rows:
                row['market_value']=round(row['quantity']*(row['price'] or 0),2); row['current_pct']=round(row['market_value']/total*100,2); row['drift_pct']=round(row['current_pct']-(row['target_pct'] or 0),2)
            return self.json({'portfolio':head[0],'holdings':rows})
        if path.startswith('/api/proposal/'):
            pid=path.rsplit('/',1)[-1]; head=query('SELECT * FROM RebalanceProposal WHERE proposal_id=?',(pid,))
            if not head: return self.json({'error':'Proposal not found'},404)
            lines=query('''SELECT t.*,i.ticker,i.name,i.asset_class,h.quantity held_quantity,m.close price,a.target_pct FROM Trade t JOIN Instrument i USING(instrument_id)
              LEFT JOIN Holding h ON h.portfolio_id=t.portfolio_id AND h.instrument_id=t.instrument_id
              LEFT JOIN MarketPrice m ON m.instrument_id=i.instrument_id AND m.price_date=(SELECT MAX(price_date) FROM MarketPrice WHERE instrument_id=i.instrument_id)
              LEFT JOIN TargetAllocation a ON a.portfolio_id=t.portfolio_id AND a.asset_class=i.asset_class AND a.effective_to IS NULL WHERE t.proposal_id=?''',(pid,))
            allocation=query('SELECT * FROM PostTradeAllocation WHERE proposal_id=? ORDER BY asset_class',(pid,))
            return self.json({'proposal':head[0],'trades':lines,'post_trade_allocation':allocation})
        if path=='/api/data': return self.json(dataset_info())
        if path.startswith('/api/export/'):
            name=path.rsplit('/',1)[-1].replace('.csv','').lower()
            table=next((t for t in TABLES if t.lower()==name),None)
            file=DB.parent/f'{name}.csv'
            if not table or not file.is_file(): return self.send('Export not found','text/plain; charset=utf-8',404)
            self.send_response(200); self.send_header('Content-Type','text/csv; charset=utf-8'); self.send_header('Content-Length',str(file.stat().st_size)); self.send_header('Cache-Control','no-store'); self.send_header('Content-Disposition',f'attachment; filename="{file.name}"'); self.end_headers()
            with file.open('rb') as stream: shutil.copyfileobj(stream,self.wfile,1024*1024)
            return
        return self.send('Not found','text/plain; charset=utf-8',404)
    def log_message(self,*args): pass
    def do_POST(self):
        if self.auth_routes(urlparse(self.path).path) is False:self.json({'error':'Not found'},404)
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--host',default='127.0.0.1'); parser.add_argument('--port',type=int,default=8010); args=parser.parse_args()
    if args.host not in ('127.0.0.1','localhost','::1'): parser.error('This demo server is local-only. Use an HTTPS production server for network access.')
    auth_store.initialize()
    print(f'Portfolio Rebalance Studio at http://{args.host}:{args.port} (DB: {DB})',flush=True); ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()

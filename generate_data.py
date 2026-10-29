#!/usr/bin/env python3
"""Deterministic synthetic portfolio data generator; standard library only."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, random, sqlite3
from datetime import date, timedelta
from pathlib import Path

SEED = 20261022
ASSETS = ["INDIAN_EQUITY", "GLOBAL_EQUITY", "GOVT_BONDS", "GOLD", "CASH"]
RISK_TARGETS = {"Conservative": [20, 5, 45, 10, 20], "Balanced": [35, 15, 25, 15, 10], "Growth": [55, 20, 10, 10, 5]}
ASSET_NAMES = {"INDIAN_EQUITY":"Simulated Indian Large-Cap Equity Basket","GLOBAL_EQUITY":"Simulated Global Equity Fund","GOVT_BONDS":"Simulated Government Securities Basket","GOLD":"Simulated Gold Allocation","CASH":"Simulated INR Cash Balance"}
ROOT = Path(__file__).resolve().parent

def build(out: Path, portfolios: int = 1000, holdings_per_portfolio: int = 5, days: int = 250, seed: int = SEED):
    rng = random.Random(seed); out.mkdir(parents=True, exist_ok=True)
    db = out / "portfolio.db"
    if db.exists(): db.unlink()
    con = sqlite3.connect(db); con.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
    today = date(2026, 10, 29); price_dates=[]; d=today
    while len(price_dates)<days:
        if d.weekday()<5: price_dates.append(d.isoformat())
        d-=timedelta(days=1)
    price_dates.reverse()
    instruments=[]; investors=[]; ports=[]; targets=[]; holdings=[]; prices=[]; fees=[]; constraints=[]; proposals=[]; trades=[]; post_trade=[]; truth=[]
    risks=list(RISK_TARGETS)
    for p in range(1,portfolios+1):
        inv=f"INV-{p:06d}"; port=f"PORT-{inv}-01"; risk=risks[(p-1)%3]; investors.append((inv,f"Investor {p:04d}",risk, today.isoformat()))
        ports.append((port,inv,"INR",500000+rng.randint(0,4500000),0.0,"ACTIVE",today.isoformat()))
        alloc=RISK_TARGETS[risk]; asset_types=[a for a,w in zip(ASSETS,alloc) if w>0]
        # A coherent 5-asset mix with small per-portfolio target variation.
        raw=[max(1,w+rng.randint(-3,3)) for w in alloc]; total=sum(raw); weights=[round(w*100/total,2) for w in raw]; weights[-1]=round(weights[-1]+100-sum(weights),2)
        for a,w in zip(ASSETS,weights): targets.append((f"TGT-{p:06d}-{a}",port,a,w,today.isoformat(),None))
        for j,a in enumerate(ASSETS[:holdings_per_portfolio]):
            idx=(p-1)*holdings_per_portfolio+j+1; ins=f"INS-{idx:06d}"; ticker=f"SIM{idx:05d}"; price=100+rng.random()*4900
            excluded_case=(p%37==0 and j==1)
            instruments.append((ins,ticker,f"{ASSET_NAMES[a]} {idx}",a,"INR",not excluded_case,"ACTIVE"))
            qty=round((ports[-1][3]*weights[j]/100)/price*rng.uniform(.85,1.15),6)
            drift_case=(p%19==0 and j==0); excluded=(p%37==0 and j==1); missing=(p%43==0 and j==2); stale=(p%47==0 and j==3)
            if drift_case: qty=round(qty*2.5,6)
            holdings.append((f"HOLD-{port}-{ins}",port,ins,qty,today.isoformat(),"ACTIVE"))
            for k,dt in enumerate(price_dates):
                if missing and k==len(price_dates)-1: continue
                # Fixed-seed random walk with deterministic bounded steps.
                price=max(.25,price*(1+rng.gauss(.00015,.009)))
                if stale and k==len(price_dates)-1: continue
                prices.append((f"PX-{ins}-{dt}",ins,dt,round(price,4),"INR",False))
            if excluded: pass
        fees.append((f"FEE-{p:06d}",port,0.0015 if p%4 else 0.0008,10.0,0.0,today.isoformat(),None))
        turnover_cap=2.0 if p%17==0 else 15.0 if p%5==0 else 40.0
        constraints.append((f"CON-{p:06d}",port,500.0,0.05,True,turnover_cap,today.isoformat(),None))
        # Known issue records, explicitly separated from input data.
        for kind, cond in [("missing_price",p%43==0),("high_drift",p%19==0),("excluded_instrument",p%37==0),("fee_tier",p%4==0)]:
            if cond: truth.append({"portfolio_id":port,"issue_type":kind,"expected_action":"BLOCK_OR_FLAG" if kind in {"missing_price","excluded_instrument"} else "REVIEW","source_rule":"generator documented deterministic rule"})
    # Build current snapshot and reproducible rule-based rebalance outputs from source rows.
    px_latest={r[1]:r for r in prices if r[2]==price_dates[-1]}
    target_by_port={}
    for row in targets: target_by_port.setdefault(row[1],{})[row[2]]=row[3]
    holding_by_port={}
    for h in holdings: holding_by_port.setdefault(h[1],[]).append(h)
    ins_by_id={r[0]:r for r in instruments}; fee_by_port={r[1]:r for r in fees}; con_by_port={r[1]:r for r in constraints}
    for p,portrow in enumerate(ports,1):
        port=portrow[0]; hs=holding_by_port[port]; values=[]
        for h in hs:
            px=px_latest.get(h[2]); values.append((h,px, (h[3]*px[3] if px else 0)))
        total=sum(v for _,_,v in values) or 1; rb=f"RB-2026-{p:06d}"; issues=[]; proposed=[]
        used_turnover=0.0; turnover_limit=total*con_by_port[port][5]/100
        for h,px,value in values:
            inst=ins_by_id[h[2]]; target=target_by_port[port].get(inst[3],0); current=value/total*100; drift=current-target
            is_excluded=not inst[5]; missing_px=px is None
            if abs(drift)>=con_by_port[port][3]*100 or missing_px or is_excluded:
                side="BUY" if drift<0 else "SELL"; amount=abs(target*total/100-value); quantity=amount/(px[3] if px else 1)
                exceeds=(side=="SELL" and quantity>h[3])
                reason="missing_price" if missing_px else "excluded_instrument" if is_excluded else "exceeds_holding" if exceeds else "minimum_trade" if amount<con_by_port[port][2] else "drift"
                status="BLOCKED" if missing_px or is_excluded or exceeds else "PROPOSED" if amount>=con_by_port[port][2] else "NO_ACTION"
                if status=="PROPOSED" and used_turnover+amount>turnover_limit:
                    status="BLOCKED"; reason="max_turnover"
                elif status=="PROPOSED": used_turnover+=amount
                proposed.append((h,px,side,amount,quantity,reason,status,drift))
                if reason!="drift": issues.append(reason)
        status="REVIEW" if issues else "READY" if proposed else "ON_TARGET"
        proposals.append((rb,port,today.isoformat(),status,json.dumps(sorted(set(issues))),total,0.0))
        for n,(h,px,side,amount,qty,reason,status2,drift) in enumerate(proposed,1):
            fee=round(max(fee_by_port[port][3],amount*fee_by_port[port][2]),2)
            if status2!="PROPOSED": amount=0; qty=0; fee=0
            trades.append((f"TRD-{p:06d}-{n:02d}",rb,port,h[2],side,round(qty,6),round(amount,2),fee,status2,reason))
        proposals[-1]=(*proposals[-1][:6],round(sum(t[7] for t in trades if t[1]==rb),2))
        adjustments={t[3]: (t[5] if t[4]=="BUY" else -t[5]) for t in trades if t[1]==rb and t[8]=="PROPOSED"}
        projected={a:0.0 for a in ASSETS}; current={a:0.0 for a in ASSETS}
        for h,px,value in values:
            asset=ins_by_id[h[2]][3]; current[asset]+=value
            projected[asset]+=max(0,(h[3]+adjustments.get(h[2],0))*(px[3] if px else 0))
        current_total=sum(current.values()) or 1; projected_total=sum(projected.values()) or 1
        for asset in ASSETS:
            target=target_by_port[port].get(asset,0); cur_pct=current[asset]/current_total*100; projected_pct=projected[asset]/projected_total*100
            post_trade.append((f"PTA-{p:06d}-{asset}",rb,asset,round(cur_pct,4),target,round(projected_pct,4),round(projected_pct-target,4)))
    tables={"InvestorProfile":investors,"Portfolio":ports,"Instrument":instruments,"Holding":holdings,"MarketPrice":prices,"TargetAllocation":targets,"FeeSchedule":fees,"Constraint":constraints,"RebalanceProposal":proposals,"Trade":trades,"PostTradeAllocation":post_trade}
    for table, rows in tables.items():
        con.executemany(f'INSERT INTO "{table}" VALUES ({",".join("?" for _ in rows[0])})',rows)
    con.commit()
    # CSV and JSON exports are generated from the exact persisted input records.
    for table in tables:
        cur=con.execute(f'SELECT * FROM "{table}"'); headers=[x[0] for x in cur.description]
        with (out/f"{table.lower()}.csv").open("w",newline="",encoding="utf-8") as f: w=csv.writer(f); w.writerow(headers); w.writerows(cur)
        cur=con.execute(f'SELECT * FROM "{table}"')
        with (out/f"{table.lower()}.json").open("w",encoding="utf-8") as f:
            f.write("["); first=True
            for row in cur:
                if not first: f.write(",")
                f.write(json.dumps(dict(zip(headers,row)),separators=(",",":"))); first=False
            f.write("]")
    with (out/"ground_truth.json").open("w",encoding="utf-8") as f: json.dump(truth,f,indent=2)
    scenarios=[
      {"scenario_id":"EDGE-001","issue_type":"allocation_not_100_percent","input":{"target_weights_pct":[30,20,20,10,10]},"expected_decision":"BLOCK_AND_FLAG","rule":"Active target allocation must sum to exactly 100%."},
      {"scenario_id":"EDGE-002","issue_type":"trade_exceeds_holding","input":{"side":"SELL","held_quantity":2.0,"proposed_quantity":2.5},"expected_decision":"BLOCK","rule":"A sell quantity cannot exceed the available holding."},
      {"scenario_id":"EDGE-003","issue_type":"excluded_instrument_recommended","input":{"instrument_eligible":False,"trade_status":"PROPOSED"},"expected_decision":"BLOCK","rule":"Ineligible instruments cannot be proposed for execution."},
      {"scenario_id":"EDGE-004","issue_type":"fee_omitted","input":{"notional":100000.0,"fee_rate":0.0015,"minimum_fee":10.0,"estimated_fee":0.0,"currency":"INR"},"expected_decision":"FLAG","rule":"Estimate fee as max(minimum fee, notional times applicable rate)."},
      {"scenario_id":"EDGE-005","issue_type":"stale_price_unflagged","input":{"price_age_days":5,"stale_flag":False},"expected_decision":"FLAG_AND_BLOCK","rule":"Price older than one trading day must be marked stale and excluded from a new proposal."}
    ]
    (out/"edge_cases.json").write_text(json.dumps(scenarios,indent=2),encoding="utf-8")
    validation={"foreign_key_violations":len(list(con.execute("PRAGMA foreign_key_check")),),"bad_target_weight_totals":con.execute("SELECT COUNT(*) FROM (SELECT portfolio_id FROM TargetAllocation WHERE effective_to IS NULL GROUP BY portfolio_id HAVING ABS(SUM(target_pct)-100)>0.01)").fetchone()[0],"proposal_fee_reconciliation_failures":con.execute("SELECT COUNT(*) FROM (SELECT p.proposal_id FROM RebalanceProposal p LEFT JOIN Trade t USING(proposal_id) GROUP BY p.proposal_id HAVING ABS(p.estimated_fees-COALESCE(SUM(t.estimated_fee),0))>0.01)").fetchone()[0],"projected_weight_reconciliation_failures":con.execute("SELECT COUNT(*) FROM (SELECT proposal_id FROM PostTradeAllocation GROUP BY proposal_id HAVING ABS(SUM(projected_pct)-100)>0.02)").fetchone()[0]}
    validation["valid"]=not any(validation.values())
    (out/"validation_summary.json").write_text(json.dumps(validation,indent=2),encoding="utf-8")
    counts={name:con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in tables}; con.close()
    manifest={"seed":seed,"parameters":{"portfolios":portfolios,"holdings_per_portfolio":holdings_per_portfolio,"price_days":days},"generated_at":"2026-10-29","source_manifest":{"type":"synthetic","external_sources":[],"generator":"generate_data.py","source_revision":"1.0","usage":"Original generated educational simulation data"},"validation_summary":validation,"counts":counts,"checksums":{}}
    for f in sorted(out.glob("*")):
        if f.is_file() and f.name!="manifest.json":
            digest=hashlib.sha256()
            with f.open("rb") as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b""): digest.update(chunk)
            manifest["checksums"][f.name]=digest.hexdigest()
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--out",type=Path,default=ROOT/"data"); ap.add_argument("--portfolios",type=int,default=1000); ap.add_argument("--holdings-per-portfolio",type=int,default=5); ap.add_argument("--days",type=int,default=250); ap.add_argument("--seed",type=int,default=SEED); a=ap.parse_args()
    if min(a.portfolios,a.holdings_per_portfolio,a.days)<1: ap.error("all scale parameters must be positive")
    print(json.dumps(build(a.out,a.portfolios,a.holdings_per_portfolio,a.days,a.seed),indent=2))
if __name__=="__main__": main()

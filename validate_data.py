#!/usr/bin/env python3
"""Validate generated relational records and reconciliation rules."""
import argparse, json, sqlite3
from pathlib import Path

def validate(db: Path):
    c=sqlite3.connect(db); c.row_factory=sqlite3.Row; errors=[]; counts={}
    c.execute("PRAGMA foreign_keys=ON")
    fk=[r for t in ["Portfolio","Holding","MarketPrice","TargetAllocation","Trade","RebalanceProposal","FeeSchedule","Constraint","PostTradeAllocation"] for r in c.execute(f"PRAGMA foreign_key_check('{t}')")]
    if fk: errors.append(f"foreign key violations: {len(fk)}")
    for table in ["InvestorProfile","Portfolio","Instrument","Holding","MarketPrice","TargetAllocation","Trade","FeeSchedule","Constraint","RebalanceProposal","PostTradeAllocation"]:
        counts[table]=c.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        pkcol={"InvestorProfile":"investor_id","Portfolio":"portfolio_id","Instrument":"instrument_id","Holding":"holding_id","MarketPrice":"price_id","TargetAllocation":"target_id","Trade":"trade_id","FeeSchedule":"fee_id","Constraint":"constraint_id","RebalanceProposal":"proposal_id","PostTradeAllocation":"allocation_id"}[table]
        pk=c.execute(f'SELECT COUNT(*)-COUNT(DISTINCT {pkcol}) FROM "{table}"').fetchone()[0]
        if pk: errors.append(f"{table}: duplicate primary keys: {pk}")
    for row in c.execute("SELECT portfolio_id,ROUND(SUM(target_pct),2) s FROM TargetAllocation WHERE effective_to IS NULL GROUP BY portfolio_id"):
        if row['s']!=100: errors.append(f"{row['portfolio_id']}: target allocation totals {row['s']}")
    for row in c.execute("SELECT p.proposal_id,p.estimated_fees,ROUND(COALESCE(SUM(t.estimated_fee),0),2) fee_sum FROM RebalanceProposal p LEFT JOIN Trade t USING(proposal_id) GROUP BY p.proposal_id"):
        if round(row['estimated_fees'],2)!=row['fee_sum']: errors.append(f"{row['proposal_id']}: proposal fee total does not reconcile")
    checks=[
      ("SELECT COUNT(*) FROM (SELECT t.trade_id FROM Trade t JOIN RebalanceProposal p USING(proposal_id) WHERE p.portfolio_id<>t.portfolio_id)","trade/proposal portfolio mismatch"),
      ("SELECT COUNT(*) FROM Trade t JOIN Instrument i USING(instrument_id) WHERE t.status='PROPOSED' AND i.eligible=0","ineligible instrument marked proposed"),
      ("SELECT COUNT(*) FROM Trade t JOIN Holding h ON h.portfolio_id=t.portfolio_id AND h.instrument_id=t.instrument_id WHERE t.status='PROPOSED' AND t.side='SELL' AND t.quantity>h.quantity","proposed sell exceeds holding"),
      ("SELECT COUNT(*) FROM (SELECT p.proposal_id,p.total_value,c.max_turnover_pct,COALESCE(SUM(CASE WHEN t.status='PROPOSED' THEN t.notional ELSE 0 END),0) turnover FROM RebalanceProposal p JOIN \"Constraint\" c USING(portfolio_id) LEFT JOIN Trade t USING(proposal_id) GROUP BY p.proposal_id HAVING turnover>p.total_value*c.max_turnover_pct/100+0.01)","proposed turnover exceeds constraint"),
      ("SELECT COUNT(*) FROM MarketPrice WHERE close<=0 OR date(price_date) IS NULL","invalid price or date"),
      ("SELECT COUNT(*) FROM TargetAllocation WHERE effective_to IS NOT NULL AND date(effective_to)<date(effective_from)","invalid target effective-date order"),
      ("SELECT COUNT(*) FROM FeeSchedule WHERE effective_to IS NOT NULL AND date(effective_to)<date(effective_from)","invalid fee effective-date order"),
      ("SELECT COUNT(*) FROM \"Constraint\" WHERE effective_to IS NOT NULL AND date(effective_to)<date(effective_from)","invalid constraint effective-date order"),
    ]
    for sql,label in checks:
        found=c.execute(sql).fetchone()[0]
        if found: errors.append(f"{label}: {found}")
    for row in c.execute("SELECT proposal_id,ROUND(SUM(projected_pct),2) s FROM PostTradeAllocation GROUP BY proposal_id"):
        if abs(row['s']-100)>0.02: errors.append(f"{row['proposal_id']}: projected allocation totals {row['s']}")
    # Lifecycle/date and referential sanity.
    bad=c.execute("SELECT COUNT(*) FROM Holding h JOIN Portfolio p USING(portfolio_id) WHERE date(h.as_of)<date(p.created_at)").fetchone()[0]
    if bad: errors.append(f"holdings before portfolio creation: {bad}")
    c.close(); return {"valid":not errors,"counts":counts,"errors":errors}
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("db",type=Path,nargs="?",default=Path(__file__).parent/"data"/"portfolio.db"); a=p.parse_args(); result=validate(a.db); print(json.dumps(result,indent=2)); raise SystemExit(0 if result['valid'] else 1)

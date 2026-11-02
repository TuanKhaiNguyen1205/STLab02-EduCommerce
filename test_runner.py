
"""CSV-driven execution for STLab02. Source baseline remains intentionally unpatched."""

import csv,json,time,datetime,pathlib,collections,html
import pandas as pd
from decimal import Decimal
from ecommerce_app import fixture,Cart,D

ROOT=pathlib.Path(__file__).parent
REQUIRED={'test_case_id','requirement_id','condition_id','scenario_id','fixture_key','input_json','expected_type','expected_json'}


def run_one(row):

    started=time.perf_counter()
    actual={}
    err=''
    outcome='FAIL'

    try:
        request=json.loads(row['input_json'])
        expected=json.loads(row['expected_json'])

        if not isinstance(request,dict) or not isinstance(expected,dict):
            raise TypeError('JSON_OBJECT_REQUIRED')

        app,user,cart=fixture(row['fixture_key'])
        op=request['operation']

        before={k:v.stock for k,v in app.catalog.products.items()}

        try:

            if op=='add':
                cart.add(request['sku'],request['qty'])
                actual={'qty':cart.total_quantity(),'lines':len(cart.lines)}

            elif op=='shipping':
                actual={'fee':int(app.shipping.calculate(cart.subtotal(),request['area']))}

            elif op=='checkout':
                order=app.place(user,cart,area=request.get('area','inner'),voucher=request.get('voucher'),method=request.get('method','COD'),approved=request.get('approved',True),key=row['test_case_id'])
                actual={'status':order.status,'total':int(order.total)}

            elif op=='two_orders':
                a=app.place(user,cart,key='ONE')
                b=app.place(user,cart,key='TWO')
                actual={'unique_ids':a.order_id!=b.order_id}

            elif op=='calc_total':
                actual={'total':int(app.calculate_total(D(request['subtotal']),D(request['discount']),D(request['shipping'])))}

            else:
                raise RuntimeError('UNKNOWN_OPERATION:'+str(op))

        except ValueError as e:
            err=str(e)
            actual={'error':err}

        after={k:v.stock for k,v in app.catalog.products.items()}

        if op=='add':
            actual.update(qty=cart.total_quantity(),lines=len(cart.lines))

        actual.update(orders=len(app.orders),charges=len(app.payments.charges),stock_unchanged=before==after,stock_before=before,stock_after=after)

        mismatch={
            k:{'expected':v,'actual':actual.get(k,'<MISSING>')}
            for k,v in expected.items()
            if actual.get(k)!=v
        }

        # Expected ValueError must match exactly; unexpected exceptions always fail.

        if err and 'error' not in expected:
            mismatch['unexpected_exception']={'actual':err}

        outcome='PASS' if not mismatch else 'FAIL'

    except (KeyError,ValueError,TypeError,json.JSONDecodeError) as e:
        outcome='BLOCKED'
        err='SETUP_ERROR:'+str(e)
        mismatch={'setup_error':err}

    except Exception as e:
        outcome='BLOCKED'
        err='RUNNER_ERROR:'+repr(e)
        mismatch={'runner_error':err}

    return dict(row,execution_status=outcome,actual_result=json.dumps(actual,ensure_ascii=False),error_message=err,evidence_reference=f"reports/test_execution.csv#{row.get('test_case_id','')}",comparison=json.dumps(mismatch,ensure_ascii=False),execution_time_ms=round((time.perf_counter()-started)*1000,3),executed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())


def main():

    with (ROOT/'test_cases.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        missing=REQUIRED-set(reader.fieldnames or [])

        if missing:
            raise RuntimeError(f'MISSING_COLUMNS:{missing}')

        rows=list(reader)

    if len({r['test_case_id'] for r in rows})!=len(rows):
        raise RuntimeError('DUPLICATE_TEST_IDS')

    results=[run_one(r) for r in rows]

    if len(results)!=len(rows):
        raise RuntimeError('ROW_COUNT_MISMATCH')

    out=ROOT/'reports'
    out.mkdir(exist_ok=True)

    with (out/'test_execution.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(results[0]),extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

    stats=collections.Counter(r['execution_status'] for r in results)
    byreq=collections.defaultdict(collections.Counter)

    for r in results:
        byreq[r['requirement_id']][r['execution_status']]+=1

    cards=''.join(
        f'<div class="card"><b>{html.escape(k)}</b><br>{v}</div>'
        for k,v in [('TOTAL',len(results)),('PASS',stats['PASS']),('FAIL',stats['FAIL']),('BLOCKED',stats['BLOCKED'])]
    )

    trs=''.join(
        '<tr>'+''.join(
            f'<td>{html.escape(str(r.get(col,"")))}</td>'
            for col in ['test_case_id','requirement_id','title','execution_status','expected_json','actual_result','comparison']
        )+'</tr>'
        for r in results
    )

    bars=''.join(
        f'<tr><td>{k}</td><td>{sum(v.values())}</td><td>{v["PASS"]}</td><td>{v["FAIL"]}</td><td>{v["BLOCKED"]}</td></tr>'
        for k,v in sorted(byreq.items())
    )

    page=f'''
<!doctype html>
<html lang="vi">

<head>
    <meta charset="utf-8">
    <title>STLab02 Execution Dashboard</title>

    <style>
        body{{font:15px Arial;margin:32px;color:#172c42;background:#f4f7fb}}
        h1{{color:#133b65}}
        .cards{{display:flex;gap:16px}}
        .card{{background:white;border-radius:8px;padding:22px;min-width:120px;box-shadow:0 1px 4px #ccc}}
        table{{width:100%;border-collapse:collapse;background:white;margin:20px 0;font-size:12px}}
        th,td{{border:1px solid #dce3ef;padding:8px;vertical-align:top;overflow-wrap:anywhere}}
        th{{background:#d7e6f6}}
    </style>
</head>

<body>
    <h1>EduCommerce — Test execution</h1>

    <p>
        Baseline: Instruction logic; expected independently from acceptance criteria.
        Generated UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
    </p>

    <section class="cards">
        {cards}
    </section>

    <h2>Results by requirement</h2>

    <table>
        <tr>
            <th>REQ</th>
            <th>TOTAL</th>
            <th>PASS</th>
            <th>FAIL</th>
            <th>BLOCKED</th>
        </tr>
        {bars}
    </table>

    <h2>Detailed execution</h2>

    <table>
        <tr>
            {''.join('<th>'+x+'</th>' for x in ['Case','REQ','Title','Status','Expected','Actual','Differences'])}
        </tr>
        {trs}
    </table>
</body>

</html>
'''

    (out/'test_dashboard.html').write_text(page,encoding='utf-8')

    df=pd.DataFrame(results)

    matrix=df[['requirement_id','condition_id','scenario_id','test_case_id','execution_status','evidence_reference','executed_at']].copy()

    summary_rows=[
        {'requirement_id':k,'total':sum(v.values()),'PASS':v['PASS'],'FAIL':v['FAIL'],'BLOCKED':v['BLOCKED']}
        for k,v in sorted(byreq.items())
    ]

    totals=pd.DataFrame([
        {'total':len(results),'PASS':stats['PASS'],'FAIL':stats['FAIL'],'BLOCKED':stats['BLOCKED'],'pass_rate_pct':round(100*stats['PASS']/len(results),2) if results else 0}
    ])

    with pd.ExcelWriter(out/'test_report.xlsx',engine='openpyxl') as xls:
        df.to_excel(xls,sheet_name='Execution',index=False)
        pd.DataFrame(summary_rows).to_excel(xls,sheet_name='By Requirement',index=False)
        matrix.to_excel(xls,sheet_name='Traceability',index=False)
        totals.to_excel(xls,sheet_name='Summary',index=False)

    print('TOTAL',len(results),'PASS',stats['PASS'],'FAIL',stats['FAIL'],'BLOCKED',stats['BLOCKED'])

    for r in results:

        if r['execution_status']!='PASS':
            print(r['test_case_id'],r['execution_status'],r['comparison'])


if __name__=='__main__':
    main()

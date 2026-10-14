"""Transparent fixture benchmark; not a score against PentAGI."""
import time
from .engine import run
from .lab import Lab, demo_config

CASES=('document','attachment','admin','revoked_session','upload','render')

def benchmark(repeats=3):
    if not isinstance(repeats,int) or not 1<=repeats<=20: raise ValueError('repeats must be 1..20')
    tp=fp=fn=tn=unresolved=0; runs=[]
    for trial in range(repeats):
        for vulnerable in (False,True):
            with Lab(vulnerable=vulnerable) as lab: report=run(demo_config(lab))
            for case in CASES:
                states=[r['status'] for r in report['results'] if r['target']==case]
                detected='fail' in states
                complete=bool(states) and all(s in ('pass','fail') for s in states)
                unresolved+=not complete
                if vulnerable:
                    tp+=detected;fn+=not detected
                elif detected:fp+=1
                elif complete:tn+=1
            runs.append({'trial':trial+1,'fixture':'vulnerable' if vulnerable else 'fixed',
                         'summary':report['summary'],'metrics':report['metrics']})
    return {'benchmark':'bundled-synthetic-fixture-v1','repeats':repeats,'cases':repeats*len(CASES)*2,
            'true_positives':tp,'false_positives':fp,'false_negatives':fn,'true_negatives':tn,'unresolved':unresolved,
            'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,
            'runs':runs,'note':'동봉한 6개 합성 사례의 회귀 실험입니다. 외부 벤치마크나 PentAGI 비교 결과가 아닙니다.'}

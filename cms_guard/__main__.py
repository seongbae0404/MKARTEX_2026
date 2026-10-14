"""CLI entry point. Run `python -m cms_guard demo` for a self-contained start."""
import argparse
import http.client
import json
from pathlib import Path
import sys
from .config import validate, ConfigError
from .engine import run
from .lab import Lab, demo_config
from .report import write_report, save_private
from .benchmark import benchmark


def load(path):
    p=Path(path)
    if p.stat().st_size>1048576: raise ConfigError('Input JSON must be at most 1 MiB')
    with p.open(encoding='utf-8') as f:return json.load(f)

def exit_status(report):
    counts=report['summary']
    if counts['error']:return 1
    if counts['fail']:return 2
    if counts['inconclusive'] or counts['manual']:return 3
    return 0

def main(argv=None):
    parser=argparse.ArgumentParser(description='CMS Guard Lite · 직원용 CMS의 명시적 권한·세션 점검')
    sub=parser.add_subparsers(dest='command',required=True)
    demo=sub.add_parser('demo',help='루프백 서버를 자동으로 시작·점검·종료')
    demo.add_argument('--vulnerable',action='store_true',help='의도적으로 취약한 합성 사례')
    demo.add_argument('--output',default='reports/demo')
    check=sub.add_parser('validate',help='설정 검사 (네트워크 요청 없음)');check.add_argument('config')
    scan=sub.add_parser('run',help='명시된 테스트 URL 조회');scan.add_argument('config');scan.add_argument('--output',default='reports/run')
    audit=sub.add_parser('audit',help='설정 스냅샷만 검토 (네트워크 요청 없음)');audit.add_argument('snapshot');audit.add_argument('--output',default='reports/audit')
    bench=sub.add_parser('benchmark',help='동봉한 고정/취약 실험 반복');bench.add_argument('--repeats',type=int,default=3);bench.add_argument('--output',default='reports/benchmark.json')
    summary=sub.add_parser('summarize',help='결과 집계만 로컬 LLM으로 요약');summary.add_argument('report');summary.add_argument('--model',required=True);summary.add_argument('--port',type=int,default=11434);summary.add_argument('--output',default='reports/summary.txt')
    args=parser.parse_args(argv)
    try:
        if args.command=='validate':
            c=validate(load(args.config));print(f'설정 유효: 대상 {len(c["targets"])}개. 네트워크 요청 없음.');return 0
        if args.command=='benchmark':
            data=benchmark(args.repeats);p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True)
            save_private(p,json.dumps(data,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in data.items() if k!='runs'},ensure_ascii=False,indent=2));return 0
        if args.command=='summarize':
            from .llm import summarize
            text=summarize(load(args.report),args.model,args.port)
            p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);save_private(p,'AI 생성 집계 요약 · 판정 근거가 아닙니다.\n\n'+text)
            print(f'로컬 요약 저장: {p}');return 0
        if args.command=='demo':
            with Lab(args.vulnerable) as lab: report=run(demo_config(lab))
        elif args.command=='audit':
            report=run({'version':1,'mode':'remote','roles':{'anonymous':{}},'targets':[],'snapshot':load(args.snapshot)})
        else:
            def progress(id_,rows): print(f'[{id_}] '+', '.join(r['role']+':'+r['status'] for r in rows))
            report=run(load(args.config),progress)
        destination=write_report(report,args.output)
        print(json.dumps(report['summary'],ensure_ascii=False));print(f'보고서: {destination}')
        return exit_status(report)
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,IndexError,http.client.HTTPException) as exc:
        # Exception messages from HTTP/JSON may echo secrets; keep stderr categorical.
        print(f'실행 중단: {type(exc).__name__}. 설정 형식, 환경 변수, 네트워크 또는 로컬 모델을 확인하세요.',file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('사용자가 중단했습니다.',file=sys.stderr);return 130

if __name__=='__main__':sys.exit(main())

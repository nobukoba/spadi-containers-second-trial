#!/usr/bin/env python3
"""Frozen synthetic byte-stream recovery and bounded-memory replay experiment."""
import argparse
import collections
import hashlib
import io
import json
import platform
import random
import statistics
import struct
import sys
import time
import tracemalloc
import zipfile
from pathlib import Path

import benchmark
from prepare import HEADER, STF_MAGIC, inspect

ROOT=Path(__file__).resolve().parent
MAGIC=struct.pack('<Q',STF_MAGIC)
PATTERNS=('missing','duplicate','reorder','header_magic','header_length','garbage','payload_truncation','mixed')

def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,value):
    path.write_bytes((json.dumps(value,indent=2,ensure_ascii=True)+'\n').encode())

def stream_frames(stream,reference,chunk_size,recover,alarms):
    """No labels/boundaries: receive continuous bytes and development references."""
    buffer=b'';offset=0;eof=False;pending=None
    maximum=reference['maximum_frame_bytes']
    def plausible(at):
        if len(buffer)-at<48:return None
        h=HEADER.unpack_from(buffer,at)
        if (h[0]!=STF_MAGIC or h[2]!=48 or not 48<=h[1]<=maximum or
            h[3]!=reference['type'] or h[5]!=reference['fem_type'] or
            h[6]!=reference['fem_id'] or h[7]!=reference['messages'] or h[9]>=1_000_000):
            return False
        return h
    while True:
        if not eof and len(buffer)<maximum+48:
            part=stream.read(chunk_size)
            if part:buffer+=part
            else:eof=True
        if not buffer:
            if pending is not None:alarms.append(dict(kind='framing_corruption',start=pending,end=offset))
            return
        h=plausible(0)
        if h is None and not eof:continue
        valid=h is not None and h is not False
        if valid:
            length=h[1]
            if len(buffer)<length:
                if not eof:continue
                valid=False
            elif len(buffer)<length+48 and not eof:
                continue
            elif pending is not None and len(buffer)>=length+48 and not plausible(length):
                valid=False
        if valid:
            if pending is not None:
                alarms.append(dict(kind='framing_corruption',start=pending,end=offset))
                pending=None
            record=buffer[:length]
            yield offset,record
            offset+=length;buffer=buffer[length:]
            continue
        if not recover:
            alarms.append(dict(kind='framing_corruption',start=offset,end=min(offset+48,offset+len(buffer))))
            return
        if pending is None:pending=offset
        candidate=buffer.find(MAGIC,1)
        if candidate>=0:
            offset+=candidate;buffer=buffer[candidate:]
        elif eof:
            offset+=len(buffer);buffer=b''
        else:
            # Keep only the possible split magic suffix; buffering is bounded.
            skip=max(0,len(buffer)-7)
            offset+=skip;buffer=buffer[skip:]

def classify(data,reference,chunk_size,recover):
    parser_alarms=[]
    recovered=list(stream_frames(io.BytesIO(data),reference,chunk_size,recover,parser_alarms))
    observations=[benchmark.observation(record,i) for i,(_,record) in enumerate(recovered)]
    blind=dict(reference=reference,records=observations)
    alarms=list(parser_alarms)
    for alarm in benchmark.rules(blind)['alarms']:
        offsets=[recovered[i][0] for i in alarm['indexes']]
        alarms.append(dict(kind=alarm['kind'],start=min(offsets),end=max(offsets)+1))
    return dict(alarms=alarms,recovered_sha256=[sha(record) for _,record in recovered],
                recovered_frames=len(recovered))

def corpus(data):
    expected=read(ROOT/'results/summary.json')
    result={}
    for source in ('00','01','02'):
        path=data/source/'run000020.dat'
        info,frames=inspect(path)
        previous=next(s for s in expected['sources'] if Path(s['file']).parent.name==source)
        if info['sha256']!=previous['sha256'] or len(frames)!=previous['frames']:
            raise ValueError('Public source hash/frame count mismatch')
        raw=path.read_bytes()
        if raw[:8]!=b'FILESNK\0' or raw[-304:-296]!=b'FILETRL\0':
            raise ValueError('Unexpected public file envelope')
        cut=len(frames)//2
        reference=benchmark.reference_for(frames[:cut])
        reference['maximum_frame_bytes']=max(4096,4*max(f['length'] for f in frames[:cut]))
        chunks=[raw[f['offset']:f['offset']+f['length']] for f in frames]
        result[source]=dict(path=path,hash=info['sha256'],frames=frames,chunks=chunks,cut=cut,reference=reference)
    return result

def mutate(chunks,pattern,position):
    entries=[dict(original=i,raw=c,damaged=False,tag=None) for i,c in enumerate(chunks)]
    interventions=[]
    def remove(original):
        index=next(i for i,e in enumerate(entries) if e['original']==original)
        entries.pop(index)
        interventions.append(dict(kind='missing',anchor_original=original+1))
    def duplicate(original):
        index=next(i for i,e in enumerate(entries) if e['original']==original)
        new=dict(entries[index]);new['tag']='duplicate'
        entries.insert(index+1,new)
        interventions.append(dict(kind='duplicate',anchor_tag='duplicate'))
    def damage(original,mode):
        index=next(i for i,e in enumerate(entries) if e['original']==original)
        e=entries[index];raw=bytearray(e['raw'])
        if mode=='magic':raw[0]=0
        elif mode=='length':struct.pack_into('<I',raw,8,0xffffffff)
        else:del raw[58:75]
        e.update(raw=bytes(raw),damaged=True)
        interventions.append(dict(kind='framing_corruption',anchor_original=original))
    if pattern=='missing':remove(position)
    elif pattern=='duplicate':duplicate(position)
    elif pattern=='reorder':
        entries[position],entries[position+1]=entries[position+1],entries[position]
        interventions.append(dict(kind='reorder',anchor_original=position+1,other_original=position))
    elif pattern=='header_magic':damage(position,'magic')
    elif pattern=='header_length':damage(position,'length')
    elif pattern=='payload_truncation':damage(position,'payload')
    elif pattern=='garbage':
        entries.insert(position,dict(original=None,raw=b'noise-\x00-\xff',damaged=True,tag='garbage'))
        interventions.append(dict(kind='framing_corruption',anchor_tag='garbage'))
    elif pattern=='mixed':
        remove(8);duplicate(24);damage(40,'length')
    offset=0
    for e in entries:e['offset']=offset;offset+=len(e['raw'])
    for intervention in interventions:
        matches=[e for e in entries if e['tag']==intervention.get('anchor_tag')] if 'anchor_tag' in intervention else [e for e in entries if e['original']==intervention['anchor_original'] and e['tag'] is None]
        e=matches[0]
        start=e['offset'];end=start+len(e['raw'])
        if 'other_original' in intervention:
            other=next(x for x in entries if x['original']==intervention['other_original'])
            start=min(start,other['offset']);end=max(end,other['offset']+len(other['raw']))
        intervention.update(byte_start=start,byte_end=end)
    intact=[sha(e['raw']) for e in entries if not e['damaged']]
    return b''.join(e['raw'] for e in entries),dict(interventions=interventions,intact_sha256=intact)

def prepare(data,out):
    if out.exists():raise ValueError('Output exists; use a new directory')
    sources=corpus(data);rng=random.Random(20261006)
    inputs={};labels={};payloads={}
    for source,s in sources.items():
        for phase,starts in (('development',[64]),('evaluation',sorted(rng.sample(list(range(s['cut'],len(s['frames'])-63,64)),4)))):
            for start in starts:
                chunks=s['chunks'][start:start+64]
                for pattern in ('untouched',)+PATTERNS:
                    position=rng.randrange(12,48)
                    binary,label=mutate(chunks,pattern,position)
                    identifier=sha(f'{phase}/{source}/{start}/{pattern}'.encode())[:16]
                    inputs[identifier]=dict(phase=phase,reference=s['reference'],sha256=sha(binary))
                    labels[identifier]=dict(source=source,source_start=start,source_end_exclusive=start+64,
                        original_file_offset=s['frames'][start]['offset'],pattern=pattern,**label)
                    payloads[identifier]=binary
    out.mkdir(parents=True)
    with zipfile.ZipFile(out/'byte-inputs.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for k,binary in payloads.items():archive.writestr(k+'.bin',binary)
    protocol=dict(created_utc=benchmark.now(),seed=20261006,development='One first-half 64-record window per source',
        evaluation='Four non-overlapping second-half 64-record windows per source; 12 paired base windows, 96 interventions plus 12 untouched',
        patterns=list(PATTERNS),source_hashes={k:s['hash'] for k,s in sources.items()},
        chunk_bytes=[512,4096,65536],parser_policies=['strict','resync'],
        scoring='Intervention detected only by same-kind alarm overlapping labelled byte interval; all events required for full-case match. Recovery counts intact-record SHA256 multiplicities.',
        repeat_factors=[1,10,100],timing_trials=3,performance_chunk_bytes=4096,
        performance='Replay the same 8470 records with per-source/session reset; hash each recovered record and maintain a 64-entry duplicate cache. No API.',
        memory='Separate tracemalloc runs at factors 1 and 100, bounded replay buffers; Python-traced allocations only, excludes preloaded corpus and process RSS.',
        limitations=['Same public run; no natural fault truth or independent run.',
            'Repeated workload does not increase unique record or independent fault count.',
            'Resynchronization uses development header constraints and next-header plausibility; not a payload decoder or authenticated framing proof.',
            'All byte mutations and combinations are artificial; no actual detector burst tested.',
            'FileSink envelope is inspected before replay; envelope corruption and network transport are untested.',
            'Windows host performance only; AWS, network, disk and real-time DAQ throughput unmeasured.',
            'No new AI calls or AI superiority measurement.'])
    write(out/'inputs.json',inputs);write(out/'labels.json',labels);write(out/'protocol.json',protocol)
    frozen=[out/'inputs.json',out/'labels.json',out/'protocol.json',out/'byte-inputs.zip',Path(__file__),ROOT/'benchmark.py',ROOT/'prepare.py']
    write(out/'freeze.json',{p.name:sha(p.read_bytes()) for p in frozen})
    print(json.dumps(dict(status='FROZEN_BEFORE_EVALUATION',cases=len(inputs),evaluation_cases=sum(c['phase']=='evaluation' for c in inputs.values()))))

def verify(out):
    for name,expected in read(out/'freeze.json').items():
        path=ROOT/name if name.endswith('.py') else out/name
        if sha(path.read_bytes())!=expected:raise ValueError('Frozen artifact changed')

def score(prediction,label):
    expected=collections.Counter(label['intact_sha256'])
    found=collections.Counter(prediction['recovered_sha256'])
    recovered=sum(min(count,found[k]) for k,count in expected.items())
    hits=[any(a['kind']==e['kind'] and a['start']<e['byte_end'] and a['end']>e['byte_start']
              for a in prediction['alarms']) for e in label['interventions']]
    return dict(events=len(hits),detected_events=sum(hits),full_case_match=all(hits) if hits else None,
        intact_expected=sum(expected.values()),intact_recovered=recovered,
        extra_recovered_records=sum(found.values())-recovered)

def evaluate(out,phase):
    verify(out)
    inputs,labels=read(out/'inputs.json'),read(out/'labels.json')
    results={}
    with zipfile.ZipFile(out/'byte-inputs.zip') as archive:
        for identifier,c in inputs.items():
            if c['phase']!=phase:continue
            binary=archive.read(identifier+'.bin')
            if sha(binary)!=c['sha256']:raise ValueError('Input hash mismatch')
            for chunk in read(out/'protocol.json')['chunk_bytes']:
                for policy in ('strict','resync'):
                    begin=time.perf_counter()
                    prediction=classify(binary,c['reference'],chunk,policy=='resync')
                    seconds=time.perf_counter()-begin
                    scored=score(prediction,labels[identifier])
                    recovered_sequence_sha256=benchmark.digest(prediction.pop('recovered_sha256'))
                    results[f'{identifier}:{chunk}:{policy}']=dict(case_id=identifier,chunk_bytes=chunk,
                        policy=policy,seconds=seconds,**prediction,score=scored,
                        recovered_sequence_sha256=recovered_sequence_sha256)
    write(out/(phase+'.json'),results)
    print(json.dumps(dict(phase=phase,parser_runs=len(results))))

def replay_once(sources,factor,policy):
    records=byte_count=alarms=0
    for _ in range(factor):
        for s in sources.values():
            flags=[];cache=collections.deque(maxlen=64);last_id=None
            # Corpus bodies are preloaded once. Each replay uses the same bytes.
            for offset,record in stream_frames(io.BytesIO(s['body']),s['reference'],4096,policy=='resync',flags):
                signature=sha(record)
                tfid=struct.unpack_from('<I',record,16)[0]
                alarms+=signature in cache
                if last_id is not None:alarms+=(tfid-last_id)!=s['reference']['id_step']
                cache.append(signature);last_id=tfid
                records+=1;byte_count+=len(record)
            alarms+=len(flags)
    return dict(frames=records,bytes=byte_count,candidate_alarms=alarms)

def performance(data,out):
    verify(out)
    original=corpus(data)
    sources={k:dict(body=b''.join(s['chunks']),reference=s['reference']) for k,s in original.items()}
    protocol=read(out/'protocol.json');timings=[];memory=[]
    for policy in protocol['parser_policies']:
        # One disclosed untimed warm-up, followed by the frozen trial schedule.
        replay_once(sources,1,policy)
        for factor in protocol['repeat_factors']:
            for trial in range(protocol['timing_trials']):
                begin=time.perf_counter();result=replay_once(sources,factor,policy);seconds=time.perf_counter()-begin
                if result['frames']!=8470*factor:raise ValueError('Replay record count mismatch')
                timings.append(dict(policy=policy,repeat_factor=factor,trial=trial,seconds=seconds,
                    frames_per_second=result['frames']/seconds,mib_per_second=result['bytes']/seconds/2**20,**result))
        for factor in (1,100):
            tracemalloc.start();result=replay_once(sources,factor,policy)
            current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
            memory.append(dict(policy=policy,repeat_factor=factor,python_traced_peak_bytes=peak,frames=result['frames']))
    result=dict(measured_utc=benchmark.now(),platform=sys.platform,python=platform.python_version(),
        os=platform.platform(),processor=platform.processor(),unique_source_records=8470,
        preloaded_body_bytes=sum(len(s['body']) for s in sources.values()),timings=timings,memory=memory,
        api_calls=0,api_tokens=0,aws_execution=False)
    write(out/'performance.json',result)
    print(json.dumps(dict(status='PERFORMANCE_MEASURED',timing_trials=len(timings),memory_trials=len(memory))))

def report(out):
    verify(out)
    labels=read(out/'labels.json');evaluation=read(out/'evaluation.json');metrics={}
    for policy in ('strict','resync'):
        by_chunk={}
        for chunk in (512,4096,65536):
            rows=[r for r in evaluation.values() if r['policy']==policy and r['chunk_bytes']==chunk]
            by_pattern={}
            for pattern in ('untouched',)+PATTERNS:
                group=[r for r in rows if labels[r['case_id']]['pattern']==pattern]
                by_pattern[pattern]=dict(cases=len(group),events=sum(r['score']['events'] for r in group),
                    detected_events=sum(r['score']['detected_events'] for r in group),
                    fully_detected_cases=sum(r['score']['full_case_match'] is True for r in group),
                    alarm_cases=sum(bool(r['alarms']) for r in group),alarms=sum(len(r['alarms']) for r in group),
                    intact_expected=sum(r['score']['intact_expected'] for r in group),
                    intact_recovered=sum(r['score']['intact_recovered'] for r in group),
                    extra_recovered_records=sum(r['score']['extra_recovered_records'] for r in group))
            by_chunk[str(chunk)]=by_pattern
        metrics[policy]=by_chunk
    performance_result=read(out/'performance.json')
    performance_summary={}
    for policy in ('strict','resync'):
        performance_summary[policy]={}
        for factor in (1,10,100):
            rows=[r for r in performance_result['timings'] if r['policy']==policy and r['repeat_factor']==factor]
            performance_summary[policy][str(factor)]=dict(frames_per_trial=8470*factor,
                seconds_median=statistics.median(r['seconds'] for r in rows),
                seconds_min=min(r['seconds'] for r in rows),seconds_max=max(r['seconds'] for r in rows),
                frames_per_second_median=statistics.median(r['frames_per_second'] for r in rows),
                mib_per_second_median=statistics.median(r['mib_per_second'] for r in rows),
                candidate_alarms=[r['candidate_alarms'] for r in rows])
    chunk_invariance={}
    for policy in ('strict','resync'):
        fingerprints=[]
        for chunk in (512,4096,65536):
            rows={r['case_id']:dict(score=r['score'],alarms=r['alarms']) for r in evaluation.values() if r['policy']==policy and r['chunk_bytes']==chunk}
            fingerprints.append(benchmark.digest(rows))
        chunk_invariance[policy]=len(set(fingerprints))==1
    final=dict(status='COMPLETED',evaluation_unique_cases=108,paired_base_windows=12,
        evaluation_intervened_cases=96,chunk_sizes_are_repeated_tests_not_independent_cases=True,
        recovery=metrics,chunk_invariance=chunk_invariance,performance=performance_summary,
        memory=performance_result['memory'],api_calls=0,api_tokens=0,new_api_cost_usd=0,
        limitations=read(out/'protocol.json')['limitations'])
    write(out/'metrics.json',final)
    lines=['# バイト列復旧・反復再生の追加試験','',
        '前回のフレーム境界を保持した試験に追加して、連続バイト列の破損と復旧を測定した。公開3ファイル8,470フレームの既存ハッシュを照合し、最初の半分だけから参照値を決めた。',
        '評価前に実装・入力・正解・評価条件をハッシュで固定。評価は後半の12区間を基に未加工12ケースと人工介入96ケースを作成。512/4096/65536バイトの読み取りで同じケースを再試験した。検出器は連続バイト列と開発用参照だけを受け取り、境界・注入位置・正解は採点側に分離した。','',
        '## 復旧と検出（4096バイト読み取り）','',
        '| 人工介入 | strict 全イベント検出ケース | resync 全イベント検出ケース | strict 無変更レコード復旧 | resync 無変更レコード復旧 |',
        '|---|---:|---:|---:|---:|']
    for pattern in PATTERNS:
        a=metrics['strict']['4096'][pattern];b=metrics['resync']['4096'][pattern]
        lines.append(f"| {pattern} | {a['fully_detected_cases']}/{a['cases']} | {b['fully_detected_cases']}/{b['cases']} | {a['intact_recovered']}/{a['intact_expected']} | {b['intact_recovered']}/{b['intact_expected']} |")
    lines+=['',f'読み取りサイズ間で採点と警報位置が一致: {chunk_invariance}。','',
        '復旧は元の無変更レコードのSHA-256と出現回数の一致で採点する。破損レコードは無変更レコードの分母から除外し、削除データを復元したとは主張しない。複合ケースでは欠落・重複・ヘッダー破損の3イベントすべての位置と種類が必要。','',
        '## 未加工データの候補警報','']
    for policy in ('strict','resync'):
        row=metrics[policy]['4096']['untouched']
        lines.append(f"- {policy}: {row['cases']}区間、警報{row['alarms']}件、無変更レコード復旧{row['intact_recovered']}/{row['intact_expected']}。")
    lines+=['','これは自然異常の正解ではなく、警報0件でも正常とは断定しない。','',
        '## Windowsホストでの反復処理性能','',
        f"Python {performance_result['python']}、{performance_result['os']}。各条件3試行の中央値。コーパスは事前にメモリへ読み込み、各パスでレコード抽出・ハッシュ計算・64件の重複履歴・ID差検査を行った。各ソース/再生回で状態をリセットする。",'',
        '| 方法 | 反復係数 | 処理フレーム/試行 | 秒（中央値） | フレーム/秒（中央値） | MiB/秒（中央値） |',
        '|---|---:|---:|---:|---:|---:|']
    for policy,levels in performance_summary.items():
        for factor,row in levels.items():
            lines.append(f"| {policy} | {factor} | {row['frames_per_trial']:,} | {row['seconds_median']:.4f} | {row['frames_per_second_median']:,.0f} | {row['mib_per_second_median']:.2f} |")
    lines+=['','繰り返しは同じ8,470フレーム。100倍再生も847,000件の独立データや実故障ではない。I/O・ネットワーク・AWS・実時間DAQの性能を示す値ではない。','',
        '## メモリ（時間測定とは別試行）','']
    for row in performance_result['memory']:
        lines.append(f"- {row['policy']} / {row['repeat_factor']}倍: Python追跡ピーク {row['python_traced_peak_bytes']:,}バイト。")
    lines+=['','tracemalloc開始前に読み込んだコーパスとプロセス全体のRSSは含まない。処理器の追加Python割当だけを測っており、全体メモリ使用量とは呼ばない。','',
        '## 申請への使い方と限界','',
        '申請には、この実測値を「ローカルで再現可能な監視・復旧の予備検証」として使用できる。AI診断の前段に必要なデータ整合性監視について、破損後に継続できる範囲と処理コストを定量化した。',
        'AWSクレジットによる今後の課題は、独立runと専門家確認済み故障の収集、曖昧・欠落・矛盾する文脈に対する診断、クラウド上の並列処理・実運用I/Oの測定である。今回AWSを必要とした／AWSでこの速度を達成したとは主張しない。',
        '前回のAI結果は維持しており、AIの優位性は未確認。今回API呼出し・トークン・追加API費用は0。AWS申請のSubmitは実行していない。','']
    lines += ['- '+limitation for limitation in final['limitations']]
    (out/'RESULTS-ja.md').write_bytes(('\n'.join(lines)+'\n').encode())
    print(json.dumps(dict(status='COMPLETED',chunk_invariance=chunk_invariance,performance=performance_summary),indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('prepare','development','evaluate','performance','report'))
    p.add_argument('--data',type=Path,default=Path('.local/raris'))
    p.add_argument('--output',type=Path,default=ROOT/'results/recovery-v1')
    a=p.parse_args()
    if a.command=='prepare':prepare(a.data,a.output)
    elif a.command=='development':evaluate(a.output,'development')
    elif a.command=='evaluate':evaluate(a.output,'evaluation')
    elif a.command=='performance':performance(a.data,a.output)
    else:report(a.output)

if __name__=='__main__':main()

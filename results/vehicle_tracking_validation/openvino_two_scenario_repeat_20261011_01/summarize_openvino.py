#!/usr/bin/env python3
"""Describe the completed OpenVINO study without changing frozen verdicts."""

import hashlib
import json
import copy
from collections import Counter
from pathlib import Path


BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]
BASELINE = ROOT / 'results/vehicle_tracking_validation/two_scenario_frozen_repeat_20261011_01'
PILOT = ROOT / 'results/vehicle_tracking_validation/openvino_pilot_20261011_01'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def fmt(value, scale=1):
    return 'N/A' if value is None else f'{value * scale:.3f}'


def main():
    current, baseline = read(BATCH / 'SUMMARY.json'), read(BASELINE / 'SUMMARY.json')
    check = read(BATCH / 'INDEPENDENT_CHECK.json')
    gate = read(PILOT / 'PILOT_GATE.json')
    protocol = read(BATCH / 'batch_protocol.json')
    old_protocol = read(BASELINE / 'batch_protocol.json')
    shared_parameters = []
    for directory in (BASELINE, BATCH):
        parameters = copy.deepcopy(read(directory / 'freeze_manifest.json')['declared_parameters'])
        for key in ('detector_backend', 'backend_artifacts'):
            parameters['perception_node'].pop(key, None)
        shared_parameters.append(parameters)
    if protocol['model_sha256'] != old_protocol['model_sha256'] or shared_parameters[0] != shared_parameters[1]:
        raise RuntimeError('The baseline differs in weights or declared non-backend parameters.')
    if not current['batch_complete'] or current['attempted'] != 20 or not check['check_passed']:
        raise RuntimeError('All twenty attempts and the independent evidence check must complete first.')
    if not gate['passed'] or protocol['passed_pilot_audit_sha256'] != gate['batch_audit_sha256']:
        raise RuntimeError('The recorded pilot promotion gate is not intact.')
    trials = current['trials']
    actual_backends, actual_threads = Counter(), Counter()
    for trial in trials:
        for line in (BATCH / trial['name'] / 'association.jsonl').read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                actual_backends[str(row.get('detector_backend'))] += 1
                actual_threads[str(row.get('cpu_inference_threads_actual'))] += 1
    if set(actual_backends) != {'openvino'} or set(actual_threads) != {'8'}:
        raise RuntimeError(f'Unexpected actual backend/threads: {actual_backends}, {actual_threads}')
    fields = [
        ('coverage_percent', '确认覆盖率 (%)', 1),
        ('full_frame_yolo_mean_s', '全图检测耗时 (ms)', 1000),
        ('processing_mean_s', '完整感知处理耗时 (ms)', 1000),
        ('target_publish_age_mean_s', '发布帧龄 (ms)', 1000),
        ('target_publish_age_p95_s', '逐试次发布帧龄 P95 (ms)', 1000),
        ('track_mean_abs_pixel_error', '横向像素误差 (px)', 1),
        ('unplanned_losses', '非计划丢失次数', 1),
        ('unplanned_recovery_max_s', '非计划最长恢复 (s)', 1),
        ('planned_recovery_max_s', '计划遮挡最长恢复 (s)', 1),
    ]
    text = [
        '# OpenVINO 两场景各十次闭环补充验证', '',
        '## 实验门槛与边界', '',
        '先完成 FP32 离线数值一致性检查，再完成一次独立后方变道回中闭环。单次严格联合验收和安全门槛均通过后，才启动本批 20 次；单次不计入批量分母。', '',
        '- 离线检查：54 张原图、108 组全图/裁剪对照，175 个匹配框，未匹配框为 0；最大框坐标差 0.0001221 px，最大置信度差 0.000007391。',
        '- 单次：确认覆盖率 91.33%，回中后 162 帧独立原车证据，981 条场景请求全部成功，严格通过并安全落地。',
        '- 使用相同 YOLO11s 原始权重，OpenVINO CPU FP32，无量化；全图 544×960、ROI 640×640，实际 8 推理线程。ByteTrack、目标锁、控制器、场景参数和验收阈值不变。',
        '- 两种同外观红车场景交替、无 GUI、独立重启各十次；车速 0.8 m/s，计划遮挡 4 仿真秒，保留 10 墙钟秒盲跟限制。未替换失败试次。',
        '- 导出模型、解释器、软件版本、源代码、安装文件和评测脚本已冻结；本报告只读取结果，不调整验收规则。', '',
        f"运行环境：Python 3.12.3，OpenVINO {protocol['backend_runtime']['packages']['openvino']}，Ultralytics {protocol['backend_runtime']['packages']['ultralytics']}。批次从 2026-10-11 跨午夜运行至 2026-10-12，目录日期表示启动日。", '',
        '## 本批结果', '',
        '| 指标 | 左侧超车 | 后方变道超车再回中 |',
        '| --- | ---: | ---: |',
    ]
    groups = ('left_overtaking', 'lane_change')
    for field, label in (('task_passed', '任务通过'), ('identity_verified', '独立身份通过'),
                         ('strict_joint_passed', '严格联合通过')):
        text.append(f'| {label} | ' + ' | '.join(f"{current['groups'][g][field]}/10" for g in groups) + ' |')
    for key, label, scale in fields:
        cells = []
        for group in groups:
            metric = current['groups'][group]['metrics'][key]
            cells.append(f"{fmt(metric['mean'], scale)} ± {fmt(metric['sample_std'], scale)}；最差 {fmt(metric['worst'], scale)}；n={metric['count']}")
        text.append(f'| {label} | ' + ' | '.join(cells) + ' |')
    text += ['', '数值为跨试次均值 ± 样本标准差；最差覆盖率取最小值，其余取最大值。没有非计划丢失的试次恢复耗时为 N/A，不以 0 秒填充。覆盖率不是检测 mAP，也不是独立身份准确率。', '',
             '计划遮挡恢复耗时描述所有记录到的遮挡事件，包括入口前提不满足的事件；耗时可测不等于该事件验收通过。各试次完整统计及恢复删失计数以严格报告为准。', '',
             f"已核对 {sum(actual_backends.values())} 条关联记录，全部实际使用 OpenVINO、8 推理线程，没有 Torch 回退记录。", '',
             f"共记录 {check['total_native_requests_recorded']} 条原生场景请求，确认失败 {check['total_native_requests_failed']} 条，缺失回执 {check['total_missing_service_receipts']} 条。两者分开统计。", '',
             f"可评分错车观测 {sum(t['wrong_identity_observations'] for t in trials)}，可评分身份切换 {sum(t['scorable_identity_switches'] for t in trials)}，记录到的安全事件观测 {sum(t['safety_event_observations'] for t in trials)}，监督干预 {sum(len(t['interventions']) for t in trials)}。未观察到不等于所有帧身份可评分或实机安全保证。", '',
             '## 逐次结果及失败原因', '',
             '| 试次 | 任务 / 身份 / 严格 | 覆盖率 (%) | 非计划丢失 | 原始失败原因 |',
             '| --- | --- | ---: | ---: | --- |']
    for trial in trials:
        verdict = ' / '.join('通过' if trial[key] else '未通过' for key in ('task_passed', 'identity_verified', 'strict_joint_passed'))
        reasons = '; '.join(trial['failure_reasons']) or '无'
        text.append(f"| [{trial['name']}]({trial['name']}/batch_audit.json) | {verdict} | {fmt(trial['coverage_percent'])} | {trial['unplanned_losses']} | {reasons} |")
    failures = []
    for trial in trials:
        if trial['strict_joint_passed']:
            continue
        native_failed = []
        for filename in ('scene_service.jsonl', 'traffic_service.jsonl'):
            for line in (BATCH / trial['name'] / filename).read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if not (row.get('binding_result') is True and row.get('response_data') is True):
                    native_failed.append({key: row.get(key) for key in
                                          ('client', 'sequence', 'service', 'model_name', 'timeout_ms',
                                           'duration_s', 'binding_result', 'response_data', 'reason', 'wall_s', 'sim_s')})
        missing = {key: value['missing'] for key, value in trial['scene_requests']['client_sequences'].items()}
        occlusions = read(BATCH / trial['name'] / 'report.json').get('occlusions', [])
        entry_context = []
        invalid_entries = [panel for panel in occlusions if not panel.get('entry_locked')]
        if invalid_entries:
            for line in (BATCH / trial['name'] / 'association.jsonl').read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if any(panel['start_wall_s'] - .8 <= row['wall_s'] <= panel['start_wall_s'] + .2
                       for panel in invalid_entries):
                    entry_context.append({'wall_s': row['wall_s'], 'reason': row.get('reason'),
                                          'candidate_reasons': [{key: c.get(key) for key in
                                                                ('index', 'track_id', 'reason', 'rejection_reasons')}
                                                               for c in row.get('candidates', [])]})
        failures.append({'name': trial['name'], 'failure_reasons': trial['failure_reasons'],
                         'native_failed_requests': native_failed, 'missing_service_receipts': missing,
                         'occlusions': occlusions, 'unlocked_entry_association_context': entry_context,
                         'identity_phase_counts': trial['identity_phase_counts'],
                         'post_identity_frames': trial['post_identity_frames']})
    text += ['', '### 未通过试次的原生请求与身份证据', '']
    if not failures:
        text.append('本批没有严格未通过试次。')
    for failure in failures:
        text.append(f"- `{failure['name']}`：超车后（变道场景为回中后）原车证据 {failure['post_identity_frames']} 帧；阶段计数 `{json.dumps(failure['identity_phase_counts'], ensure_ascii=False)}`。")
        missing = {key: value for key, value in failure['missing_service_receipts'].items() if value}
        if missing:
            text.append(f"  缺失回执序号 `{json.dumps(missing, ensure_ascii=False)}`；这里只能确认日志缺失，不能推断这些请求是否成功。")
        for request in failure['native_failed_requests']:
            model_name = request['model_name'] or '(未记录)'
            text.append(f"  `{request['client']}` 序号 {request['sequence']}，`{request['service']}`，模型 `{model_name}`；预算 {request['timeout_ms']} ms，实际 {fmt(request['duration_s'], 1000)} ms，binding={request['binding_result']}，response={request['response_data']}，原因 `{request['reason']}`。")
        for panel in failure['occlusions']:
            if not panel.get('entry_locked'):
                text.append(f"  计划遮挡在记录器 {fmt(panel['start_wall_s'])} s 开始，但入口 `entry_locked=false`，未满足当时目标可见且连续三帧确认的前提；结束后确认恢复 {fmt(panel.get('confirmed_recovery_s'))} s。恢复快不能补足入口前提，保留任务失败结论。")
                context = '; '.join(f"{fmt(row['wall_s'])}s {row['reason']}" for row in failure['unlocked_entry_association_context'])
                text.append(f'  入口附近关联时间线：{context}；每个候选的拒绝原因见 `OPENVINO_COMPARISON.json`。')
    text += ['', '场景回执缺失意味着证据链不完整，不等同于请求执行失败；请求执行超时须以原生客户端日志为准。身份未验证须检查跟踪窗口是否覆盖完整回中阶段，不以 RETURN 后车流完成替代。所有这些情形均保持原始严格结论。', '',
             '## 与此前 Torch 二十次的观察性对照', '',
             '两个批次不是同时间交叉随机化后端消融。相同核心源码、权重和场景协议不排除主机负载、仿真速率、PX4 持久校准状态和检测时序差异；下表只能描述本机本协议的结果，不能归因所有变化于 OpenVINO。', '',
             '| 场景 / 指标 | Torch | OpenVINO | 差值 OpenVINO−Torch |',
             '| --- | ---: | ---: | ---: |']
    comparisons = {}
    for group in groups:
        comparisons[group] = {}
        for key, label, scale in fields:
            before = baseline['groups'][group]['metrics'][key]['mean']
            after = current['groups'][group]['metrics'][key]['mean']
            delta = None if before is None or after is None else after - before
            comparisons[group][key] = {'torch': before, 'openvino': after, 'difference': delta}
            text.append(f'| {group} / {label} | {fmt(before, scale)} | {fmt(after, scale)} | {fmt(delta, scale)} |')
        text.append(f"| {group} / 严格通过 | {baseline['groups'][group]['strict_joint_passed']}/10 | {current['groups'][group]['strict_joint_passed']}/10 | 不作为耗时差值 |")
    text += ['', '## 证据与复现', '',
             f"PX4 持久状态未逐次强制清空：二十份日志中，{current['px4_parameter_audit']['runs_with_calibration_differences']} 次与首轮校准不同、{current['px4_parameter_audit']['runs_with_bookkeeping_differences']} 次有计数参数差异，其他参数差异 {current['px4_parameter_audit']['runs_with_other_parameter_differences']} 次。此边界不能从比较中忽略。", '',
             f"独立检查通过 {check['checks_count']} 项，重新计算试次数、汇总统计、身份阶段、请求序列、原始日志哈希及 ULog 安全计数。检查不覆盖或改写失败结论。", '',
             '- [严格审计报告](FINAL_REPORT.md)、[逐次数据](trials.csv)、[机器汇总](SUMMARY.json)、[独立核查](INDEPENDENT_CHECK.json)。',
             '- [冻结协议](batch_protocol.json)、[试次计划](plan.json)、[冻结清单](freeze_manifest.json)、各试次 `attempts/`、原图、关联记录、身份观测、场景回执和 `flight.ulg`。',
             '- [单次准入](../openvino_pilot_20261011_01/PILOT_GATE.json)、[单次审计](../openvino_pilot_20261011_01/lane_change_pilot/batch_audit.json)、[离线一致性](../openvino_equivalence_20261011_01/report.json)。',
             '- [此前 Torch 报告](../two_scenario_frozen_repeat_20261011_01/FINAL_REPORT.md)保持原样，不混计两批样本。', '']
    text += ['在项目根目录只读复核并重新生成补充报告：', '', '```bash',
             '.venv-yolo/bin/python results/vehicle_tracking_validation/openvino_two_scenario_repeat_20261011_01/independent_check.py',
             '.venv-yolo/bin/python results/vehicle_tracking_validation/openvino_two_scenario_repeat_20261011_01/summarize_openvino.py',
             '```', '',
             '复核复用原 Torch 批次的独立检查脚本，但从本批冻结快照加载身份评测器；检查脚本与调用包装的哈希均记录在输出中。只更新补充分析产物，不覆盖任务日志或冻结验收结论。', '']
    output = {'comparison': comparisons, 'failed_trials': failures, 'pilot_passed': gate['passed'],
              'same_weight_and_declared_nonbackend_parameters': True,
              'actual_backend_counts': dict(actual_backends), 'actual_inference_thread_counts': dict(actual_threads),
              'independent_check_passed': check['check_passed'], 'backend_runtime': protocol['backend_runtime'],
              'input_sha256': {str(path.relative_to(ROOT)): sha(path) for path in
                               (BATCH / 'SUMMARY.json', BASELINE / 'SUMMARY.json', BATCH / 'INDEPENDENT_CHECK.json',
                                PILOT / 'PILOT_GATE.json', BATCH / 'batch_protocol.json', BASELINE / 'batch_protocol.json',
                                BATCH / 'freeze_manifest.json', BASELINE / 'freeze_manifest.json')},
              'script_sha256': sha(Path(__file__))}
    (BATCH / 'OPENVINO_COMPARISON.json').write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
    (BATCH / 'RESULTS.md').write_text('\n'.join(text))
    print(json.dumps({'report': str(BATCH / 'RESULTS.md'), 'planned': 20, 'attempted': current['attempted']}))


if __name__ == '__main__':
    main()

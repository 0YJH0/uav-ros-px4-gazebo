#!/usr/bin/env python3
"""Supplemental read-only diagnostics; never change frozen acceptance verdicts."""

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
BATCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BATCH / 'frozen_files/scripts'))
from vehicle_crossing_validation import evaluate_identity


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def records(path):
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def stamp(row):
    return row['stamp']['sec'], row['stamp']['nanosec']


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def summarize_trial(trial):
    audit = read(trial / 'batch_audit.json')
    sources = ('batch_audit.json', 'report.json', 'association.jsonl', 'identity_observations.jsonl',
               'scene_service.jsonl', 'traffic_service.jsonl')
    if trial.name == 'lane_change_10':
        sources += ('samples.jsonl', 'crossing_events.jsonl', 'identity_poses.jsonl')
    hashes = {name: digest(trial / name) for name in sources if (trial / name).is_file()}
    cached = trial / 'failure_diagnostics.json'
    script_hash = digest(Path(__file__))
    if cached.is_file():
        old = read(cached)
        if old.get('input_sha256') == hashes and old.get('diagnostic_script_sha256') == script_hash:
            return old
    associations = records(trial / 'association.jsonl')
    report = read(trial / 'report.json')
    truth = {stamp(row): row for row in records(trial / 'identity_observations.jsonl')}
    services = records(trial / 'scene_service.jsonl') + records(trial / 'traffic_service.jsonl')
    failed_services = []
    for row in services:
        if row.get('success') is True:
            continue
        later = [item for item in services if item.get('client') == row.get('client')
                 and item.get('sequence', 0) > row.get('sequence', 0)
                 and item.get('payload_sha256') == row.get('payload_sha256')]
        retry = next((item for item in later if item.get('success') is True), None)
        failed_services.append({**row, 'same_payload_later_success_sequence': retry.get('sequence') if retry else None,
                                'same_payload_later_success_duration_s': retry.get('duration_s') if retry else None,
                                'category': 'startup_create_unconfirmed' if row.get('service', '').endswith('/create')
                                            else 'motion_pose_unconfirmed' if row.get('service', '').endswith('/set_pose')
                                            else 'other_service_unconfirmed'})
    episodes = []
    for episode in audit.get('recovery_episodes', []):
        start = episode['loss_wall_s']
        end = episode.get('confirmation_wall_s')
        if end is None:
            end = start + (episode.get('censor_lower_bound_s') or 0)
        context = [row for row in associations if start - 1.5 <= row['wall_s'] <= end + .25]
        rows, correct_rejections = [], Counter()
        for row in context:
            matched = truth.get(stamp(row))
            correct = []
            for candidate in row.get('candidates', []):
                if not matched or not matched.get('projected_boxes'):
                    continue
                evidence = evaluate_identity(candidate.get('bbox'), matched['projected_boxes'])
                if evidence['label'] != 'tracked_vehicle':
                    continue
                item = {key: candidate.get(key) for key in (
                    'index', 'track_id', 'accepted', 'confidence', 'reason', 'rejection_reasons',
                    'center_error', 'center_gate', 'log_scale_error', 'log_scale_gate',
                    'appearance_similarity', 'mahalanobis_distance', 'mahalanobis_gate',
                    'predicted_size_px', 'bbox', 'vertical_truncated')}
                correct.append(item)
                if start <= row['wall_s'] <= end and not item['accepted']:
                    correct_rejections.update(item.get('rejection_reasons') or [item.get('reason')])
            motion = row.get('camera_motion', {})
            rows.append({'wall_s': row['wall_s'], 'stamp': row['stamp'],
                         'identity_confirmed': row.get('identity_confirmed'),
                         'onboard_reason': row.get('reason'),
                         'independent_label': matched.get('label') if matched else 'missing_stamp_match',
                         'candidate_count': len(row.get('candidates', [])),
                         'candidate_summaries': [{key: candidate.get(key) for key in (
                             'track_id', 'bbox', 'reason', 'rejection_reasons', 'confirmation_count',
                             'confirmation_required', 'overlap_confirmation_preserved')}
                             for candidate in row.get('candidates', [])],
                         'independently_supported_target_candidates': correct,
                         'gmc_reason': motion.get('reason'), 'gmc_quality': motion.get('quality'),
                         'gmc_warp_px': motion.get('warp_px'),
                         'processing_s': row.get('processing_s'),
                         'target_publish_age_s': row.get('target_publish_age_s'),
                         'roi_yolo_s': row.get('detector', {}).get('roi_yolo_s')})
        window = [row for row in rows if start <= row['wall_s'] <= end]
        correct_frames = sum(bool(row['independently_supported_target_candidates']) for row in window)
        rejected_correct_frames = sum(any(not item['accepted'] for item in row['independently_supported_target_candidates'])
                                      for row in window)
        panel = next((item for item in report.get('occlusions', [])
                      if item.get('end_wall_s') is not None and item['start_wall_s'] <= start <= item['end_wall_s']), None)
        episodes.append({**episode, 'association_frames_in_task_loss': len(window),
            'panel_start_wall_s': panel['start_wall_s'] if panel else None,
            'panel_end_wall_s': panel['end_wall_s'] if panel else None,
            'panel_end_to_confirmed_recovery_s': panel.get('confirmed_recovery_s') if panel else None,
            'frames_with_independent_target_candidate': correct_frames,
            'frames_with_rejected_independent_target_candidate': rejected_correct_frames,
            'correct_candidate_rejection_reason_counts': dict(correct_rejections),
            'onboard_reason_counts': dict(Counter(row['onboard_reason'] for row in window)),
            'gmc_reason_counts': dict(Counter(str(row['gmc_reason']) for row in window)),
            'no_candidate_frames': sum(row['candidate_count'] == 0 for row in window),
            'context_start_wall_s': start - 1.5, 'context_end_wall_s': end + .25,
            'context': rows})
    result = {'name': trial.name, 'group': audit['group'], 'strict_joint_passed': audit['strict_joint_passed'],
              'task_passed': audit['task_passed'], 'identity_verified': audit['identity_verified'],
              'coverage_percent': audit['coverage_percent'], 'failure_reasons': audit['failure_reasons'],
              'failed_services': failed_services, 'recovery_episodes': episodes,
              'service_receipt_integrity': audit.get('scene_requests', {}).get('client_sequences', {}),
              'recorded_service_count': audit.get('scene_requests', {}).get('total'),
              'all_association_reason_counts': dict(Counter(row.get('reason') for row in associations)),
              'all_candidate_rejection_counts': dict(Counter(reason for row in associations for candidate in row.get('candidates', [])
                                                    for reason in candidate.get('rejection_reasons', []))),
              'all_association_gmc_quality_counts': dict(Counter(str(row.get('camera_motion', {}).get('quality', {}).get('reason'))
                                                               for row in associations)),
              'input_sha256': hashes, 'diagnostic_script_sha256': script_hash}
    if trial.name == 'lane_change_10':
        samples = records(trial / 'samples.jsonl')
        last_track = [row for row in samples if row.get('state') == 'TRACK'][-1]
        first_ahead = next(row for row in samples
                           if (row.get('vehicle_ground_truth') or {}).get('motion_time', 0) >= 57.)
        last_identity = max(truth.values(), key=lambda row: row['sim_s'])
        matching_association = next(row for row in associations if stamp(row) == stamp(last_identity))
        completed = next(row for row in records(trial / 'crossing_events.jsonl')
                         if row['event'] == 'lane_change_overtaking_completed')
        pose = min(records(trial / 'identity_poses.jsonl'), key=lambda row: abs(row['sim_s'] - completed['sim_s']))
        result['identity_window_evidence'] = {
            'follow_wall_time_s': report['follow_wall_time_s'],
            'return_recorder_wall_s': next(row['time_s'] for row in report['transitions'] if row['state'] == 'RETURN'),
            'last_track_sample': {key: last_track[key] for key in ('wall_s', 'state', 'vehicle_ground_truth')},
            'first_motion_57_sample': {key: first_ahead[key] for key in ('wall_s', 'state', 'vehicle_ground_truth')},
            'last_identity': {key: last_identity[key] for key in ('stamp', 'sim_s', 'motion_time', 'wall_s', 'phase', 'label')},
            'last_identity_same_stamp_recorder_wall_s': matching_association['wall_s'],
            'traffic_completed_event': completed, 'pose_near_completion': pose,
            'observer_filter': 'association() only accepts SEARCH, DETECT, APPROACH, TRACK, RECOVER; RETURN is excluded.',
            'clock_warning': 'Recorder wall_s and identity/traffic observer wall_s use different origins; do not subtract them directly.',
        }
    write(cached, result)
    return result


def main():
    frozen = read(BATCH / 'freeze_manifest.json')
    identity_script = 'scripts/vehicle_crossing_validation.py'
    if digest(BATCH / 'frozen_files' / identity_script) != frozen['source_sha256'][identity_script]:
        raise RuntimeError('Frozen identity evaluator changed')
    trials = []
    for item in read(BATCH / 'plan.json'):
        trial = BATCH / item['name']
        attempt = BATCH / 'attempts' / (item['name'] + '.json')
        if not attempt.is_file() or read(attempt).get('state') != 'completed':
            continue
        if not (trial / 'batch_audit.json').is_file():
            continue
        trials.append(summarize_trial(trial))
    result = {'completed_trials_analyzed': len(trials), 'trials': trials,
              'diagnostic_script_sha256': digest(Path(__file__)),
              'limitations': [
                  'Supplemental post-hoc diagnosis, never used to change frozen trial verdicts.',
                  'Candidate identity uses timestamp-matched frozen v2 projected-volume evidence, not pixels or online ground truth.',
                  'Counts refer to candidate rejection reasons and may count multiple reasons per candidate, not unique missed frames.',
                  'A native timeout means no confirmed receipt, not proof the server never performed the request.',
                  'GMC/latency changes are observed associations, not isolated causal ablations.',
                  'Context starts 1.5 wall seconds before the task loss to retain the triggering visual gap.',
                  'No candidate or no independently supported candidate is not automatically a detector false negative: occlusion, truncation and projection ambiguity remain possible.',
              ]}
    write(BATCH / 'FAILURE_ANALYSIS.json', result)
    lines = ['# 批量实验失败与恢复问题分析', '',
             f'已分析 {len(trials)} 次结束的实验。本报告是事后诊断，不更改预先冻结的验收标准、原始日志或成功率分母。', '',
             '## 结论边界', '',
             '任务成功、独立身份证据通过和严格联合验收不是同一个指标。启动阶段的一次场景请求超时，'
             '即使重试成功且完成正常跟踪，也会使“所有原生请求成功”的严格条件失败。'
             '这类失败须保留，但不能等同为跟踪算法失败。', '',
             '计划遮挡的“总丢失时长”从任务发出 TRACK_TARGET_LOST 开始；'
             '“遮挡结束后恢复时长”从挡板移开开始。两者均为墙钟秒，与设定的 4 秒仿真遮挡时长不同，不能混用。', '',
             '## 场景请求可靠性', '',
             '以下区分启动创建请求和运动阶段 set_pose 请求。后续相同载荷重试成功，不会抹除首次失败。'
             'native binding/response 未获确认只说明客户端未收到成功回执，不能证明服务端从未执行该请求。', '',
             '| 实验 | 客户端 / 序号 | 请求 | 耗时/秒 | 后续相同载荷成功序号 |',
             '|---|---|---|---:|---|']
    for trial in trials:
        for failure in trial['failed_services']:
            lines.append(f"| {trial['name']} | {failure.get('client')} / {failure.get('sequence')} | "
                         f"{failure.get('service')} | {failure.get('duration_s'):.4f} | "
                         f"{failure['same_payload_later_success_sequence']} |")
    lines += ['', '### 回执完整性与真实请求失败分开统计', '',
              '| 实验 | 客户端 | 实际记录数 | 首/末序号 | 缺失序号 | 重复序号 |',
              '|---|---|---:|---|---|---|']
    for trial in trials:
        for client, sequence in trial['service_receipt_integrity'].items():
            if sequence.get('complete_from_one'):
                continue
            lines.append(f"| {trial['name']} | {client} | {sequence['count']} | "
                         f"{sequence['first']} / {sequence['last']} | {sequence['missing']} | {sequence['duplicates']} |")
    lines += ['', '缺失回执的原始成功/失败状态未知。不能把它们计为已知失败请求，也不能把记录到的零失败扩展为所有请求成功。']
    lines += ['', '## 每次任务丢失与恢复', '',
              '| 实验 | 计划遮挡内丢失 | 丢失墙钟时刻/秒 | 丢失至确认/秒 | 遮挡结束至确认/秒 | 未恢复 | 正确候选拒绝原因 |',
              '|---|---|---:|---:|---:|---|---|']
    for trial in trials:
        for episode in trial['recovery_episodes']:
            duration = f"{episode['duration_s']:.3f}" if episode['duration_s'] is not None else 'N/A'
            after_panel = (f"{episode['panel_end_to_confirmed_recovery_s']:.3f}"
                           if episode['panel_end_to_confirmed_recovery_s'] is not None else '不适用')
            reasons = ', '.join(f'{key}: {value}' for key, value in episode['correct_candidate_rejection_reason_counts'].items())
            lines.append(f"| {trial['name']} | {episode['planned_occlusion']} | {episode['loss_wall_s']:.3f} | "
                         f"{duration} | {after_panel} | {episode['censored']} | {reasons or '无独立可评分的拒绝'} |")
    lines += ['', '## 关键归因', '']
    for trial in trials:
        if trial['name'] == 'left_overtaking_01' and trial['failed_services']:
            failure = trial['failed_services'][0]
            lines += ['### 左侧超车第 1 轮：启动建路请求未获确认', '',
                      f"唯一原生失败请求为 scene 序号 {failure['sequence']} 的 create，"
                      f"耗时 {failure['duration_s'] * 1000:.2f} ms，预算 {failure['timeout_ms']} ms。"
                      f"后续同载荷序号 {failure['same_payload_later_success_sequence']} 重试成功。"
                      '冻结场景代码 pending[0] 为道路，因此这是首次建路阶段的启动可靠性问题，'
                      '不是车辆运动过程中持续 set_pose 失败。本轮任务与身份证据通过，严格联合验收仍保留失败。', '']
        if trial['name'] == 'left_overtaking_04':
            sequence = trial['service_receipt_integrity'].get('scene', {})
            if sequence.get('missing') == [1, 2, 3, 4]:
                lines += ['### 左侧超车第 4 轮：启动回执证据缺口', '',
                          f"scene 日志从序号 5 开始，5–{sequence['last']} 连续，但最初四个 create 回执未留存。"
                          '它们对应道路、原车、路边车和挡板初始化；已记录的原生请求没有失败。'
                          'mission.log 出现 Street and vehicles ready，结合只在 request 返回成功后移除 pending 项的代码，'
                          '可推断初始化流程完成，但这不能补造四条原始回执或替代严格审计。', '',
                          '场景回执 publisher/subscriber 使用默认 volatile 持久性，且启动未等待该订阅匹配完成，'
                          '因此现象符合启动期 DDS 匹配前回执未被 recorder 保存。四条消息远少于 depth=100，'
                          '没有证据支持“队列溢出”或“四次服务实际失败”。当前保留严格完整性失败，不在批次中修改代码。', '']
        stale = [row for episode in trial['recovery_episodes'] if not episode['planned_occlusion']
                 for row in episode['context'] if row['onboard_reason'] == 'stale_inference_result']
        if stale:
            by_stamp = {tuple(row['stamp'].values()): row for row in stale}
            ages = [row['target_publish_age_s'] for row in by_stamp.values() if row.get('target_publish_age_s') is not None]
            processing = [row['processing_s'] for row in by_stamp.values() if row.get('processing_s') is not None]
            lines += [f"### {trial['name']}：完整感知链路时效波动", '',
                      f'非计划恢复上下文出现 {len(by_stamp)} 个去重的 stale_inference_result 帧。'
                      f'观测发布时间龄范围 {min(ages):.3f}–{max(ages):.3f} 秒，'
                      f'处理耗时范围 {min(processing):.3f}–{max(processing):.3f} 秒。'
                      '冻结系统保留 0.5 秒图像处理时效限制；过期结果被主动拒绝，随后需要重新积累确认。'
                      '这是实时性保护与实际计算波动的影响，不能归为 YOLO 完全看不见目标。', '']
        if trial['name'] == 'lane_change_06':
            lines += ['### 变道回中第 6 轮：重叠框形态抖动', '',
                      '169.245 秒开始的非计划恢复持续约 2.400 秒。原轨迹 ID 14 没有切换，'
                      '但候选框宽度约 94 px 时，高度在约 79–111 px 间交替；'
                      '同一 ID 的三帧确认计数多次重新从 1 累积。冻结连续确认还要求几何一致性，'
                      '因此保留 ID 本身不保证证据连续。多帧独立投影标签为 overlap_unscorable，'
                      '符合正常车身框与包含两车投影的大框交替的现象，不能把这些候选全部判定为正确原车。', '',
                      '这与单纯切换重叠模式后无条件清空确认不同；当前修复保留兼容证据，'
                      '并未消除真实框形态变化带来的安全重确认。后续改进空间在分离重叠实例和提高框稳定性，'
                      '不能用统一放宽所有关联门限或宣称不可评分大框身份正确来消除统计损失。', '']
        if trial.get('identity_window_evidence'):
            window = trial['identity_window_evidence']
            last = window['last_identity']
            gt = window['last_track_sample']['vehicle_ground_truth']
            ahead = window['first_motion_57_sample']
            lines += ['### 变道回中第 10 轮：任务墙钟窗口早于场景仿真阶段结束', '',
                      f"本轮覆盖率 {trial['coverage_percent']:.2f}%，任务通过，但身份与严格联合验收不通过。"
                      f"跟随窗口为 {window['follow_wall_time_s']:.3f} 墙钟秒，"
                      f"RETURN 出现在 recorder 墙钟 {window['return_recorder_wall_s']:.3f} 秒。"
                      f"最后 TRACK 样本中的车辆运动时长仅 {gt['motion_time']:.1f} 仿真秒；"
                      f"最后独立身份图像在 sim={last['sim_s']:.3f} 秒、motion={last['motion_time']:.1f} 秒，"
                      '尚未达到 57 仿真秒的 ahead_follow 阶段。', '',
                      f"同一 recorder 时钟下，首次记录 motion=57 的样本在 {ahead['wall_s']:.3f} 秒，"
                      f"状态已经是 {ahead['state']}。traffic 节点在返航后继续更新车辆，"
                      f"因此稍后 sim={window['traffic_completed_event']['sim_s']:.3f} 秒确实发出了场景完成事件，"
                      '完整 pose 流也保留了车已回中且在前方的位姿。然而身份 observer 的 association() '
                      '明确排除 RETURN 状态，返航后的图像不再进入身份证据窗口。', '',
                      '所以 traffic_completed=True 与 post={} 并不矛盾：场景后来完成，但本次有效跟踪观测窗口没有覆盖回中后的确认。'
                      '这不是“已经回中后一直认不出原车”，也不是已观察到错车；'
                      '末帧仍被独立确认为 tracked_vehicle，已记录观测的 truth 匹配比例为 1.0。'
                      '仿真推进慢于墙钟，使固定墙钟跟踪任务与仿真时间驱动的交通阶段脱节。'
                      '本批不修改观察窗口，也不把完成事件替代缺失的至少 10 帧 post 原车证据。', '',
                      '注意 crossing_events 与 recorder 的 wall_s 原点不同；上文时间顺序依据同一个 samples.jsonl '
                      '及图像 stamp、sim_s 对齐，不直接相减两个节点的墙钟相对值。', '']
        for episode in trial['recovery_episodes']:
            if episode['planned_occlusion'] or (episode['duration_s'] is not None and episode['duration_s'] < 2):
                continue
            reasons = episode['correct_candidate_rejection_reason_counts']
            correct = [item for row in episode['context'] for item in row['independently_supported_target_candidates']
                       if not item['accepted']]
            unavailable = [row for row in episode['context'] if not row['identity_confirmed']
                           and row['gmc_reason'] != 'applied']
            quality = dict(Counter(row.get('gmc_quality', {}).get('reason', 'unknown') for row in unavailable))
            lines += [f"### {trial['name']}：{episode['loss_wall_s']:.3f} 秒开始的非计划恢复", '',
                      f"总恢复耗时 {episode['duration_s']} 秒；任务丢失窗口共 {episode['association_frames_in_task_loss']} 个关联帧，"
                      f"其中 {episode['frames_with_independent_target_candidate']} 帧存在独立投影支持的原车候选，"
                      f"{episode['frames_with_rejected_independent_target_candidate']} 帧的正确候选未被接受。"
                      f"拒绝原因统计：{reasons}。"]
            if reasons.get('center_gate') and not reasons.get('scale_gate'):
                lines.append('可评分正确候选主要被中心位置关联条件拒绝，而不是尺度门限。'
                             '这说明不能把本段恢复概括为 YOLO 一直没有检测到原车，也不能归为修复前的尺度预测发散。')
            if quality:
                lines.append(f'恢复及其前 1.5 秒上下文内，相机运动补偿不可用原因：{quality}。'
                             '这与后续中心预测失配在时间上相关，但日志关联本身不是单变量因果证明。')
            if correct:
                scales = [item['log_scale_error'] for item in correct if item.get('log_scale_error') is not None]
                centers = [item['center_error'] for item in correct if item.get('center_error') is not None]
                lines.append(f'上下文内被拒的正确候选中心误差范围 {min(centers):.4f}–{max(centers):.4f}（归一化坐标），'
                             f'对数尺度误差范围 {min(scales):.4f}–{max(scales):.4f}；'
                             '每帧实际门限、预测宽高、GMC 质量和推理延时均保留在 JSON 中。')
            lines.append('')
    lines += ['', '## 解释限制', '',
              '- 身份诊断沿用冻结的 v2 投影体积证据，同图像时间戳匹配；没有向在线控制器输入仿真真值。',
              '- 拒绝原因按候选计数，同一候选可以同时违反多个条件；不是独立漏检帧数量。',
              '- 无候选或无可评分原车候选，不自动等同为 YOLO 漏检：真实遮挡、截断和投影歧义仍可能存在。',
              '- 不可评分帧不能假定跟对；错车为零只适用于可评分观测。',
              '- GMC 和时延变化只说明日志中的时间关联，没有通过新增消融实验证明唯一因果。',
              '- 没有恢复的事件保留为未恢复及已观察时长下界，不填入零秒或当作成功。',
              '', '完整逐帧候选、补偿矩阵、预测尺度和时延见 [FAILURE_ANALYSIS.json](FAILURE_ANALYSIS.json) '
              '及每轮 `failure_diagnostics.json`。', '']
    (BATCH / 'FAILURE_ANALYSIS.md').write_text('\n'.join(lines))
    print(json.dumps({'analyzed': len(trials), 'service_failures': sum(len(row['failed_services']) for row in trials),
                      'unplanned_episodes': sum(not ep['planned_occlusion'] for row in trials for ep in row['recovery_episodes'])}))


if __name__ == '__main__':
    main()

"""Re-run ASR for all rows reusing existing TTS audio.

Uses the strict ASR prompt configured in xiaomi_api_config.json.
On refusal / empty output, falls back to mimo-v2-omni.
"""
import base64, json, os, sys
from pathlib import Path
import pandas as pd, requests

sys.path.insert(0, 'PROJECT_ROOT_PLACEHOLDER')
from run_xiaomi_tts_asr_eval import call_asr, eval_spans

BASE = Path('PROJECT_ROOT_PLACEHOLDER')
RES = BASE / 'mvp_eval' / 'tts_asr_eval_50_results.xlsx'
CONFIG = json.loads((BASE / 'xiaomi_api_config.json').read_text(encoding='utf-8'))
URL = 'https://token-plan-cn.xiaomimimo.com/v1/chat/completions'
KEY = os.environ['MIMO_API_KEY']

REFUSAL = [
 '您发送','不是音频文件','无法转写','抱歉，我无法','我无法接收','无法播放音频',
 '您好，这里有几点','请提供音频文件','建议使用专业的语音转文字','希望我根据您提供',
 '我很乐意帮忙','直接转写音频内容','作为一个AI','作为文本生成模型',
 '上传音频','没有附上音频','没有收到音频','并没有附带音频','请上传音频文件',
]

def bad(t):
    s = (t or '').strip()
    if not s or s.lower() == 'nan':
        return True
    return any(p in s for p in REFUSAL)

def omni_asr(audio_path):
    a = base64.b64encode(Path(audio_path).read_bytes()).decode()
    body = {
        'model': 'mimo-v2-omni',
        'messages': [{'role': 'user', 'content': [
            {'type': 'input_audio', 'input_audio': {'data': f'data:audio/wav;base64,{a}'}},
            {'type': 'text', 'text': '请逐字按发音转写以下中文音频，禁止把汉字数字写成阿拉伯数字，禁止把百分之十写成10%。只输出转写文本。'}
        ]}],
        'temperature': 0,
        'max_completion_tokens': 2048,
    }
    r = requests.post(URL, headers={'api-key': KEY, 'Content-Type': 'application/json'},
                      json=body, timeout=120, proxies={'http': None, 'https': None})
    r.raise_for_status()
    return r.json()['choices'][0]['message']['content'] or ''

def main():
    df = pd.read_excel(RES)
    df['asr_text'] = df['asr_text'].fillna('').astype(str)
    total = len(df)
    primary = 0
    fallback = 0
    still = []
    for idx, row in df.iterrows():
        audio = row['audio_path']
        if not Path(audio).exists():
            print('missing', audio); continue
        try:
            text, _ = call_asr(CONFIG, Path(audio))
        except Exception as exc:
            text = ''
            print(f'primary err [{idx+1}/{total}] {row["case_id"]} {row["pipeline"]}: {exc!r}')
        used = 'primary'
        if bad(text):
            try:
                text = omni_asr(audio)
                used = 'omni'
            except Exception as exc:
                print(f'omni err [{idx+1}/{total}] {row["case_id"]} {row["pipeline"]}: {exc!r}')
                still.append((row['case_id'], row['pipeline']))
                continue
            if bad(text):
                still.append((row['case_id'], row['pipeline']))
                print(f'still bad [{idx+1}/{total}] {row["case_id"]} {row["pipeline"]}')
                continue
            fallback += 1
        else:
            primary += 1
        spans = json.loads(row['risk_spans_json'] or '[]')
        ev = eval_spans(text, spans)
        c = sum(1 for x in ev if x['correct']); t = len(ev)
        df.at[idx, 'asr_text'] = text
        df.at[idx, 'risk_span_eval_json'] = json.dumps(ev, ensure_ascii=False)
        df.at[idx, 'risk_span_correct_count'] = c
        df.at[idx, 'risk_span_total_count'] = t
        df.at[idx, 'risk_span_audio_accuracy'] = c / t if t else 0
        df.to_excel(RES, index=False)
        if (idx + 1) % 10 == 0 or idx == total - 1:
            print(f'[{idx+1}/{total}] {row["case_id"]} {row["pipeline"]} {used} acc={c}/{t}')
    print('done primary=', primary, 'fallback=', fallback, 'still_bad=', len(still))
    if still:
        print(still)

if __name__ == '__main__':
    main()

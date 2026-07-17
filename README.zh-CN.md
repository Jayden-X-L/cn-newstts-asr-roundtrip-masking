# 中文新闻 TTS 中 ASR 回环评估的错误遮蔽研究

[English README](README.md)

本私有仓库是论文 **ASR-Roundtrip Evaluation Can Mask Context- and Convention-Dependent Reading Errors in Chinese News TTS** 的轻量级支撑材料包，用于论文投稿与复现实验说明。

这项工作的核心不是提出一个通用 TTS benchmark，而是研究一种具体的评估失效形式：在中文新闻 TTS 中，TTS 音频已经把某些上下文/行业规范依赖的文本读错了，但 ASR 回环转写可能恢复成“表面正确”的文本，从而把听感上真实存在的读法错误遮蔽为自动评估中的假阴性。

**论文 PDF:** [main.pdf](https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking/blob/main/paper/main.pdf)

## 研究问题

ASR roundtrip evaluation 通常用于低成本评估 TTS 可懂度：先合成语音，再用 ASR 转写，最后比较转写文本和参考文本。但对中文新闻中的短文本风险片段，这种方法可能误判。

典型风险片段包括：

- 比分：`13-11` 应读作“十三比十一”，而不是范围式读法。
- 飞机/装备型号：`伊尔-76` 是型号，不是负数。
- 技术单位：`640kW`、`350Wh/kg` 需要按行业约定读出。
- 会员/产品名：如 `88VIP`，错误读法可能被 ASR 规范化回正确写法。

这些错误对听众是可感知的，但 ASR 可能根据上下文、文本规范化或领域先验，把错误音频转写成预期文本。论文将这类现象称为 ASR 回环评估中的 masked false negative。

## 主要发现

- 在 110 个高风险候选样本的 audio-first targeted audit 中，确认 46 个 `confirmed masked` 案例：Raw TTS 读错，但至少一条 ASR 路径输出了预期或表面正确文本。
- 同一审计还完整报告了分母：9 个 `exposed TTS error`，55 个 `no Raw TTS error`，避免只报告阳性案例。
- span-isolation 诊断在 46 个 confirmed masked 案例中重新暴露 19 个错误，支持“句子上下文会帮助 ASR 遮蔽局部读法错误”的机制解释。
- 在同一高风险池上，用 CosyVoice 做 Raw-only 第二 TTS 验证，确认 51 个 masked cases，说明这种遮蔽现象不是单一 TTS 系统的偶然结果。
- 新增 Paraformer-zh 对照后，逐 occurrence 转写复核只在 MiMo 0/46、CosyVoice 2/51 条既有人耳确认错误中发现精确表面恢复。这说明 masking 强烈依赖 ASR 与转写协议，并非所有 ASR 都同样发生，进一步支持“不应把单一路 ASR-roundtrip 当作独立真值”的结论。
- 结论边界：110 个样本是 targeted audit yield，不是生产环境自然发生率；span-isolation 是机制诊断，不是替代评估指标。

## 仓库内容

- `paper/`: 编译后的论文 PDF 快照。
- `metadata/frozen_benchmark/`: 冻结的 200 例评估元数据，以及 Raw/Structured 输入矩阵。
- `metadata/candidate_pools/`: 500 条真实新闻候选池和 5K 合成 hard-case 候选池。
- `rules_and_schema/`: 规则、标注 schema、提示词和打分 schema 快照。
- `labels/human_200/`: 200 例 human listening audit 的匿名标注和 IAA 文件。
- `labels/targeted_audit_110/`: MiMo targeted masked-error audit 的标注和汇总表。
- `results/paper_tables/paper_assets_20260608/targeted_audit_110_blind_relabel_30_agreement_summary_20260620.md`: 30 例独立盲复标的一致性摘要。
- `labels/cosyvoice_110/`: CosyVoice Raw-only 110 例人工审计标注和汇总。
- `results/p1p2/`: 自动 TTS/ASR 结果表与协议对照。其中保留的 Edge TTS 仅是辅助自动对照，未进行 targeted human masking audit，也不进入论文核心证据链。
- `results/span_isolation/`: span-isolation manifest、ASR 输出、人工复核摘要和表格。
- `results/cosyvoice/`: CosyVoice TTS/ASR 输出和运行摘要。
- `results/paraformer/`: 清除本机/工作站绝对路径后的 Paraformer-zh manifest、266 条完整转写、逐 occurrence 转写复核表和结果摘要。
- `manifests/`: 生成与转写 manifest。
- `scripts/`: 构造样本、运行 ASR/TTS 评估、合并标注、生成审计表的脚本。
- `docs/`: 标注规范与项目评估说明。

## 不包含的内容

- 完整的 108K 原始新闻导出。
- API key 或任何 provider credentials。
- Provider 原始响应 payload，包括 response ID 和 reasoning trace。发布记录保留审计所需的最终转写、模型与协议标识、错误和耗时元数据。
- 快照备份与中间工作目录。
- 大体量生成音频文件。音频包将通过配套 Zenodo 包归档。

## 复现说明

论文中报告的 MiMo 转写由支持音频输入的 MiMo `mimo-v2.5` API 在本仓库所含 strict transcription prompt 下生成；`mimo-v2-omni` 用作 fallback 和 protocol-ablation 路线。本材料包提供 API 模型标识、prompt、协议设置、转写和评分脚本，用于审计已报告输出并重新运行 API 协议。MiMo TTS 音频通过固定设置的 MiMo-V2.5-TTS API 生成。CosyVoice、Whisper 和 Paraformer 输出来自开源组件。Paraformer 对照使用 `paraformer-zh` v2.0.4 与 FSMN-VAD v2.0.4，关闭 inverse text normalization，且不使用标点模型、热词或外部语言模型。

论文中 targeted audit yield 相关数字可从以下文件开始核对：

- `labels/targeted_audit_110/targeted_masked_error_audit_yield_review_results_final_20260612.csv`
- `results/paper_tables/paper_assets_20260608/targeted_audit_110_blind_relabel_30_agreement_summary_20260620.md`
- `results/paper_tables/paper_assets_20260608/targeted_audit_110_blind_relabel_30_agreement_20260620.csv`
- `labels/cosyvoice_110/cosyvoice_raw_110_human_review_labels_final_20260614.csv`
- `results/span_isolation/table_full_vs_rough_vs_aligned_asr_probe_20260612.md`
- `results/paraformer/paraformer_targeted_control_summary.md`
- `results/paraformer/paraformer_confirmed_97_transcript_audit.csv`

## 引用

请参见 `CITATION.cff`。

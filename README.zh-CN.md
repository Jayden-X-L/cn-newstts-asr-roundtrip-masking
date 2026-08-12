# ASR 回环评估会遮蔽中文新闻 TTS 中依赖上下文与惯例的读法错误

<div align="center">

**论文配套数据、标注、ASR 输出与评估工具**

[![arXiv](https://img.shields.io/badge/arXiv-2608.10606-b31b1b?style=for-the-badge)](https://arxiv.org/abs/2608.10606)
[![Zenodo DOI](https://img.shields.io/badge/Zenodo-10.5281%2Fzenodo.21454402-1682D4?style=for-the-badge)](https://doi.org/10.5281/zenodo.21454402)
[![Release](https://img.shields.io/badge/Release-v1.0.1-16A34A?style=for-the-badge)](https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking/releases/tag/v1.0.1)

[English README](README.md) | [论文](https://arxiv.org/abs/2608.10606) | [数据归档](https://doi.org/10.5281/zenodo.21454402) | [Release](https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking/releases/tag/v1.0.1)

</div>

---

## 研究概述

ASR 回环评估常被用作低成本的 TTS 可懂度代理。本研究发现，它会漏掉中文新闻 TTS 中一类明确的读法错误：合成音频已经把依赖上下文或行业惯例的文本读错，但 ASR 又把音频转写成预期文本或表面正确文本。

典型风险包括体育比分、飞机型号、技术单位和会员名称。对于这些读法，ASR 可以用于筛查，但不能作为独立的 ground truth。

## 核心结果

| 证据 | 结果 | 含义 |
|---|---:|---|
| MiMo 定向审计 | 46 遮蔽、9 暴露、55 个 Raw 无错（共 110） | 以完整分母证明假阴性机制存在 |
| MiMo 对齐片段隔离 | 18 暴露、12 仍遮蔽、13 无输出、3 其他（共 46） | 移除整句上下文后，部分局部错读证据重新出现 |
| CosyVoice 定向审计 | 51 遮蔽、27 暴露、30 个 Raw 无错、2 个未决（共 110） | 第二个 TTS 系统复现了该现象 |
| Qwen3-ASR-1.7B 对照 | 40/97 表面正确恢复 | MiMo 之外的 ASR 同样会发生遮蔽 |
| Paraformer-zh 对照 | 2/97 表面正确恢复 | 遮蔽强烈依赖 ASR 系统与评估协议 |
| 30 例独立盲复标 | 遮蔽 vs. 其他的 Cohen's kappa = 0.800 | 为主审计标签提供独立一致性证据 |

110 个样本是按规则构建的高风险定向审计池。这些数字表示审计产出和机制证据，不表示生产环境自然发生率。

## 发布内容

| 资源 | 位置 | 用途 |
|---|---|---|
| 冻结 200 例 benchmark | [metadata/frozen_benchmark/](metadata/frozen_benchmark/) | case metadata 与配对 Raw/Structured 条件 |
| 候选池 | [metadata/candidate_pools/](metadata/candidate_pools/) | 500 条公司授权生产新闻文稿与 5,000 条合成 hard cases |
| 风险规则与 schema | [rules_and_schema/](rules_and_schema/) | 风险 span 规则、标签、提示词和评分 schema |
| 200 例人工标注 | [labels/human_200/](labels/human_200/) | 主听评标签和 IAA 记录 |
| MiMo 110 例审计 | [labels/targeted_audit_110/](labels/targeted_audit_110/) | 完整分母 masked-error audit |
| CosyVoice 110 例审计 | [labels/cosyvoice_110/](labels/cosyvoice_110/) | Raw-only 跨 TTS 人工审计 |
| span-isolation 证据 | [results/span_isolation/](results/span_isolation/) | 切片 manifest、ASR 输出、复核标签和汇总 |
| Paraformer 对照 | [results/paraformer/](results/paraformer/) | 转写、逐 occurrence 复核和结果汇总 |
| Qwen3-ASR 对照 | [results/qwen3_asr/](results/qwen3_asr/) | 转写、逐 occurrence 复核和 full-to-aligned 对照 |
| 完整音频归档 | [Zenodo](https://doi.org/10.5281/zenodo.21454402) | 生成音频与完整归档包 |
| 论文 | [arXiv:2608.10606](https://arxiv.org/abs/2608.10606) | 方法、实验、结果与局限性 |

GitHub `v1.0.1` 是文档与自动核验更新；Zenodo 数据归档版本仍为 `v1.0.0`。

源数据池包含 108,124 条在生产 TTS 流程中使用的公司自产中文新闻文稿。完整源数据导出不对外发布；公开包包含进入真实新闻候选池的 500 条公司授权文稿和 5,000 条合成 hard cases。

## 快速核验

下面的命令不依赖第三方 Python 包，可直接从公开标签和汇总文件重算论文中的关键数字：

```bash
git clone https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking.git
cd cn-newstts-asr-roundtrip-masking
python3 scripts/verify_paper_claims.py
```

该脚本会核验 MiMo 与 CosyVoice 审计计数、span-isolation 结果、Qwen3-ASR 与 Paraformer 对照、盲复标一致性计数，以及 200 例 Raw/Structured 人评结果。

也可以在公开目录中重新生成两个 ASR 对照分析：

```bash
python3 scripts/analyze_paraformer_targeted_control_20260717.py
python3 scripts/analyze_qwen3_asr_control_20260717.py
```

## 评估协议说明

- 论文报告的 MiMo 转写由支持音频输入的 MiMo `mimo-v2.5` API 在公开 strict transcription prompt 下生成；`mimo-v2-omni` 用作 fallback 和 protocol-ablation 路线。
- MiMo TTS 音频由固定设置的 MiMo-V2.5-TTS API 生成。
- CosyVoice、Whisper、Paraformer 与 Qwen 输出来自开源组件。
- Paraformer 使用 `paraformer-zh` v2.0.4 与 FSMN-VAD v2.0.4，不使用标点模型、热词或外部语言模型。`use_itn` 开关没有改变 220 条完整音频和 46 条对齐片段中的任何转写，因此不把它解释为 ITN 因果消融。
- Qwen3-ASR-1.7B 使用空 context 和自动语言识别，不接收原文、预期读法、负例读法或目标提示。
- Raw/Structured 对照是 oracle-style diagnostic，不是可部署前端的公平系统比较；Structured 显式实例化了预先标注的预期读法。

## 仓库结构

```text
cn-newstts-asr-roundtrip-masking/
  metadata/                  # 冻结 benchmark、候选池与标注补充
  rules_and_schema/          # 风险规则、schema、提示词和评分定义
  labels/                    # 200 例和 110 例人工标注
  results/                   # TTS/ASR 输出、审计表和对照实验
  manifests/                 # 生成与转写 manifest
  scripts/                   # 构造、分析与核验脚本
  docs/                      # 标注规范和协议说明
```

大体量生成音频通过 [Zenodo 归档](https://doi.org/10.5281/zenodo.21454402) 发布，不存放在 GitHub。

## 引用

论文：

```bibtex
@misc{luo2026asrroundtrip,
  title        = {ASR-Roundtrip Evaluation Can Mask Context- and Convention-Dependent Reading Errors in Chinese News TTS},
  author       = {Luo, Shijun and Wan, Lizhi},
  year         = {2026},
  eprint       = {2608.10606},
  archivePrefix= {arXiv},
  primaryClass = {cs.CL},
  doi          = {10.48550/arXiv.2608.10606}
}
```

配套数据：

```text
Luo, Shijun, and Lizhi Wan. Supporting Materials for ASR-Roundtrip
Evaluation Can Mask Context- and Convention-Dependent Reading Errors in
Chinese News TTS. Zenodo, 2026. https://doi.org/10.5281/zenodo.21454402
```

机器可读的引用信息见 [CITATION.cff](CITATION.cff)。

## 许可证

- 代码和脚本：[MIT License](LICENSE)。
- 公开的公司授权生产新闻文稿、合成样本、配套归档中的生成式 TTS 音频、标注、人工标签、ASR 转写、审计表和衍生 metadata：[CC BY 4.0](DATA_LICENSE.md)。

## 联系方式

发布材料相关问题：xiaobiluo@gmail.com。

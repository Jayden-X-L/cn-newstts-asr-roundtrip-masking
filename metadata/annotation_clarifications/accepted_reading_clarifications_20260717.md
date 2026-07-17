# Accepted-reading clarification (2026-07-17)

`P1P2_027 / PCP2_0064` contains the aircraft model `737-8`. The frozen rule metadata treated it as a generic hyphenated range, which is too narrow for this context.

Public aviation sources support `737减8` as an industry reading and also document `737杠8` as an accepted public reading. The corrected accepted set is therefore `七三七减八` / `七三七杠八`. The observed MiMo Raw reading `七三七负八` and the range-like Structured reading `七百三十七到八` remain errors.

This clarification does not change the 200-case human correct-span counts or the MiMo 110-case audit outcome. The Raw audio remains wrong, while default and MiMo-V2-Omni ASR routes recover a surface-correct aircraft form. It does change the aligned context-isolation judgment: the isolated transcript `七三七杠八` is an accepted variant and is therefore `still_masked`, not `exposed`.

Sources:

- CCTV / Civil Aviation Administration explanation: <https://m.news.cctv.com/2019/03/18/ARTI02dD4o3KY1mQD6HXyLyJ190318.shtml>
- Beijing News report syndicated by NetEase: <https://www.163.com/air/article/EAKFBSQA000181O6.html>

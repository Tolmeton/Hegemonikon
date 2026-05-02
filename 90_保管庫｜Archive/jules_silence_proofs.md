# Jules Specialist Review — 不在証明 (Silence Proofs)

> **生成日**: 2026-02-21
> **母集団**: 1349 PRs (Tolmeton/Hegemonikon, open)
> **沈黙PR数**: 271 (Cortex 2重検証済み)
> **指摘PR数**: 1018
> **コード変更PR数**: 60
> **沈黙率**: 20.1%
> **偽陰性検証**: 全273件を Cortex (gemini-2.0-flash) で4バッチ + Pass 2 検証。偽陰性2件除外済み。

---

## 沈黙PR一覧

| # | PR | タイトル | ブランチ |
|:--|:---|:--------|:--------|
| 1 | #3252 | Add Stoic Control Referee review for Aristos | aristos-review-3993586608688556591 |
| 2 | #3253 | Add CCL Style Aesthete review for Aristos | review/aristos-init-5258115134131482560 |
| 3 | #3254 | Add HG-001.MF PROOF Line Review for Aristos | hg-001.mf-review-aristos-4887228404822787537 |
| 4 | #3263 | Add HG-006.M review for Aristos project | hg-006-workflow-review-aristos-17083993755564411796 |
| 5 | #3265 | Stoic Control Adjudicator Review for Aristos | hg-003-review-aristos-9725496390815694114 |
| 6 | #3268 | Add AI-002.F review for Aristos project | aristos-review-ai-002f-5124585595352391438 |
| 7 | #3272 | HG-006.P Review: nous/projects/aristos/**init**.py | hg-006-p-review-aristos-1043072921466192507 |
| 8 | #3273 | Add HG-002.μP review for Aristos project | hg-002-review-aristos-16776588542302281832 |
| 9 | #3278 | Add HG-005.μP review for Aristos | feature/aristos-review-hg-005-up-2992666685925506216 |
| 10 | #3285 | Add HG-002.M review for Aristos | hg-002-m-review-aristos-10405607964428318516 |
| 11 | #3288 | Add CCL review for aristos project | docs/aristos-ccl-review-12466877968613998159 |
| 12 | #3293 | docs: add specialist review for aristos/**init**.py | specialist-review-aristos-init-3439256326528431171 |
| 13 | #3294 | AI-005.F Review for Aristos | ai-005.f-review-aristos-4749857118579059260 |
| 14 | #3301 | docs: add cognitive nesting review for aristos | docs/aristos-nesting-review-17398258888715996392 |
| 15 | #3302 | docs: add Simplicity Gatekeeper review for aristos | docs/add-aristos-simplicity-review-6323090312573880490 |
| 16 | #3303 | Add HG-006.μP review for aristos | review/aristos-hg-006-18023173757834156183 |
| 17 | #3304 | Add Workflow Conformance Auditor review for Aristos project | review/aristos-workflow-audit-5547649680340884476 |
| 18 | #3305 | CF-001.μ Review for nous/projects/aristos/**init**.py | specialist-review-aristos-init-1810383375658757390 |
| 19 | #3307 | Workflow Suitability Review: nous/projects/aristos/**init**.py | hg-006-uf-review-aristos-9853001696137969895 |
| 20 | #3310 | Add Cognitive Chunk Analysis review for aristos/**init**.py | specialist/cg-002-u-aristos-init-6853609204619524677 |
| 21 | #3316 | chore: add import graph audit for aristos | aristos-import-audit-6570640045348047864 |
| 22 | #3317 | Add Series Placement review for Aristos | ev-001-series-placement-review-aristos-11296213630400324888 |
| 23 | #3321 | feat(symploke): add import graph review for aristos | jules/aristos-review-7139447347531033891 |
| 24 | #3322 | Add AI-002.μ hallucination review for aristos | ai-002-mu-hallucination-review-aristos-2481157710617657801 |
| 25 | #3329 | AI-005.μF Review for Aristos Project | ai-005-review-aristos-7103310665806802089 |
| 26 | #3332 | docs: add specialist review for aristos/**init**.py | docs/add-aristos-init-review-3379793362403447277 |
| 27 | #3335 | Add Stoic Control Adjudicator review for Aristos | review/aristos-hg-003-mf-2750206912001804650 |
| 28 | #3339 | Add CG-001.M review for Aristos init | cg-001-m-review-aristos-1850364432255207698 |
| 29 | #3342 | Add AE-014.M review for Aristos | aristos-review-ae-014m-13758284160626892154 |
| 30 | #3351 | Add CCL Style Aesthete review for derivative_selector.py | review/hg-004.f-derivative-selector-18163504829677519675 |
| 31 | #3352 | docs: Add HG-006.MP review for mekhane/fep/derivative_selector.py | hg-006-mp-derivative-selector-10411170343371016207 |
| 32 | #3353 | Add AI-002.M review for aristos | specialist-review-aristos-4479427442564471208 |
| 33 | #3356 | docs: add AI-002.MF review for Aristos | docs/add-aristos-hallucination-review-6857094356117570596 |
| 34 | #3357 | docs(reviews): add Import Graph audit for aristos | docs/aristos-import-audit-5555217068430214267 |
| 35 | #3359 | Add AE-014.F Review for Aristos | docs/add-ae-014-f-review-aristos-6963799374477126401 |
| 36 | #3361 | Add CF-002.M review for aristos/**init**.py | aristos-review-cf-002m-5456863492336540588 |
| 37 | #3362 | Add Implicit Contract Review for Aristos | docs/aristos-implicit-contract-review-17283339331635144843 |
| 38 | #3378 | Simplicity Gatekeeper Review: Aristos | ae-013/simplicity-review-10267406937844034277 |
| 39 | #3379 | AE-013.M Review for aristos init | ae-013-aristos-init-review-7445522321166343465 |
| 40 | #3385 | docs: Add CF-002.F review for Aristos **init**.py | docs/add-cf-002.f-review-aristos-4448063997811771728 |
| 41 | #3387 | HG-004.µF Specialist Review for derivative_selector.py | hg-004-uF-review-derivative-selector-8679235044841297144 |
| 42 | #3398 | Specialist Review CF-002.MF for Aristos | specialist-review-aristos-cf002mf-5187167372551994897 |
| 43 | #3399 | docs: Add Nest Depth Alerter review for Aristos | specialist/cg-001-mf-aristos-review-10775604498762584244 |
| 44 | #3402 | Add Visual Rhythm review for Aristos init file | docs/aristos-visual-rhythm-review-3059712073987053954 |
| 45 | #3406 | LLM Odor Review for Aristos | lm-001-odor-aristos-9800419019628777243 |
| 46 | #3412 | docs: add ev-001 review for aristos | docs/ev-001-review-aristos-18208811756487473585 |
| 47 | #3417 | Add HG-007.MF review for derivative_selector.py | hg-007-mf-review-17884830263062315289 |
| 48 | #3419 | Add AI-002.μF review for derivative_selector.py | ai-002-hallucination-review-15166979258190884326 |
| 49 | #3426 | LM-001.F Review: nous/projects/aristos/**init**.py | jules-review-aristos-init-1270874579503740444 |
| 50 | #3427 | docs: add AE-012.MP review for derivative_selector.py | docs/ae-012-mp-review-17237732085513877468 |
| 51 | #3434 | Add specialist review for derivative_selector.py | review-hg006-derivative-selector-533066894546330108 |
| 52 | #3435 | feat(review): add AE-012.M specialist review for derivative_selector.py | ae-012-m-derivative-selector-4679690938756014886 |
| 53 | #3436 | Add AI-002.MF review for derivative_selector.py | docs/add-ai-002-mf-review-3946688280085648796 |
| 54 | #3443 | Add AE-012.μ review for derivative_selector.py | ae-012-mu-review-derivative-selector-17455221523922117663 |
| 55 | #3446 | docs: add CCL Style Aesthete review for workflow_runner.py | hg-004-review-workflow-runner-12408213728381226211 |
| 56 | #3453 | Add HG-006.M review for derivative_selector.py | hg-006-m-review-derivative-selector-2224473545074023564 |
| 57 | #3461 | Add LM-001.MF review for Aristos | lm-001-mf-aristos-review-16326427010815012689 |
| 58 | #3463 | Workflow Conformance Auditor Review: derivative_selector.py | hg-006-mf-review-derivative-selector-11761296682500464955 |
| 59 | #3464 | Add CCL Style Aesthete (HG-004.P) review for derivative_selector.py | specialist-review-hg-004-p-15528387215616334694 |
| 60 | #3473 | AI-002.F Review: derivative_selector.py | ai-002-f-review-derivative-selector-49517320209956507 |
| 61 | #3477 | Add HG-004.μF specialist review for workflow_runner.py | hg-004-uf-review-workflow-runner-10381445275299457795 |
| 62 | #3485 | Add CF-002.μ review for aristos/**init**.py | specialist/cf-002-mu-aristos-review-6137061502047345887 |
| 63 | #3496 | HG-004.µ Review: mekhane/workflow_runner.py | specialist/hg-004.u-workflow-runner-8411961644945394076 |
| 64 | #3499 | Add AE-013 review for Aristos | ae-013-aristos-review-16730010277833323961 |
| 65 | #3511 | Add HG-004.µP review for derivative_selector.py | hg-004-derivative-selector-review-6124185448811255192 |
| 66 | #3514 | chore: add CCL Style Aesthete review for workflow_runner.py | chore/hg-004-f-review-workflow-runner-6950385051698254040 |
| 67 | #3520 | Add EV-001.μF review for Aristos project | ev-001-f-aristos-review-13468087726072792609 |
| 68 | #3534 | Specialist Review: HG-004.µ (CCL Aesthetician) | hg-004-micro-review-12681457090405054722 |
| 69 | #3536 | docs: add AI-002.μ review for derivative_selector.py | docs/add-ai-002-u-review-16187493862524448211 |
| 70 | #3539 | Add Nest Depth review for workflow_runner.py | specialist-review-cg-001.f-workflow-runner-5211027905464233115 |
| 71 | #3543 | Add specialist review for workflow_runner.py | review/ae-012-workflow-runner-13580759179030093424 |
| 72 | #3567 | docs: add cognitive chunk review for workflow_runner.py | docs-cognitive-chunk-workflow-runner-2774597334409320337 |
| 73 | #3568 | Add HG-004.M Review for Workflow Runner | hg-004-m-review-workflow-runner-10377405900430050909 |
| 74 | #3573 | AI-002.μF Review: mekhane/workflow_runner.py | ai-002-mu-f-review-14782827327259403215 |
| 75 | #3581 | LM-001.μ review of aristos/**init**.py | lm-001-review-aristos-12008558115878028580 |
| 76 | #3582 | Add HG-004.MF Specialist Review for workflow_runner.py | doc/hg-004-review-workflow-runner-2895249989380212551 |
| 77 | #3586 | AI-002.MP Review: mekhane/workflow_runner.py | ai-002-mp-review-workflow-runner-10205891523677486833 |
| 78 | #3602 | Add HG-006.MP Review for executor.py | hg-006-mp-review-executor-945870839302415935 |
| 79 | #3608 | Add HG-001.MP Review for hermeneus/src/executor.py | hg-001.mp-review-hermeneus-executor-16411084935380199277 |
| 80 | #3613 | AI-002.μ review for hermeneus/src/executor.py | ai-002-review-executor-3158637502476257868 |
| 81 | #3619 | Add HG-004.F review for hermeneus/src/executor.py | hg-004-f-review-executor-13852642889715952034 |
| 82 | #3625 | Add PROOF Line Inspector review for hermeneus/src/executor.py | hg-001.mu-review-executor-4426380101611716855 |
| 83 | #3628 | HG-004.μ Review for hermeneus/src/executor.py | feature/hg-004-mu-review-executor-14672043132560192810 |
| 84 | #3629 | Add HG-006.F review for hermeneus/src/executor.py | hg-006.f-executor-review-2731976692676455015 |
| 85 | #3630 | Add HG-006.μ Review for hermeneus/src/executor.py | hg-006.mu-review-hermeneus-executor-6099193535527541580 |
| 86 | #3633 | Add AI-002.M review for hermeneus/src/executor.py | ai-002-m-executor-review-10637392000426911331 |
| 87 | #3636 | Add CCL Aesthetician review for hermeneus/src/executor.py | review/hg-004-mf-executor-15461199541077891812 |
| 88 | #3640 | Add HG-006.μP review for executor.py | hg-006-review-executor-3914846953787040818 |
| 89 | #3643 | AI-002.P Review for hermeneus/src/executor.py | hermeneus-executor-ai-002p-review-12009725433996750950 |
| 90 | #3645 | AE-012.MP Visual Rhythm Review for hermeneus/src/executor.py | review/ae-012.mp-hermeneus-executor-10434579799866102550 |
| 91 | #3649 | docs: add AI-002.MP hallucination review for hermeneus/src/executor.py | ai-002-mp-review-6675665564627480395 |
| 92 | #3651 | Add Visual Rhythm Conductor review for executor.py | ae-012-review-executor-6485825781339261584 |
| 93 | #3652 | Add HG-007.MF review for hermeneus/src/executor.py | hg-007-mf-review-executor-780623375670310685 |
| 94 | #3656 | Add HG-006.μF review for hermeneus/src/executor.py | hg-006-review-executor-3557585603734613260 |
| 95 | #3662 | Add AE-012.MF Review for Hermeneus Executor | ae-012-mf-review-17877061858167000762 |
| 96 | #3665 | Add HG-006.MF review for hermeneus/src/executor.py | hg-006-review-executor-10277166464846557655 |
| 97 | #3669 | Add AI-002.μF review for hermeneus/src/executor.py | ai-002-review-executor-18084711900663136071 |
| 98 | #3686 | Add EV-001.µF review for hermeneus/src/executor.py | ev-001-executor-review-307196732720568461 |
| 99 | #3689 | Add AI-002.MF review for hermeneus/src/executor.py | hermeneus-executor-ai-002-mf-review-5865191277663790209 |
| 100 | #3697 | Add HG-007.µ review for mekhane/anamnesis/cli.py | hg-007-review-anamnesis-cli-921825756122362784 |
| 101 | #3701 | AE-012.P Review of hermeneus/src/executor.py | ae-012-p-review-executor-12130370314577589581 |
| 102 | #3704 | Add AI-002.F review for hermeneus/src/executor.py | jules-ai-002-review-hermeneus-executor-11892393490541544492 |
| 103 | #3708 | EV-001.μP Review of `hermeneus/src/executor.py` | ev-001-review-executor-5184086555255339444 |
| 104 | #3710 | Add HG-003.μP review for hermeneus/src/executor.py | hg-003-review-executor-14343699873578551014 |
| 105 | #3712 | Docs: Add HG-004.F review for mekhane/anamnesis/cli.py | docs/hg-004-f-review-cli-17176587740505785507 |
| 106 | #3715 | Add CG-002 review for mekhane/anamnesis/cli.py | cg-002-review-anamnesis-9408068970682032956 |
| 107 | #3717 | docs: add nesting depth review for hermeneus/src/executor.py | cg-001-executor-review-6419155581936483805 |
| 108 | #3720 | Add HG-006.μ review for mekhane/anamnesis/cli.py | hg-006-review-anamnesis-cli-6105947602188720899 |
| 109 | #3722 | docs: Add CCL Style Aesthete review for mekhane/anamnesis/cli.py | specialist-review/hg-004-up-anamnesis-cli-9165627314302484913 |
| 110 | #3723 | Add HG-006.M review for mekhane/anamnesis/cli.py | specialist/hg-006-m-review-122299344941294098 |
| 111 | #3727 | Add HG-004.μF review for mekhane/anamnesis/cli.py | hg-004-review-anamnesis-cli-11284207373617838682 |
| 112 | #3732 | Add HG-007.MP review for hermeneus/src/executor.py | hg-007-mp-review-16506040923968556259 |
| 113 | #3733 | Add AI-002.µP review for hermeneus/src/executor.py | review/hermeneus-executor-ai002-4554851991385630845 |
| 114 | #3734 | Add CG-001.P review for hermeneus/src/executor.py | review/cg-001.p/hermeneus-executor-10522141629564043113 |
| 115 | #3735 | Add HG-006.P review for mekhane/anamnesis/cli.py | hg-006-p-review-cli-2723129481617797842 |
| 116 | #3736 | Add AI-002.M Hallucination Detector Review for Anamnesis CLI | ai-002-m-anamnesis-cli-17040997832973308667 |
| 117 | #3743 | AI-002.μF Review of mekhane/anamnesis/cli.py | ai-002-mu-f-review-cli-13323987097434695112 |
| 118 | #3745 | Add AE-012.μ Visual Rhythm review for executor.py | ae-012.μ-review-executor-11694248234312655025 |
| 119 | #3747 | AI-002.F Review: mekhane/anamnesis/cli.py (Silence) | ai-002-f-review-cli-analysis-1799780637804076319 |
| 120 | #3751 | HG-004.MP Review: mekhane/anamnesis/cli.py | hg-004-review-anamnesis-cli-15185375159506005832 |
| 121 | #3754 | Add HG-006.MP Review for mekhane/anamnesis/cli.py | hg-006-mp-review-anamnesis-cli-15699106154307437248 |
| 122 | #3758 | AI-002.MP Review: Hallucination Detection for mekhane/anamnesis/cli.py | ai-002-mp-review-16997872839569405446 |
| 123 | #3759 | Add HG-006.μP review for mekhane/anamnesis/cli.py | hg-006-review-anamnesis-cli-18343018805232463325 |
| 124 | #3762 | Add HG-006.F review for mekhane/anamnesis/cli.py | hg-006-f-review-anamnesis-cli-7991282345741888861 |
| 125 | #3812 | Add HG-006.P review for session_indexer.py | hg-006-p-review-session-indexer-306476686373263806 |
| 126 | #3816 | HG-004.P Review: mekhane/anamnesis/session_indexer.py | hg-004-p-review-session-indexer-3334169235548432519 |
| 127 | #3818 | Add CCL Aesthetician review for session_indexer.py | hg-004-mu-review-session-indexer-13763201755173923288 |
| 128 | #3819 | Add HG-007.MF review for mekhane/anamnesis/cli.py | hg-007-mf-review-anamnesis-5389349809686173755 |
| 129 | #3824 | Add HG-007.MP review for mekhane/anamnesis/cli.py | hg-007-mp-review-anamnesis-cli-3826363957396240301 |
| 130 | #3831 | AI-002.μP Review of mekhane/anamnesis/cli.py | ai-002-mp-review-cli-13704282683554510189 |
| 131 | #3837 | AI-002.P Review for session_indexer.py | ai-002.p-session-indexer-1442477747668164402 |
| 132 | #3842 | Add AI-002.MF review for mekhane/anamnesis/cli.py | docs/add-ai-002-mf-review-cli-16205225370532482827 |
| 133 | #3849 | Add CG-001.μF review for executor.py | jules-review-cg-001-uf-executor-9552254067002600423 |
| 134 | #3862 | Add HG-004.F review for mekhane/anamnesis/session_indexer.py | hg-004-f-review-session-indexer-13733956023962730133 |
| 135 | #3864 | Add AI-002.MP review for session_indexer.py | ai-002-mp-review-session-indexer-5116597037886427073 |
| 136 | #3866 | Add CF-002.μ review for mekhane/anamnesis/cli.py | jules-review-mekhane-anamnesis-cli-cf-002-u-13495918147133530797 |
| 137 | #3876 | Add AI-002.μ review for mekhane/anamnesis/cli.py | ai-002-mu-review-cli-12919247055974259861 |
| 138 | #3882 | docs: add AE-012.M specialist review for session_indexer.py | ae-012-m-review-session-indexer-15196972748590605112 |
| 139 | #3885 | Add AE-012.M Specialist Review for hermeneus/src/executor.py | ae-012-review-executor-13873411679330566182 |
| 140 | #3899 | Add HG-006.MP review for chat.py | hg-006-mp-chat-review-1162492916756705309 |
| 141 | #3912 | AI-005.μ Review: mekhane/anamnesis/cli.py | ai-005-review-cli-13931192922594822418 |
| 142 | #3924 | Add AI-002.M review for chat.py | add-ai-002-m-review-chat-8415434393293405038 |
| 143 | #3928 | Add EV-001.MP review for mekhane/api/routes/chat.py | ev-001-review-chat-route-11604142946893568548 |
| 144 | #3947 | Add HG-007.MF review for mekhane/api/server.py | hg-007-mf-review-server-4228756851114538151 |
| 145 | #3948 | doc: add HG-006.MF workflow review for mekhane/api/server.py | review/hg-006.mf-mekhane-api-server-556442980490260456 |
| 146 | #3957 | Add HG-004.μ review for mekhane/fep/attractor_advisor.py | hg-004-mu-review-attractor-advisor-13262155768354720935 |
| 147 | #3965 | AI-002.P Review: mekhane/fep/attractor_advisor.py | ai-002-p-review-attractor-advisor-2194528305544343623 |
| 148 | #3970 | Add HG-006.M review for mekhane/api/server.py | hg-006-m-review-api-server-10748157027287943030 |
| 149 | #3973 | HG-004.μP review of mekhane/api/server.py | review/hg-004-api-server-9113278755336936094 |
| 150 | #3974 | Add AI-002.μ review | ai-002-review-1080947899802178844 |
| 151 | #3979 | AE-012.P Review of attractor_advisor.py | ae-012-review-12623648444823444787 |
| 152 | #3980 | Workflow Suitability Review: mekhane/api/server.py | hg-006-micro-workflow-check-6634747669493624690 |
| 153 | #3981 | docs: AE-014.M review of mekhane/api/server.py | ae-014-m-review-server-16607430067431172664 |
| 154 | #3984 | HG-006.MF Review for Attractor Advisor | hg-006-mf-review-attractor-advisor-10864774812997581732 |
| 155 | #3986 | Add HG-003.μP review for mekhane/api/server.py | docs/hg-003-review-server-15694259345669941517 |
| 156 | #3989 | AI-002.MP Review: mekhane/api/server.py | ai-002.mp/server-review-17861541028613067378 |
| 157 | #3990 | chore: add HG-006.MP review for attractor_advisor | hg-006-mp-review-attractor-advisor-7308126692316151254 |
| 158 | #3992 | AI-002.μF Review: mekhane/api/routes/chat.py | ai-002-review-chat-route-6614440049593044652 |
| 159 | #3994 | Add AE-014.P Review for mekhane/api/server.py | ae-014-p-review-api-server-1303999641614006754 |
| 160 | #3996 | Add HG-006.P review for mekhane/fep/attractor_advisor.py | hg-006-p-review-attractor-advisor-15765508159160093387 |
| 161 | #4017 | Add HG-007.MF review for hgk_gateway.py | hg-007-review-gateway-1076728493201278703 |
| 162 | #4024 | AI-002.μP Review of HGK Gateway | ai-002-review-hgk-gateway-5488041326307167220 |
| 163 | #4033 | Add HG-006.P review for ochema_mcp_server.py | hg-006-review-ochema-mcp-14904042692565644341 |
| 164 | #4038 | Add HG-007.MP review for hgk_gateway.py | hg-007-mp-review-gateway-641055281091980913 |
| 165 | #4039 | Add HG-006.μ review for mekhane/fep/attractor_advisor.py | hg-006.μ-review-14197529261620867918 |
| 166 | #4043 | AI-002.µF Review: hgk_gateway.py | ai-002-mu-f-review-hgk-gateway-16888816544488506384 |
| 167 | #4048 | Add HG-003.MP review for mekhane/api/server.py | hg-003-server-review-116179792604942672 |
| 168 | #4053 | Add HG-004.µ review for hgk_gateway.py | hg-004-review-gateway-7655313899206282452 |
| 169 | #4060 | Import Graph Auditor Review for hgk_gateway.py | jules/review-cf-001-f-hgk-gateway-1022600208687579634 |
| 170 | #4071 | Add AI-002.MP review for hgk_gateway.py | ai-002-mp-review-hgk-gateway-4943712311252017294 |
| 171 | #4079 | Add HG-007.μ review for ochema_mcp_server | review/hg-007-ochema-mcp-7178731382307832679 |
| 172 | #4081 | Add HG-003.μ review for mekhane/ochema/**init**.py | hg-003-review-ochema-16779794075979693979 |
| 173 | #4098 | HG-007.MP Review: ochema_mcp_server.py | hg-007-mp-review-ochema-mcp-7034499453989145702 |
| 174 | #4103 | AI-002.MP Review: mekhane/ochema/**init**.py | ai-002-mp-review-11191646186937862501 |
| 175 | #4107 | Add HG-004.MF review for ochema_mcp_server.py | hg-004-mf-ochema-mcp-review-15458027913373392624 |
| 176 | #4111 | AI-002.M Review: ochema_mcp_server.py (Silence) | jules-ai-002-m-ochema-mcp-review-12704968483395357664 |
| 177 | #4117 | AI-002.F Review: mekhane/ochema/**init**.py | ai-002-f-review-ochema-init-7100010465863919199 |
| 178 | #4119 | AE-012.M Review for mekhane/ochema/**init**.py | ae-012-review-ochema-5000354691618245477 |
| 179 | #4120 | Add Cognitive Chunk Analysis review for mekhane/ochema/**init**.py | cg-002-mp-review-ochema-init-10090468829452559694 |
| 180 | #4121 | Add AI-002.P review for ochema_mcp_server.py | ai-002-p-review-ochema-mcp-server-2470239982121943091 |
| 181 | #4140 | Add HG-006.P review for hgk_gateway | hg-006-p-review-hgk-gateway-16220398961293555452 |
| 182 | #4144 | docs: Add HG-006.µP review for mekhane/ochema/**init**.py | hg-006.up-review-ochema-16246683964753934974 |
| 183 | #4146 | Import Graph Audit of mekhane/ochema/**init**.py (CF-001.MP) | jules-review-ochema-init-graph-audit-10909629249037663794 |
| 184 | #4154 | Import Graph Review: mekhane/ochema/**init**.py | import-graph-review-ochema-2197645757991311987 |
| 185 | #4158 | Add LM-001 review for attractor_advisor.py | lm-001-attractor-advisor-review-17278452204957160512 |
| 186 | #4159 | LM-001.M Review for mekhane/ochema/**init**.py | lm-001.m-review-ochema-7168508996486562444 |
| 187 | #4160 | Add HG-006.M review for antigravity_client.py | hg-006-review-client-1615745069231031531 |
| 188 | #4164 | Add AI-002.µF review for mekhane/ochema/**init**.py | ai-002-review-ochema-init-6907622515321752825 |
| 189 | #4165 | Add LM-001.μF review for mekhane/ochema/**init**.py | lm-001-ochema-init-review-3306928340032912933 |
| 190 | #4169 | docs: add AI-002.μP review for mekhane/ochema/antigravity_client.py | doc/ai-002-review-antigravity-client-16006025437438094512 |
| 191 | #4171 | Add HG-004.MP review for mekhane/ochema/**init**.py | hg-004-review-ochema-6916067380037924954 |
| 192 | #4172 | Add HG-007.μF review for mekhane/ochema/**init**.py | hg-007-review-ochema-init-9323839071702692045 |
| 193 | #4174 | chore: add nest depth review for mekhane/ochema/**init**.py | chore/nest-depth-review-ochema-init-6967872059952224770 |
| 194 | #4179 | AE-013.MF Simplicity Review: mekhane/ochema/**init**.py | review/ae-013-ochema-1978123091638815125 |
| 195 | #4180 | Add CG-002.MF review for mekhane/ochema/**init**.py | cg-002-review-ochema-475308359740227231 |
| 196 | #4181 | LM-001.P Review of mekhane/ochema/**init**.py | lm-001-review-ochema-init-6156099156944810037 |
| 197 | #4183 | docs: add CF-001.μ review for mekhane/ochema/**init**.py | docs/add-cf-001-micro-review-ochema-init-9935900948902466140 |
| 198 | #4187 | Add EV-001.MP review for mekhane/ochema | ev-001-ochema-review-2987950365033831548 |
| 199 | #4197 | Add AI-002.F Hallucination Review for Antigravity Client | ai-002-review-antigravity-client-8451469564027544326 |
| 200 | #4206 | HG-006.MF Review: Antigravity Client | hg-006-mf-antigravity-client-review-13525282621641328327 |
| 201 | #4210 | Add Simplicity Gatekeeper review for mekhane/ochema/**init**.py | review/ochema-init-ae013-2157448749350812893 |
| 202 | #4216 | Add HG-004.μ review for mekhane/ochema/**init**.py | hg-004-mu-review-ochema-init-17633377331809661284 |
| 203 | #4220 | docs: Add HG-006.P review for ochema/antigravity_client | hg-006-p-review-ochema-client-16313409922358749604 |
| 204 | #4233 | Add Cognitive Chunk Analysis for AntigravityClient | chore/cognitive-chunk-review-antigravity-4423463387136034988 |
| 205 | #4239 | HG-006.MP Review: Antigravity Client (Silence) | hg-006-mp-review-antigravity-client-892488866326578044 |
| 206 | #4246 | Add HG-007.MP review for mekhane/ochema/antigravity_client.py | hg-007-review-ochema-3441381764731005212 |
| 207 | #4247 | Add HG-008.MF review for antigravity_client.py | hg-008-mf-review-antigravity-client-6503056191539930014 |
| 208 | #4254 | HG-004.μ Review: cortex_client.py | hg-004-review-cortex-client-8023139856414142596 |
| 209 | #4258 | Add HG-007.MP review for mekhane/ochema/cortex_client.py | review/hg-007-mp-cortex-client-2840491909806633242 |
| 210 | #4261 | Add HG-004.M specialist review for mekhane/ochema/service.py | review/hg-004-m-ochema-service-16699904563762368028 |
| 211 | #4265 | Add HG-004.MF review for mekhane/ochema/service.py | hg-004-mf-review-ochema-service-10478812996412468272 |
| 212 | #4267 | Add AI-002.MP review for ochema/service.py | jules-review-ai-002-mp-ochema-service-4122824352284726753 |
| 213 | #4269 | LM-001.P Review for Cortex Client | lm-001-review-cortex-client-11641456884424076879 |
| 214 | #4272 | Add CG-002.F review for mekhane/ochema/service.py | cg-002-review-ochema-service-12072205770256271376 |
| 215 | #4280 | Add CG-002.μ review for mekhane/ochema/cortex_client.py | reviews/cg-002-micro-cortex-client-4175079025339853493 |
| 216 | #4283 | Add AE-012.μP review for ochema/service.py | ae-012-review-service-12780929413377025968 |
| 217 | #4289 | Add AI-002.µF review for test_service.py | ai-002-mf-review-test-service-1389679618436799993 |
| 218 | #4293 | Visual Rhythm Review: mekhane/ochema/service.py | ae-012-review-service-1185795214827174857 |
| 219 | #4294 | LM-001.MP Review for mekhane/ochema/service.py | lm-001-mp-review-ochema-service-5984318701988788201 |
| 220 | #4301 | Add HG-004.MP review for mekhane/ochema/service.py | hg-004-mp-review-service-7698482189706500724 |
| 221 | #4307 | Add Cognitive Chunk Analysis review for test_service.py | jules-cg-002-review-tests-6182935045268445151 |
| 222 | #4310 | HG-007.µ Review of mekhane/ochema/tests/test_service.py | review/hg-007.u-test-service-12647199906674870778 |
| 223 | #4312 | Add EV-001.M review for mekhane/ochema/tests/test_service.py | ev-001-m-review-8894855342661991644 |
| 224 | #4318 | CF-002.μ review of mekhane/ochema/tests/test_service.py | cf-002-review-service-test-8121718117828767742 |
| 225 | #4319 | Add Nesting Depth Review for Citation Agent | cg-001-review-citation-agent-15899913116734090262 |
| 226 | #4322 | Add HG-006.MP review | review/hg-006-mp-2361562278751802675 |
| 227 | #4324 | Add HG-006.MP review for citation_agent | hg-006-mp-review-citation-agent-3768010345629542693 |
| 228 | #4335 | Add HG-004.M specialist review for periskope/cli.py | hg-004-m-review-periskope-cli-5344187656380772930 |
| 229 | #4336 | Add HG-001.P review for mekhane/periskope/cli.py | hg-001.p-review-periskope-cli-9569411124970134103 |
| 230 | #4342 | CG-001 Review: Periskope CLI | cg-001-nest-depth-review-5122005710472592730 |
| 231 | #4360 | Add HG-002.μ review for mekhane/periskope/engine.py | hg-002-mu-review-periskope-engine-5465653334276653956 |
| 232 | #4382 | Add Simplicity Gatekeeper review for mekhane/periskope/engine.py | jules-ae-013-mf-review-engine-15649685251757682296 |
| 233 | #4386 | Add HG-005.M audit report for periskope/engine.py | hg-005-audit-periskope-engine-16754165436960548619 |
| 234 | #4388 | Add LM-001.μF review for mekhane/periskope/cli.py | lm-001-periskope-review-4999936754375496812 |
| 235 | #4392 | Add HG-003.μP review for mekhane/periskope/models.py | hg-003-review-periskope-models-1968105700637312962 |
| 236 | #4398 | CG-001.μF Review of mekhane/periskope/engine.py | jules-cg-001-micro-review-9726096391890674812 |
| 237 | #4429 | HG-002.M Review of Periskopē Models | hg-002.m-review-periskope-models-13711629298161073778 |
| 238 | #4435 | Add HG-004.M Review for Periskope Models | hg-004-m-review-periskope-models-1000700990457235759 |
| 239 | #4454 | Add Cognitive Chunk Analyst review for models.py | add-cognitive-chunk-review-models-6881867045817359707 |
| 247 | #4484 | Add NM-010 review for boot_integration.py | nm-010-review-boot-integration-2173915130776988413 |
| 248 | #4489 | Add CS-005 review for boot_integration.py | cs-005-review-boot-integration-14023329055020894765 |
| 249 | #4490 | Add Lambda Boundary review for boot_integration.py | fn-006-review-boot-integration-4009396738310101638 |
| 250 | #4492 | Add CS-007 review for boot_integration.py | cs-007-boot-integration-review-10464535087382076969 |
| 251 | #4495 | AP-005: Content-Type Review for boot_integration.py | review/ap-005-15085595194198369630 |
| 252 | #4502 | Add GT-005 review for boot_integration.py | gt-005-review-boot-integration-17614386956213801176 |
| 253 | #4503 | HG-004 Review for boot_integration.py | hg-004-review-boot-integration-2501613371765320429 |
| 254 | #4507 | Add UL-005 Midnight Commit Alarmer review | ul-005-review-boot-integration-9342952364807330631 |
| 255 | #4519 | Add HTTPS Promoter review | sc-005-review-9645655305809929375 |
| 256 | #4522 | TS-006: Review boot_integration.py for skipped tests | ts-006-review-boot-integration-633376901929591186 |
| 257 | #4528 | NM-008 Review: boot_integration.py | nm-008-boot-integration-review-13459143704959410592 |
| 258 | #4529 | Add AS-002 Review for boot_integration.py | as-002-review-boot-integration-2187535477042884567 |
| 259 | #4540 | AS-005 Review: mekhane/symploke/boot_integration.py | as-005-review-boot-integration-14286814701641302987 |
| 260 | #4545 | Add CS-001 review for mekhane/symploke/boot_integration.py | review/cs-001/boot-integration-3147354559151078187 |
| 261 | #4550 | Add Etymological Review for boot_integration.py | nm-001-review-boot-integration-9485337126732906008 |
| 262 | #4554 | PF-002 Review: Silence for boot_integration.py | pf-002-review-boot-integration-17692085948113399259 |
| 263 | #4561 | Add TY-003 review for boot_integration.py | ty-003-boot-integration-review-8376516515319047290 |
| 264 | #4564 | Add TS-002 Review Report | ts-002-review-report-13471798031928220580 |
| 265 | #4567 | Add JP-002 review for boot_integration.py | reviews/jp-002-boot-integration-15007623948949648700 |
| 266 | #4573 | Add GT-006 review for boot_integration.py | gt-006-review-boot-integration-3224814596254034935 |
| 267 | #4578 | Add AS-003 review for boot_integration.py | as-003-review-boot-integration-9099241233899486645 |
| 268 | #4580 | HG-003 Review for boot_integration.py | hg-003-boot-review-53213070022415748 |

| 270 | #4583 | docs: add SC-003 pickle review for boot_integration | docs-add-sc-003-review-6429669580716603390 |
| 271 | #4586 | Add Migration Completeness review for boot_integration.py | specialist-review-db004-11247133760204732738 |
| 272 | #4590 | Add FN-005 review for boot_integration.py | fn-005-review-boot-integration-8061201083605303136 |
| 273 | #4591 | Add Dictionary Dispatch Proponent review for boot_integration.py | review-boot-integration-fn002-6620716577698656706 |

---

## 統計

- 全PR: 1349
- 沈黙 (問題なし): 271 (20.1%) — Cortex 2重検証済み
- 指摘あり: 1018 (75.5%)
- コード変更: 60 (4.4%)
- 偽陰性検証: 全273件をCortex 4バッチ + Pass 2 で検証。#4464 (コード変更), #4582 (指摘の可能性) を除外
- 偽陰性率: 0.7% (2/273)

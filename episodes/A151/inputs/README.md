# A151 新版字幕与实际成片门槛

## 已接收并锁定
- 用户新上传 SRT 为唯一字幕基准：[subtitles-latest.srt](subtitles-latest.srt)。
- 85条字幕，首条0:00，末条到203.280秒。
- 原配音 MP3: 203.4415秒，时间匹配，无需重配音。
- 相较上一版，**实质正文与字幕时间码完全一致**，主要取消句末标点。
- 原 MP3 暂不存入公开 GitHub；本地/受控执行需另行提供音频原件。

## 制作路径
1. 阅读 [文字画风宪章](../../../docs/visual-style-bible.md)，按52镜头独立生图，人物白圆脸、豆豆眼、简化发型，人物与生活场景自然融合；不得SVG贴片、九宫格或真人。
2. 输出 `shots/A151-S001.png` 至 `shots/A151-S052.png`，至少40张不同原生画面；当前计划为52张，须52张全部真实存在。
3. 素材程序筛查和逐帧人工审核；审片清单 `visual-qa.json` 的 `approved_shots` 必须列出全部计划镜头ID，并由审片者填写 `reviewer` 与 `notes`。
4. [渲染程序](../../../scripts/render_a151_video.py) 读取新版字幕和原 MP3，用静稳镜头直接剪切（不加抖动）、底部中文字幕、AAC音轨，生成MP4和渲染报告；视频制作完还须从头到尾看/听审。

```bash
python -m pip install Pillow
python scripts/validate_shot_assets.py \
  --plan episodes/A151/v3/scene-plan.json \
  --asset-root /path/to/A151-assets \
  --report /path/to/A151-assets/readiness.json

python scripts/render_a151_video.py \
  --plan episodes/A151/v3/scene-plan.json \
  --shots-dir /path/to/A151-assets \
  --audio /path/to/A151-original.mp3 \
  --srt episodes/A151/inputs/subtitles-latest.srt \
  --qa /path/to/A151-assets/visual-qa.json \
  --output /path/to/A151-final.mp4
```

## 真实状态
- **新SRT已就绪**；画风/角色卡/52镜头规划/渲染程序已准备。
- 本轮尝试生成画面仍出现含文字与播放器界面的九宫格概念图，严格判为不合格、不计数。
- **没有52张视觉合格的独立素材，也就没有符合约定的新版完整版MP4**。不得用4张图或裁切拼贴替代。

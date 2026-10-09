# 劉仲敬檔案館 · Liu Zhongjing Archive

劉仲敬公开内容的索引站，每月 1 日由 GitHub Actions 自动采集并发布到 GitHub Pages。

| 来源 | 内容 | 收录方式 |
|---|---|---|
| YouTube 官方频道 | 视频、直播、播放列表分类 | 标题、日期、时长、链接 |
| Medium @LiuZhongjing | 公开文章 | **全文** |
| 刘仲敬文稿站 (lzjscript.com，已下线) | 会员文稿 | 标题、日期、Wayback 存档链接 |
| 维基百科 | 著作、译著书目 | 书目信息 |

书籍和付费内容只收元数据，不转载正文，版权归原作者所有。

## 本地运行

```bash
pip install yt-dlp
cd collect && for s in books medium lzjscript youtube; do python3 $s.py; done; cd ..
python3 build.py && python3 -m http.server -d site 8000
```

- `collect/*.py`：每个来源一个采集器，数据只增不删，写入 `data/*.json`
- `build.py`：把 `data/` 生成为静态站点 `site/`
- `.github/workflows/collect.yml`：每月定时采集、提交数据、部署 Pages；也可在 Actions 页手动触发

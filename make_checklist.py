import re, pathlib
text = pathlib.Path("app/static/data.js").read_text(encoding="utf8")
names = re.findall(r'([A-Za-z][A-Za-z\- ]*?):(?:pu|pl|hg|sq|cu|ra|cr|m|t)(?=[,"])', text)
seen = dict.fromkeys(names)
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
lines = [f"{slug(n)}.mp4    <- {n}" for n in seen]
pathlib.Path("video_checklist.txt").write_text("\n".join(lines), encoding="utf8")
print(len(lines), "files listed in video_checklist.txt")

import UnityPy, json, re
base = "/Users/zhongyi/Documents/switch_exploration/fb3/romfs_dump/NCA FS/User/Extracted/Fit Boxing 3 -Your パーソナルトレーナー- 1.3.0 [0100AC101BFA2800][v524288][UPD]/Program #0/1/Data/StreamingAssets/aa/Switch/defaultassets_assets_database/"

def mono(path):
    env = UnityPy.load(path)
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            return o.read_typetree()
    return None

# 1) musicfiledata —— 找 BPM / cue / acb 映射
print("="*70, "\n### musicfiledata (找 BPM / 音频cue 映射)")
t = mono(base + "musicfiledata.bundle")
if t:
    tbl = t.get("Table", [])
    print("行数:", len(tbl))
    if tbl:
        print("字段:", list(tbl[0].keys()))
        for row in tbl[:4]:
            print("  ", json.dumps(row, ensure_ascii=False, default=str))

# 2) exercisescore00 —— 行数 / 槽数 / 用到的动作词汇
print("="*70, "\n### exercisescore00 结构统计")
t = mono(base + "exercisescore00.bundle")
tbl = t.get("Table", [])
print("行数(rows):", len(tbl))
slotlens = {len(r["Notes"]) for r in tbl}
print("每行槽数集合:", slotlens)
toks = [n for r in tbl for n in r["Notes"] if n]
print(f"非空音符总数: {len(toks)}")
uniq = sorted(set(toks))
print(f"不同 token 数: {len(uniq)}")
print("全部 token:", uniq)
cams = sorted({r["Camerawork"] for r in tbl if r["Camerawork"]})
print("Camerawork 取值:", cams)

# 3) exercisecombinationdata —— iNNN 是不是组合/指令
print("="*70, "\n### exercisecombinationdata (iNNN 含义?)")
t = mono(base + "exercisecombinationdata.bundle")
if t:
    tbl = t.get("Table", [])
    print("行数:", len(tbl), "字段:", list(tbl[0].keys()) if tbl else None)
    for row in tbl[:6]:
        print("  ", json.dumps(row, ensure_ascii=False, default=str))

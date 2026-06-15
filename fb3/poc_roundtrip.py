import UnityPy, json, os, glob

DB = "/Users/zhongyi/Documents/switch_exploration/fb3/romfs_dump/NCA FS/User/Extracted/Fit Boxing 3 -Your パーソナルトレーナー- 1.3.0 [0100AC101BFA2800][v524288][UPD]/Program #0/1/Data/StreamingAssets/aa/Switch/defaultassets_assets_database/"
SRC = DB + "exercisescore00.bundle"
STAGE = "/Users/zhongyi/Documents/switch_exploration/fb3/mod_staging/"
os.makedirs(STAGE, exist_ok=True)
OUT = STAGE + "exercisescore00.bundle"

print("### 1) 回环测试: 改写 exercisescore00 并重打包")
env = UnityPy.load(SRC)
mb = next(o for o in env.objects if o.type.name == "MonoBehaviour")
tree = mb.read_typetree()
rows = tree["Table"]
print(f"   原始: {len(rows)} 行, 前面非空音符示例 row5.Notes={[n for n in rows[5]['Notes'] if n]}")

# 安全且明显的改动: 把第 20~34 行(中段)的所有 Notes 清空 = 游戏里这段没有出拳提示
CLR0, CLR1 = 20, 35
cleared = 0
for r in rows[CLR0:CLR1]:
    for i in range(len(r["Notes"])):
        if r["Notes"][i]:
            cleared += 1
        r["Notes"][i] = ""
print(f"   改动: 清空第 {CLR0}~{CLR1-1} 行的音符, 共清掉 {cleared} 个")

mb.save_typetree(tree)

# 重打包(尝试 lz4 压缩, 失败则默认)
data = None
for kw in (dict(packer="lz4"), dict()):
    try:
        data = env.file.save(**kw); print(f"   重打包成功 (args={kw}), {len(data)} bytes"); break
    except Exception as e:
        print(f"   save{kw} 失败: {e!r}")
if data:
    open(OUT, "wb").write(data)
    print(f"   原文件 {os.path.getsize(SRC)} bytes -> 改后 {os.path.getsize(OUT)} bytes")

    print("\n### 2) 重新读取验证改动是否生效、结构是否完整")
    env2 = UnityPy.load(OUT)
    mb2 = next(o for o in env2.objects if o.type.name == "MonoBehaviour")
    t2 = mb2.read_typetree()
    ok_struct = (len(t2["Table"]) == len(rows)) and all(len(r["Notes"]) == 32 for r in t2["Table"])
    ok_cleared = all(all(n == "" for n in r["Notes"]) for r in t2["Table"][CLR0:CLR1])
    ok_kept = [n for n in t2["Table"][5]["Notes"] if n] == [n for n in rows[5]["Notes"] if n]
    print(f"   结构完整(70行×32槽): {ok_struct}")
    print(f"   目标段已清空: {ok_cleared}")
    print(f"   其它行保持不变(row5): {ok_kept}")
    print(f"   >>> 回环 {'✅ 通过' if (ok_struct and ok_cleared and ok_kept) else '❌ 失败'}")

print("\n### 3) 找 exercisescore00 对应的可玩项目(扫描所有 356 张表的交叉引用)")
hits = []
for f in sorted(glob.glob(DB + "*.bundle")):
    name = os.path.basename(f)[:-7]
    if name.startswith("exercisescore") or name.startswith("lecturescore"):
        continue
    try:
        e = UnityPy.load(f)
        m = next((o for o in e.objects if o.type.name == "MonoBehaviour"), None)
        if not m: continue
        s = json.dumps(m.read_typetree(), ensure_ascii=False, default=str)
    except Exception:
        continue
    if "Score00" in s or "score00" in s:
        # 找含 Score00 的具体片段
        idx = s.find("core00")
        hits.append((name, s[max(0, idx - 120):idx + 60]))
print(f"   引用 'Score00' 的表: {len(hits)} 张")
for name, snip in hits[:12]:
    print(f"   [{name}] …{snip}…")

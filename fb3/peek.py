import sys, UnityPy
print("UnityPy", getattr(UnityPy, "__version__", "?"))

def peek(path, label):
    print("\n" + "="*70)
    print(f"### {label}\n    {path.split('/')[-1]}")
    try:
        env = UnityPy.load(path)
    except Exception as e:
        print(f"  load 失败: {e!r}"); return
    objs = list(env.objects)
    print(f"  对象数: {len(objs)}  类型: {[o.type.name for o in objs]}")
    for o in objs:
        tn = o.type.name
        if tn in ("AssetBundle",):
            try:
                d = o.read(); print(f"  [AssetBundle] name={getattr(d,'m_Name',getattr(d,'name','?'))}")
            except Exception as e:
                print(f"  [AssetBundle] read err {e!r}")
            continue
        # MonoBehaviour / ScriptableObject
        print(f"  --- {tn} (path_id={o.path_id}) ---")
        # 1) 试 typetree（若 bundle 带类型树）
        tree = None
        try:
            tree = o.read_typetree()
        except Exception as e:
            print(f"      typetree 不可用: {e.__class__.__name__}")
        if tree:
            import json
            s = json.dumps(tree, ensure_ascii=False, default=str)
            print(f"      typetree keys: {list(tree.keys())}")
            print(f"      typetree(截断): {s[:1500]}")
            continue
        # 2) 退回原始字节
        raw = None
        for meth in ("get_raw_data", "raw_data"):
            try:
                raw = getattr(o, meth)() if callable(getattr(o, meth, None)) else getattr(o, meth, None)
                if raw: break
            except Exception:
                pass
        if raw is None:
            try:
                d = o.read(); raw = getattr(d, "raw_data", None)
            except Exception as e:
                print(f"      read err {e!r}")
        if raw:
            print(f"      raw {len(raw)} bytes, hex head: {raw[:48].hex()}")
            # 抽可读 ASCII 串
            import re
            strs = re.findall(rb"[\x20-\x7e]{4,}", raw)
            print(f"      可读串({len(strs)}): {[s.decode() for s in strs[:25]]}")

base = "/Users/zhongyi/Documents/switch_exploration/fb3/romfs_dump/NCA FS/User/Extracted/Fit Boxing 3 -Your パーソナルトレーナー- 1.3.0 [0100AC101BFA2800][v524288][UPD]/Program #0/1/Data/StreamingAssets/aa/Switch/defaultassets_assets_database/"
peek(base + "exercisescore00.bundle", "谱面 exercisescore00")
peek(base + "exerciseactiondata.bundle", "动作定义 exerciseactiondata")
peek(base + "musiclistdata.bundle", "歌单 musiclistdata")

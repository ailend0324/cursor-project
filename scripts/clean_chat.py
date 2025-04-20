import sys, logging, time
from pathlib import Path
from datetime import datetime
import pandas as pd
import yaml
import subprocess, shutil

# ---------- 配置区：后续只改这里 ----------
with open("config.yaml", "r", encoding="utf-8") as f:
    RULES = yaml.safe_load(f)
TIMESTAMP = datetime.now().strftime("%Y%m%dT%H%M%S")
# ----------------------------------------

def auto_git_commit(files: list[Path], msg: str):
    """把指定文件列表提交进 Git；仓库不存在时自动跳过"""
    if not Path(".git").exists():
        logging.warning("未初始化 git 仓库，已跳过提交")
        return
    # 把 Path 转成 str
    files_str = [str(f) for f in files if f.exists()]
    try:
        subprocess.run(["git", "add", *files_str], check=True)
        subprocess.run(["git", "commit", "-m", msg], check=True)
        logging.info(f"已 git commit: {msg}")
    except subprocess.CalledProcessError as e:
        logging.error(f"git 提交失败: {e}")

# ---------- 日志设置 ----------
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=log_dir / "clean_chat.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# ----------------------------

def load_raw(path: Path) -> pd.DataFrame:
    logging.info(f"Load raw file: {path}")
    return pd.read_excel(path)

def clean_data(df: pd.DataFrame, rules: dict) -> tuple[pd.DataFrame, list[str]]:
    changes = []
    # 1. 删除关键字段缺失行
    before = len(df)
    df = df.dropna(subset=rules["drop_if_null"])
    changes.append(f"删除 {before-len(df)} 行（{rules['drop_if_null']} 为空）")
    # 2. 填充缺失值
    for col, value in rules["fillna"].items():
        n_null = df[col].isna().sum()
        if n_null:
            df[col] = df[col].fillna(value)
            changes.append(f"填充 {col} 缺失 {n_null} 个 → '{value}'")
    return df, changes

def save_clean(df: pd.DataFrame, raw_path: Path) -> Path:
    out_name = f"{raw_path.stem}_cleaned_{TIMESTAMP}.xlsx"
    out_path = Path("data/cleaned") / out_name
    df.to_excel(out_path, index=False)
    logging.info(f"Saved cleaned file: {out_path}")
    return out_path

def make_report(meta: dict, raw_path: Path, clean_path: Path, changes: list[str]) -> Path:
    report_name = f"{raw_path.stem}_report_{TIMESTAMP}.md"
    report_path = Path("reports") / report_name
    head = f"# 数据清洗报告\n\n生成时间: {meta['now']}\n\n原始文件: {raw_path}\n输出文件: {clean_path}\n"
    summary = f"\n## 关键变更\n\n" + "\n".join([f"- {c}" for c in changes])
    report_path.write_text(head + summary, encoding="utf-8")
    logging.info(f"Saved report: {report_path}")
    return report_path

def run_once(raw_file: str):
    raw_path = Path(raw_file)
    df_raw = load_raw(raw_path)
    df_clean, changes = clean_data(df_raw, RULES)
    clean_path = save_clean(df_clean, raw_path)
    meta = {"now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    report_path = make_report(meta, raw_path, clean_path, changes)
    # ---- 自动 git commit ----
    auto_git_commit([clean_path, report_path, Path("logs/clean_chat.log")],
                    f"clean {raw_path.name} {TIMESTAMP}")
    print(f"✅ 清洗完成，输出: {clean_path}")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        p = Path(arg)
        if p.is_file():
            run_once(p)
        elif p.is_dir():
            for file in p.glob("*.xlsx"):
                run_once(file)
        else:
            print("输入既不是文件也不是文件夹，请检查路径")
    else:
        print("用法：")
        print("  python scripts/clean_chat.py <原始.xlsx>")
        print("  python scripts/clean_chat.py <目录>")
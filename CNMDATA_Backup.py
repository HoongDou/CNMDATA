"""
任务名称
name: CNMDATA_Backup
定时规则
cron: 0 0 2 1,11,21 * *
"""


import os
import zipfile
import shutil
from datetime import datetime


def compress_directory_by_month(pull_dir, exclude_files=None):
    """
    将目录下的图片按月份压缩，只处理上个月及更早的文件
    文件名格式需为 YYYYMMDDHHmmSS.PNG / .png
    """
    if exclude_files is None:
        exclude_files = []

    if not os.path.exists(pull_dir):
        print(f"错误：目录 {pull_dir} 不存在")
        return False

    now = datetime.now()
    current_month = now.strftime("%Y%m")  # 当前月，例如 202506

    # 按月份归组：{ "202505": ["202505010001.PNG", ...], ... }
    month_files = {}

    for item in os.listdir(pull_dir):
        item_path = os.path.join(pull_dir, item)

        # 跳过排除文件、zip文件、目录
        if item in exclude_files:
            continue
        if item.lower().endswith('.zip'):
            continue
        if not os.path.isfile(item_path):
            continue

        # 从文件名提取月份，文件名格式：YYYYMMDDHHmmSS.PNG
        name_without_ext = os.path.splitext(item)[0]
        if len(name_without_ext) >= 6:
            file_month = name_without_ext[:6]  # 取前6位 YYYYMM
        else:
            print(f"跳过无法识别日期的文件: {item}")
            continue

        # 只处理上个月及更早的文件，当月文件跳过
        if file_month >= current_month:
            continue

        if file_month not in month_files:
            month_files[file_month] = []
        month_files[file_month].append(item)

    if not month_files:
        print(f"[{pull_dir}] 没有需要归档的历史文件（当月文件不处理）")
        return True

    # 按月份逐一压缩
    for month, files in sorted(month_files.items()):
        zip_filename = f"archive_{month}.zip"
        zip_path = os.path.join(pull_dir, zip_filename)

        # 如果该月的 zip 已存在，追加进去
        mode = 'a' if os.path.exists(zip_path) else 'w'
        print(f"\n[{pull_dir}] 处理 {month}，共 {len(files)} 个文件，模式: {'追加' if mode == 'a' else '新建'}")

        try:
            with zipfile.ZipFile(zip_path, mode, zipfile.ZIP_DEFLATED) as zipf:
                existing_names = set(zipf.namelist()) if mode == 'a' else set()
                for file_name in files:
                    if file_name in existing_names:
                        print(f"  已存在，跳过: {file_name}")
                        continue
                    file_path = os.path.join(pull_dir, file_name)
                    zipf.write(file_path, file_name)
                    print(f"  已压缩: {file_name}")

            print(f"  压缩完成: {zip_filename}")

            # 压缩成功后删除原文件
            for file_name in files:
                file_path = os.path.join(pull_dir, file_name)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"  删除文件 {file_name} 时出错: {e}")

            print(f"  原文件已清理完毕")

        except Exception as e:
            print(f"  压缩 {month} 时出错: {e}")
            return False

    return True


def main():
    print("=" * 50)
    print("雷达图月度归档工具")
    print("=" * 50)
    print(f"当前工作目录: {os.getcwd()}")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    print("\n--- 处理全国雷达图 ./Pull ---")
    results.append(compress_directory_by_month(
        pull_dir="./Pull",
        exclude_files=["last_success.json"]
    ))

    print("\n--- 处理广州雷达图 ./Pull_GZ ---")
    results.append(compress_directory_by_month(
        pull_dir="./Pull_GZ",
        exclude_files=["last_success.json"]
    ))

    print("\n" + "=" * 50)
    if all(results):
        print("所有目录归档完成！")
    else:
        print("部分目录归档时出现错误，请检查日志")


if __name__ == "__main__":
    main()

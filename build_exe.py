import os
import sys
import subprocess

def build_exe():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置输出目录
    dist_dir = os.path.join(current_dir, "dist")
    
    # 构建命令
    cmd = [
        sys.executable, 
        "-m", 
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=TTML转LYS工具",
        "--add-data=log;log",
        os.path.join(current_dir, "TTML_to_LYS_GUI.py")
    ]
    
    # 执行命令
    print("执行命令:", " ".join(cmd))
    subprocess.call(cmd)
    
    print("\n构建完成！")
    print(f"可执行文件位于: {os.path.join(dist_dir, 'TTML转LYS工具.exe')}")

if __name__ == "__main__":
    build_exe()
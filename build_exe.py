import os
import sys
import subprocess
import shutil
import importlib
import pkg_resources
import time

def is_package_installed(package_name):
    """检查包是否已安装 - 使用更可靠的方法"""
    try:
        # 方法1: 使用pkg_resources
        pkg_resources.get_distribution(package_name)
        return True
    except pkg_resources.DistributionNotFound:
        try:
            # 方法2: 尝试导入
            __import__(package_name)
            return True
        except ImportError:
            # 方法3: 使用pip list查找
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "list"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return package_name.lower() in result.stdout.lower()
            except:
                return False

def install_package(package_name):
    """安装指定的包"""
    print(f"正在安装 {package_name}...")
    
    try:
        # 运行安装命令并实时显示输出
        process = subprocess.Popen(
            [sys.executable, "-m", "pip", "install", "--user", package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # 实时输出安装进度
        for line in process.stdout:
            print(line, end='')
        
        # 等待安装完成
        process.wait()
        
        # 检查安装是否成功
        if process.returncode != 0:
            print(f"\n安装 {package_name} 失败，返回代码: {process.returncode}")
            return False
        
        # 确认安装是否成功
        time.sleep(1)  # 短暂等待，确保安装完成
        if is_package_installed(package_name):
            print(f"\n{package_name} 安装成功!")
            return True
        else:
            print(f"\n安装后无法检测到 {package_name}，但安装命令已成功执行")
            # 安装命令成功但检测不到，也返回成功，让构建继续
            return True
            
    except Exception as e:
        print(f"\n安装过程中发生错误: {str(e)}")
        return False

def build_exe():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 检查pip是否最新版本
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=False)
    except:
        pass  # 如果更新失败，忽略错误
    
    # 检查所有必需的包
    required_packages = ["pyinstaller", "requests", "loguru", "pyperclip"]
    for package in required_packages:
        if not is_package_installed(package):
            print(f"未检测到{package}，准备安装...")
            success = install_package(package)
            if not success and package == "pyinstaller":
                print("\n自动安装PyInstaller失败。请尝试以下步骤:")
                print("1. 使用管理员权限打开命令提示符")
                print(f"2. 运行: {sys.executable} -m pip install --user pyinstaller")
                print("3. 安装完成后重新运行此脚本")
                if not os.environ.get('GITHUB_ACTIONS'):  # 只在非GitHub Actions环境中等待用户输入
                    input("\n按Enter键退出...")
                sys.exit(1)
    
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if not current_dir:  # 如果为空，使用当前目录
        current_dir = os.getcwd()
    
    # 设置输出目录
    dist_dir = os.path.join(current_dir, "dist")
    
    
    # 确定主程序文件
    main_script = "TTML_to_Lyricify_Syllable_GUI.py"
    main_script_path = os.path.join(current_dir, main_script)
    
    if not os.path.exists(main_script_path):
        main_script = "TTML_to_LYS_GUI.py"
        main_script_path = os.path.join(current_dir, main_script)
        
    if not os.path.exists(main_script_path):
        print(f"错误: 找不到主程序文件。请确保以下文件之一存在:")
        print(f"  - {os.path.join(current_dir, 'TTML_to_Lyricify_Syllable_GUI.py')}")
        print(f"  - {os.path.join(current_dir, 'TTML_to_LYS_GUI.py')}")
        if not os.environ.get('GITHUB_ACTIONS'):  # 只在非GitHub Actions环境中等待用户输入
            input("\n按Enter键退出...")
        sys.exit(1)
    
    # 直接搜索可执行文件
    pyinstaller_paths = [
        # 可能的PyInstaller可执行文件路径
        os.path.join(os.path.dirname(sys.executable), "Scripts", "pyinstaller.exe"),
        os.path.join(os.path.dirname(sys.executable), "pyinstaller.exe"),
    ]
    
    pyinstaller_cmd = None
    for path in pyinstaller_paths:
        if os.path.exists(path):
            pyinstaller_cmd = path
            break
    
    # 构建命令
    if pyinstaller_cmd:
        # 使用绝对路径
        cmd = [
            pyinstaller_cmd,
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--name=TTML_to_LYS_Tool",
            "--hidden-import=requests",
            "--hidden-import=loguru",
            "--hidden-import=pyperclip",
            "--hidden-import=tkinterdnd2",
            "--add-data=icon.ico;.",
            "--icon=icon.ico",  # 添加图标文件作为资源
        ]
    else:
        # 使用Python模块
        cmd = [
            sys.executable, 
            "-m", 
            "PyInstaller",
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--name=TTML_to_LYS_Tool",
            "--hidden-import=requests",
            "--hidden-import=loguru",
            "--hidden-import=pyperclip",
            "--hidden-import=tkinterdnd2",
            "--add-data=icon.ico;.",
            "--icon=icon.ico",  # 添加图标文件作为资源
        ]

    # 添加主程序文件
    cmd.append(main_script_path)
    
    # 执行命令
    print("\n执行命令:", " ".join(cmd))
    try:
        # 使用Popen实时显示输出
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # 实时显示输出
        for line in process.stdout:
            print(line, end='')
        
        # 等待进程完成
        process.wait()
        
        # 检查是否成功
        if process.returncode != 0:
            print(f"\n构建失败，返回代码: {process.returncode}")
            sys.exit(1)
            
        print("\n构建完成！")
        print(f"可执行文件位于: {os.path.join(dist_dir, 'TTML_to_LYS_Tool.exe')}")
        
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        build_exe()
    except Exception as e:
        print(f"\n发生意外错误: {str(e)}")
    finally:
        if not os.environ.get('GITHUB_ACTIONS'):  # 只在非GitHub Actions环境中等待用户输入
            input("\n按Enter键退出...")  # 防止窗口立即关闭
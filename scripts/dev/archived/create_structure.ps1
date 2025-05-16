# PowerShell脚本：创建QTE项目目录结构

# 创建主要模块目录
$directories = @(
    "qte\execution",
    "qte\portfolio",
    "qte\analysis",
    "qte\ml",
    "qte\utils",
    "strategies",
    "strategies\traditional",
    "strategies\ml",
    "examples",
    "tests",
    "tests\unit",
    "tests\integration",
    "tests\performance",
    "docs",
    "docs\api",
    "docs\tutorials",
    "docs\architecture"
)

# 创建目录
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created directory: $dir"
    } else {
        Write-Host "Directory already exists: $dir"
    }
}

# 创建必要的Python包初始化文件
$init_files = @(
    "qte\__init__.py",
    "qte\core\__init__.py",
    "qte\data\__init__.py",
    "qte\execution\__init__.py",
    "qte\portfolio\__init__.py",
    "qte\analysis\__init__.py",
    "qte\ml\__init__.py",
    "qte\utils\__init__.py",
    "strategies\__init__.py",
    "strategies\traditional\__init__.py",
    "strategies\ml\__init__.py"
)

# 创建__init__.py文件
foreach ($file in $init_files) {
    if (!(Test-Path $file)) {
        New-Item -ItemType File -Path $file -Force
        Write-Host "Created file: $file"
    } else {
        Write-Host "File already exists: $file"
    }
}

Write-Host "项目目录结构创建完成！" 
# 环境配置说明

## Conda环境
```bash
# 激活环境
conda activate ./env

# 安装依赖
pip install -r requirements.txt

# 更新环境（当依赖变更时）
conda env update --prefix ./env --file environment.yml  --prune
```

## 常见问题
Q: 环境路径被误提交怎么办？
A: 删除env目录后执行：
```
git rm -r --cached env/
git commit -m "remove env from version control"
```
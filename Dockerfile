# ============================================================
# NDXinfo - NASDAQ 每日分析报告生成器
# 多阶段 Docker 镜像构建文件
#
# 构建命令: docker build -t ndxinfo .
# 运行命令: docker run --rm -v $(pwd)/reports:/app/reports ndxinfo
# ============================================================

# ============================================================
# 阶段一：构建阶段（builder）
#   仅安装 Python 依赖，利用层缓存加速后续构建
# ============================================================
FROM python:3.11-slim AS builder

# 设置工作目录
WORKDIR /app

# 关闭 pip 缓存与版本检查，减小镜像体积
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 先单独复制 requirements.txt，利用 Docker 层缓存
# 仅当依赖列表变化时才重新执行 pip install
COPY requirements.txt ./

# 将依赖安装到用户目录（~/.local），便于第二阶段精确复制
RUN pip install --user --no-cache-dir -r requirements.txt

# ============================================================
# 阶段二：运行阶段（runtime）
#   精简最终镜像，仅包含运行所需文件
# ============================================================
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 从构建阶段复制已安装的 Python 依赖包
COPY --from=builder /root/.local /root/.local

# 环境变量配置：
#   PATH              - 将用户安装的可执行文件加入路径
#   PYTHONUNBUFFERED  - 禁用输出缓冲，日志实时打印
#   PYTHONDONTWRITEBYTECODE - 不生成 .pyc 文件
#   TZ                - 时区设为亚洲/上海（北京时间）
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai

# Feature Flags 默认值（可通过 docker run -e 覆盖）
# 与 config.py 中的开关一一对应
ENV ENABLE_BACKTEST=true \
    ENABLE_NEWS_SENTIMENT=true \
    ENABLE_SECTOR_ETF=true \
    ENABLE_COMPARISON=true \
    ENABLE_HK_A_SHARE=false \
    ENABLE_ML_PREDICT=false

# 复制项目全部源码文件（受 .dockerignore 控制）
COPY . .

# 镜像标签（OCI 标准标签）
LABEL org.opencontainers.image.title="NDXinfo - NASDAQ 每日分析报告" \
      org.opencontainers.image.description="NASDAQ 纳斯达克每日分析报告自动生成工具，含技术指标、回测、板块轮动与新闻情绪分析" \
      org.opencontainers.image.source="https://github.com/NDXinfo/NDXinfo" \
      org.opencontainers.image.licenses="MIT" \
      maintainer="NDXinfo"

# 默认启动命令：生成当日分析报告
CMD ["python", "nasdaq_analyzer.py"]

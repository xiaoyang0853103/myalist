FROM xiaoyaliu/alist:latest

# 设置工作目录
WORKDIR /opt/alist

# 暴露端口（小雅通常使用 5678）
EXPOSE 5678

# 启动命令
CMD ["./alist", "server"]

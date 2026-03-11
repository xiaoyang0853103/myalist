# 🔓 TVBox 接口自动解密工具

自动解密 TVBox 接口地址，支持 Base64、AES 等多种加密方式，每天定时更新。

## ✨ 功能特性

- 🤖 **自动解密**：智能识别 Base64、AES 等加密方式
- ⏰ **定时执行**：每天北京时间 08:00 和 20:00 自动运行
- 🖱️ **手动触发**：支持 GitHub Actions 手动执行
- 📝 **双格式输出**：生成 `live.txt`（合并内容）和 `live_report.json`（详细报告）
- 🔄 **自动提交**：解密结果自动提交到仓库

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `url.txt` | 待解密的接口地址列表（每行一个URL） |
| `decrypt.py` | 主解密脚本 |
| `live.txt` | 解密后的合并结果（自动生成） |
| `live_report.json` | JSON格式的详细报告（自动生成） |

## 🚀 使用方法

### 1. 添加URL
编辑 `url.txt` 文件，添加需要解密的接口地址：

```text
https://gitee.com/yimi321/tv/raw/master/tv.png
https://dsj-1312694395.cos.ap-guangzhou.myqcloud.com/dsj10.1.txt
https://d.kstore.dev/download/12441/ds9.txt

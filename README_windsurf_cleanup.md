# Windsurf 完整清理工具使用说明

## 📋 概述

这个脚本可以帮助你完全删除Mac系统中的Windsurf应用程序及其所有相关文件，包括：

- **主应用程序** (约556MB): `/Applications/Windsurf.app`
- **用户配置** (约1.2GB): `~/.windsurf/` (包含扩展和设置)
- **系统偏好设置**: `~/Library/Preferences/com.exafunction.windsurf.plist`
- **缓存文件**: `~/Library/Caches/com.exafunction.windsurf/`
- **浏览器数据**: Chrome中的windsurf相关数据

**总共释放空间**: 约1.8GB

## 🚀 使用方法

### 第一步：运行脚本
```bash
./windsurf_cleanup.sh
```

### 第二步：查看检测结果
脚本会自动检测你系统中的所有Windsurf相关文件，并显示每个文件的大小

### 第三步：确认删除
- 脚本会要求你输入 `YES` 来确认删除
- **注意**：删除后无法恢复！

### 第四步：等待完成
脚本会自动：
- 删除所有相关文件
- 结束运行中的Windsurf进程
- 验证清理结果
- 生成详细日志

## ⚠️  重要提醒

### 删除前请考虑：
1. **备份重要数据**：如果你有重要的Windsurf配置或扩展，请先备份
2. **确认不再使用**：删除后如需重新使用Windsurf，需要重新安装和配置
3. **关闭应用程序**：运行脚本前建议先退出Windsurf

### 安全特性：
- ✅ 需要明确确认（输入"YES"）才会执行删除
- ✅ 详细的操作日志记录
- ✅ 彩色输出，便于查看进度
- ✅ 删除前显示文件大小统计
- ✅ 删除后验证清理结果

## 📝 日志文件

脚本会生成一个详细的日志文件：`windsurf_cleanup_YYYYMMDD_HHMMSS.log`

日志包含：
- 操作时间戳
- 删除的文件列表
- 成功/失败状态
- 错误信息（如有）

## 🔧 故障排除

### 如果某些文件删除失败：
1. 确保Windsurf应用程序已完全退出
2. 检查文件权限
3. 使用管理员权限运行脚本：`sudo ./windsurf_cleanup.sh`

### 如果仍有残留文件：
查看日志文件中的详细信息，手动删除剩余文件

## 📞 需要帮助？

如果你在使用过程中遇到任何问题，可以：
1. 查看生成的日志文件
2. 联系技术支持
3. 手动删除特定文件

## 🎯 清理验证

脚本完成后，你可以运行以下命令验证清理效果：

```bash
# 检查应用程序是否还存在
ls -la /Applications/ | grep -i windsurf

# 检查用户配置是否还存在  
ls -la ~/.windsurf

# 检查系统偏好设置
ls -la ~/Library/Preferences/ | grep windsurf
```

如果这些命令都没有输出，说明Windsurf已被完全清理！ 
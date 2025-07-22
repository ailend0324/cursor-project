# VPN监控与管理系统

这是一个智能VPN监控系统，可以自动检测VPN连接状态并在出现问题时发出通知。

## 📋 项目结构

```
/
├── vpn/                    # VPN监控相关文件
│   ├── vpn_monitor.sh     # VPN状态监控脚本
│   ├── vpn_reconnect.sh   # VPN重连和网络修复脚本
│   ├── vpn_monitor.log    # 监控日志文件
│   ├── vpn_stop.flag      # 停止脚本的标志文件
│   ├── vpn_fix_errors.sh  # VPN错误修复脚本
│   ├── vpn_deep_fix.sh    # VPN深度修复脚本
│   ├── cleanup_check.sh   # StrongVPN完全清理检查脚本
│   └── 使用说明.md        # 中文使用说明
├── ai_service/            # AI服务模块
├── smart_customer_agent/  # 智能客服代理
├── smart_service_agent/   # 智能服务代理
└── README.md             # 项目说明文档
```

## 🔧 VPN监控系统功能

### 1. 自动监控VPN连接状态
- 每20秒检查一次VPN连接
- 验证当前IP是否为允许的VPN IP地址
- 记录详细的连接日志

### 2. 智能网络修复
- 自动检测网络连接问题
- 重置DNS缓存和网络接口
- 清理异常的VPN路由

### 3. 实时通知系统
- 当VPN断开时发送桌面通知
- 记录所有操作到日志文件
- 支持手动停止监控

## 🚨 常见错误解决方案

### StrongVPN/IPVanish连接错误

当你看到这些错误时：
```
Error Reading the PID file for OpenVPN: The file "ipvanish3-openvpn.pid" couldn't be opened
Error Deleting the PID file for OpenVPN: "ipvanish3-openvpn.pid" couldn't be removed
Error occurred copying OpenVPNCertificatePath
ifconfig: ioctl (SIOCDIFADDR): Can't assign requested address
```

**简单解释**：
- PID文件就像程序的"身份证"，文件丢失了
- 证书文件就像门钥匙，复制失败了
- 网络地址分配出错了

**解决步骤**：

#### 第一步：清理VPN进程
```bash
# 停止所有VPN相关进程
sudo pkill openvpn
sudo pkill strongvpn
sudo pkill ipvanish
```

#### 第二步：清理网络配置
```bash
# 重置网络接口
sudo ifconfig tun0 down 2>/dev/null
sudo ifconfig ppp0 down 2>/dev/null

# 刷新DNS缓存
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

#### 第三步：重启VPN应用
1. 完全退出StrongVPN应用
2. 等待10秒钟
3. 重新启动应用
4. 选择不同的服务器重新连接

## 🛠️ 使用方法

### 启动VPN监控
```bash
# 进入VPN目录
cd /Users/boxie/cursor/vpn

# 启动监控脚本（后台运行）
nohup ./vpn_monitor.sh &

# 或启动完整的重连监控
nohup ./vpn_reconnect.sh &
```

### 停止VPN监控
```bash
# 创建停止标志文件
touch /Users/boxie/cursor/vpn_stop.flag

# 或直接终止进程
pkill -f vpn_monitor.sh
pkill -f vpn_reconnect.sh
```

### 查看监控日志
```bash
# 实时查看日志
tail -f vpn/vpn_monitor.log

# 查看最近的错误
grep "错误\|Error" vpn/vpn_monitor.log | tail -10
```

## ⚙️ 配置说明

### 允许的VPN IP地址列表
在`vpn_monitor.sh`和`vpn_reconnect.sh`中修改：
```bash
VPN_IPS=("207.204.224.*" "192.200.144.*" "216.169.131.*" "173.255.168.*")
```

### 监控间隔设置
```bash
CHECK_INTERVAL=20  # 检查间隔（秒）
```

## 🔍 故障排除

### 如果VPN连接但无法上网
1. 检查DNS设置：`nslookup google.com`
2. 重置DNS：`sudo dscacheutil -flushcache`
3. 检查路由表：`netstat -rn`

### 如果脚本无法启动
1. 检查文件权限：`chmod +x vpn/*.sh`
2. 检查路径是否正确
3. 查看系统日志：`Console.app`

### 如果监控不准确
1. 更新VPN IP地址列表
2. 检查网络接口名称（tun0, ppp0等）
3. 调整检查间隔时间

## 📱 通知设置

系统会在以下情况发送桌面通知：
- VPN连接断开
- 网络连接异常
- 网络修复成功/失败

确保在"系统偏好设置 > 通知"中允许终端发送通知。

## 🔒 安全说明

- 所有脚本都以当前用户权限运行
- 需要sudo权限来修改网络配置
- 日志文件不包含敏感信息
- IP地址信息仅用于连接验证

## 📞 技术支持

如果遇到问题：
1. 查看日志文件找到具体错误
2. 尝试重启VPN应用
3. 检查网络连接是否正常
4. 确认VPN服务商状态

## 🧹 StrongVPN完全清理

**更新时间**: 2025年5月29日  
**状态**: ✅ 已完全清理

### 清理成果总结

经过深度清理检查，StrongVPN的所有相关文件已被彻底清理：

#### ✅ 已清理的文件类型：
1. **应用程序文件** - StrongVPN.app 已手动删除
2. **用户配置文件** - 所有Library目录下的配置已清理
3. **系统级配置** - LaunchDaemons和PrivilegedHelperTools已清理
4. **缓存文件** - HTTPStorages和崩溃报告缓存已清理
5. **临时文件** - 所有PID文件和临时文件已清理
6. **安装包** - StrongVPN.dmg已删除

#### ⚠️ 需要重启清理的：
- **系统扩展** - 位于`/Library/SystemExtensions`的网络扩展需要重启后自动清理

### 使用的清理工具

1. **vpn_deep_fix.sh** - 深度修复和清理脚本
2. **cleanup_check.sh** - 全面的清理检查脚本

### 清理验证

- ✅ 无残留进程
- ✅ 无VPN网络接口
- ✅ 无用户配置文件
- ✅ 无系统配置文件
- ✅ 无临时文件
- ⚠️ 系统扩展需重启后清理

### 建议

1. **重启电脑** - 确保系统扩展完全清理
2. **选择新的VPN方案** - 建议使用其他更稳定的VPN服务
3. **避免重新安装StrongVPN** - 该软件存在严重的兼容性问题

---

**作者**：AI助手  
**创建时间**：2025年1月  
**最后更新**：2025年5月29日 - 完成StrongVPN完全清理  

这个系统不仅能监控VPN连接，还能彻底清理有问题的VPN软件！ 🛡️ 
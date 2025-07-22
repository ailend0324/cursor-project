# StrongVPN 故障排除指南

## 📋 概述

本文档记录了在 macOS 15.5 (24F74) 系统上解决 StrongVPN 连接问题的完整故障排除过程，包括问题诊断、解决方案和最终配置。

---

## 🖥️ 系统环境

- **操作系统**: macOS 15.5 (24F74)
- **StrongVPN 版本**: 2.4.4 (126629)
- **网络环境**: CHINANET-BACKBONE，广州
- **真实IP**: 218.18.137.26

---

## ⚠️ 初始问题症状

### 连接错误日志
```
Error Reading the PID file for OpenVPN: The file "ipvanish3-openvpn.pid" couldn't be opened
Error Deleting the PID file for OpenVPN: "ipvanish3-openvpn.pid" couldn't be removed
Error occurred copying OpenVPNCertificatePath
OpenVPN terminated unexpectedly
```

### 网络测试结果
- StrongVPN 服务器 IP 完全无法 ping 通（100% 丢包）
- 基础网络连接正常（8.8.8.8 可达，延迟 9ms）

---

## 🔍 问题诊断过程

### 1. VPN 工具冲突检测

#### 发现的冲突软件
```bash
# 检查VPN相关进程
ps aux | grep -iE "(vpn|proxy|tunnel|wireguard|openvpn|express|nord)"

# 检查系统启动项
sudo launchctl list | grep -i vpn
launchctl list | grep -i vpn
```

**发现的冲突源：**
- ✅ ProtonVPN WireGuard 扩展残留
- ✅ ExpressVPN 完整安装（进程 + 启动项）
- ✅ PG2Ray 应用
- ✅ V2rayU 启动项配置
- ✅ IPVanish 配置残留

### 2. 网络连通性分析

#### 服务器可达性测试
```bash
# 测试不同服务器
ping -c 3 hk1.strongvpn.com      # 香港：100% 丢包
ping -c 3 jp1.strongvpn.com      # 日本：100% 丢包  
ping -c 3 us-west1.strongvpn.com # 美国西海岸：100% 丢包
ping -c 3 108.171.117.52         # NYC服务器：100% 丢包

# 端口连接测试
nc -z -v -w 3 hk1.strongvpn.com 443  # HTTPS端口：超时
```

**结论**: 网络层面存在 IP 级别的屏蔽

### 3. 系统配置检查

#### 代理设置检查
```bash
networksetup -getwebproxy "Wi-Fi"
networksetup -getsecurewebproxy "Wi-Fi"  
networksetup -getsocksfirewallproxy "Wi-Fi"
```
**结果**: 所有代理均已禁用

#### DNS 配置
```bash
scutil --dns | head -20
```
**发现**: 使用国内 DNS（223.5.5.5, 114.114.114.114）

---

## 🛠️ 解决方案实施

### 阶段1：清理 VPN 工具冲突

#### 1.1 移除 ProtonVPN WireGuard 扩展
```bash
# 通过系统偏好设置 → 网络 → VPN 手动删除
```

#### 1.2 完全卸载 ExpressVPN
```bash
# 停止服务
sudo launchctl stop com.expressvpn.expressvpnd
sudo launchctl unload -w /Library/LaunchDaemons/com.expressvpn.expressvpnd.plist

# 删除文件
sudo rm -rf "/Library/Application Support/com.expressvpn.ExpressVPN"
sudo rm -f "/Library/LaunchDaemons/com.expressvpn.expressvpnd.plist"
sudo rm -f "/Library/Application Support/Mozilla/NativeMessagingHosts/com.expressvpn.helper.json"
sudo rm -f "/Library/Google/Chrome/NativeMessagingHosts/com.expressvpn.helper.json"
sudo rm -f "/Library/Microsoft/Edge/NativeMessagingHosts/com.expressvpn.helper.json"

# 清理用户文件
rm -rf "/Users/boxie/Library/Application Support/com.expressvpn.ExpressVPN"
rm -f "/Users/boxie/Library/Preferences/com.expressvpn.ExpressVPN.plist"
rm -rf "/Users/boxie/Library/HTTPStorages/com.expressvpn.ExpressVPN"
```

#### 1.3 卸载 PG2Ray
```bash
sudo rm -rf "/Applications/PG2Ray.app"
rm -f "/Users/boxie/Library/Preferences/com.tan.pg2ray.plist"
rm -rf "/Users/boxie/Library/HTTPStorages/com.tan.pg2ray"
```

#### 1.4 清理 V2Ray 启动项
```bash
launchctl unload "/Users/boxie/Library/LaunchAgents/yanue.v2rayu.v2ray-core.plist"
rm -f "/Users/boxie/Library/LaunchAgents/yanue.v2rayu.v2ray-core.plist"
```

### 阶段2：StrongVPN 应用问题修复

#### 2.1 发现核心问题
通过深度搜索发现 StrongVPN 应用内部硬编码了 IPVanish 配置：

```bash
grep -r "ipvanish" "/Applications/StrongVPN.app"
```

**关键发现**:
```
/Applications/StrongVPN.app/Contents/Frameworks/VPNHelperAdapter.framework/Versions/A/Resources/config.ovpn:
writepid /tmp/ipvanish3-openvpn.pid
```

#### 2.2 临时修复方案
由于应用文件受系统保护无法修改，创建临时文件解决：

```bash
sudo touch /tmp/ipvanish3-openvpn.pid
sudo chmod 666 /tmp/ipvanish3-openvpn.pid
```

#### 2.3 重置 StrongVPN 配置
```bash
# 停止所有服务
sudo launchctl stop com.strongvpn.StrongVPN2-Helper
killall StrongVPN
sudo pkill -f strongvpn
sudo pkill -f openvpn

# 清理配置
sudo rm -rf "/Users/boxie/Library/Application Support/com.strongvpn.StrongVPN2-Client/"*

# 重启服务
sudo launchctl start com.strongvpn.StrongVPN2-Helper
open -a StrongVPN
```

---

## ✅ 最终成功配置

### StrongVPN 设置
- **协议**: OpenVPN
- **端口**: 53 (DNS)
- **加扰功能**: 启用 ✅
- **IPv6 泄漏保护**: 启用 ✅
- **自动重新连接**: 启用 ✅
- **中国优化**: 启用 ✅

### 连接结果
- **原始IP**: 218.18.137.26 (广州，中国)
- **VPN IP**: 108.171.96.29 (旧金山，美国)
- **延迟**: ~160ms
- **稳定性**: 0% 丢包

---

## 📊 性能测试

### 连接验证
```bash
# IP地址检查
curl -s "https://ipinfo.io/json" | python3 -m json.tool

# 网络延迟测试  
ping -c 3 8.8.8.8

# 连接稳定性
# 结果：158-166ms延迟，0%丢包
```

---

## 🔧 故障排除工具箱

### 常用诊断命令

#### VPN 进程检查
```bash
ps aux | grep -iE "(vpn|proxy|tunnel|wireguard|openvpn|ipsec|ikev2|sstp|v2ray|shadowsock|clash|surge|proxifier)"
```

#### 系统服务检查
```bash
sudo launchctl list | grep -i vpn
launchctl list | grep -i vpn
```

#### 网络接口检查
```bash
ifconfig | grep -E "(utun|tap|tun|ppp|ipsec|vpn)" -A 5 -B 1
```

#### 系统扩展检查
```bash
systemextensionsctl list
sudo systemextensionsctl list
```

#### 路由表检查
```bash
netstat -rn | grep -E "(default|0.0.0.0|utun|tun|ppp|vpn)"
```

#### 深度文件搜索
```bash
sudo find / -name "*vpn*" -o -name "*proxy*" 2>/dev/null | grep -v "/System/" | head -20
```

### 清理脚本模板

#### 通用 VPN 清理
```bash
#!/bin/bash
# 停止所有VPN相关进程
sudo pkill -f vpn
sudo pkill -f openvpn
sudo pkill -f wireguard
sudo pkill -f v2ray

# 清理临时文件
sudo rm -f /tmp/*vpn*.pid
sudo rm -f /tmp/*openvpn*
sudo rm -f /private/tmp/*vpn*

echo "VPN processes cleaned"
```

---

## ⚠️ 常见问题与解决方案

### 1. "ipvanish3-openvpn.pid" 错误
**原因**: StrongVPN 应用内部硬编码了 IPVanish 配置  
**解决**: 创建临时 PID 文件
```bash
sudo touch /tmp/ipvanish3-openvpn.pid
sudo chmod 666 /tmp/ipvanish3-openvpn.pid
```

### 2. 证书复制错误
**原因**: 多个 VPN 工具冲突或权限问题  
**解决**: 完全清理冲突软件并重置权限

### 3. 连接建立后立即断开
**原因**: Kill Switch 冲突或网络配置问题  
**解决**: 检查网络扩展和系统代理设置

### 4. 所有服务器 IP 被屏蔽
**原因**: 网络层面的 IP 级别屏蔽  
**解决**: 
- 使用端口 53 (DNS) 或 80 (HTTP)
- 启用加扰/混淆功能
- 尝试不同协议（OpenVPN → IKEv2）

---

## 🎯 预防措施

### 1. 避免多 VPN 工具并存
- 一次只安装和使用一个 VPN 应用
- 卸载时彻底清理所有相关文件

### 2. 定期检查系统启动项
```bash
# 定期执行检查
sudo launchctl list | grep -i vpn
launchctl list | grep -i vpn
```

### 3. 监控网络配置
```bash
# 检查代理设置
networksetup -getwebproxy "Wi-Fi"
networksetup -getsecurewebproxy "Wi-Fi"
networksetup -getsocksfirewallproxy "Wi-Fi"
```

### 4. 保持应用更新
定期更新 VPN 应用以获得最新的反审查技术

---

## 📞 技术支持信息

### StrongVPN 官方支持
- 官网: strongvpn.com
- 技术支持: 可报告 "ipvanish3-openvpn.pid" 配置问题

### 替代解决方案
如果问题持续，考虑：
1. 完全重新安装 StrongVPN
2. 尝试其他 VPN 服务商
3. 使用其他协议（IKEv2、WireGuard）

---

## 📝 更新日志

- **2025/06/05**: 初始版本，记录完整故障排除过程
- **问题状态**: ✅ 已解决，StrongVPN 稳定运行

---

## 🏷️ 标签

`StrongVPN` `macOS` `VPN故障排除` `网络诊断` `ExpressVPN冲突` `IPVanish配置` `OpenVPN` `网络审查` `系统清理` 
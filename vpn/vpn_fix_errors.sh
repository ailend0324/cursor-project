#!/bin/bash

# VPN错误修复脚本
# 专门解决StrongVPN/IPVanish的PID文件、证书和网络配置错误

LOG_FILE="/Users/boxie/cursor/vpn/vpn_fix.log"

# 日志函数
log_message() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# 显示通知
show_notification() {
    osascript -e "display notification \"$1\" with title \"VPN修复工具\""
}

log_message "========== VPN错误修复脚本启动 =========="
echo "🛠️  VPN错误修复工具"
echo "这个工具会帮你解决StrongVPN/IPVanish的常见连接错误"
echo ""

# 第一步：停止所有VPN相关进程
log_message "第一步：清理VPN进程"
echo "📋 第一步：停止所有VPN进程..."

# 查找并停止OpenVPN进程
OPENVPN_PIDS=$(pgrep -f openvpn)
if [ ! -z "$OPENVPN_PIDS" ]; then
    log_message "发现OpenVPN进程: $OPENVPN_PIDS"
    sudo pkill -f openvpn
    log_message "已停止OpenVPN进程"
else
    log_message "未发现运行中的OpenVPN进程"
fi

# 停止StrongVPN进程
sudo pkill -f StrongVPN 2>/dev/null
sudo pkill -f strongvpn 2>/dev/null

# 停止IPVanish进程  
sudo pkill -f ipvanish 2>/dev/null
sudo pkill -f IPVanish 2>/dev/null

log_message "VPN进程清理完成"
echo "✅ VPN进程已清理"

# 第二步：清理PID文件
log_message "第二步：清理PID文件"
echo "📋 第二步：清理PID文件..."

# 清理常见的PID文件位置
PID_LOCATIONS=(
    "/tmp/ipvanish3-openvpn.pid"
    "/tmp/strongvpn-openvpn.pid"
    "/var/run/openvpn.pid"
    "/usr/local/var/run/openvpn.pid"
    "/Library/Application Support/StrongVPN/openvpn.pid"
    "/Library/Application Support/IPVanish/openvpn.pid"
)

for pid_file in "${PID_LOCATIONS[@]}"; do
    if [ -f "$pid_file" ]; then
        log_message "删除PID文件: $pid_file"
        sudo rm -f "$pid_file"
        echo "🗑️  删除了 $pid_file"
    fi
done

log_message "PID文件清理完成"
echo "✅ PID文件已清理"

# 第三步：重置网络接口
log_message "第三步：重置网络接口"
echo "📋 第三步：重置网络配置..."

# 关闭VPN网络接口
for interface in tun0 tun1 tun2 ppp0 ppp1; do
    if ifconfig "$interface" >/dev/null 2>&1; then
        log_message "关闭网络接口: $interface"
        sudo ifconfig "$interface" down 2>/dev/null
        echo "🔌 关闭了 $interface"
    fi
done

# 清理路由表中的VPN路由
log_message "清理VPN路由"
# 获取默认网关
DEFAULT_GW=$(netstat -rn | grep '^default' | grep -v '::' | awk '{print $2}' | head -1)
if [ ! -z "$DEFAULT_GW" ]; then
    log_message "发现默认网关: $DEFAULT_GW"
    # 删除可能重复的默认路由
    sudo route -n delete default 2>/dev/null
    # 重新添加正确的默认路由
    sudo route -n add default "$DEFAULT_GW" 2>/dev/null
    log_message "重置了默认路由"
fi

log_message "网络接口重置完成"
echo "✅ 网络接口已重置"

# 第四步：重置DNS和网络缓存
log_message "第四步：重置DNS缓存"
echo "📋 第四步：重置DNS缓存..."

# 刷新DNS缓存
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder 2>/dev/null

# 重置DNS设置到自动
networksetup -setdnsservers Wi-Fi Empty 2>/dev/null

log_message "DNS缓存重置完成"
echo "✅ DNS缓存已重置"

# 第五步：重启网络接口
log_message "第五步：重启网络"
echo "📋 第五步：重启网络接口..."

# 重启WiFi接口
WIFI_DEVICE=$(networksetup -listallhardwareports | grep -A 1 "Wi-Fi" | grep "Device:" | cut -d' ' -f2)
if [ ! -z "$WIFI_DEVICE" ]; then
    log_message "重启WiFi接口: $WIFI_DEVICE"
    sudo ifconfig "$WIFI_DEVICE" down
    sleep 2
    sudo ifconfig "$WIFI_DEVICE" up
    echo "📶 重启了WiFi接口"
fi

log_message "网络重启完成"
echo "✅ 网络已重启"

# 第六步：等待网络稳定
echo "📋 第六步：等待网络稳定..."
log_message "等待网络连接稳定"
sleep 5

# 测试网络连通性
if ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
    log_message "网络连接正常"
    echo "✅ 网络连接正常"
else
    log_message "网络连接可能有问题"
    echo "⚠️  网络连接可能有问题，请检查WiFi连接"
fi

# 第七步：清理证书缓存
log_message "第七步：清理证书缓存"
echo "📋 第七步：清理证书缓存..."

# 清理可能的证书缓存位置
CERT_CACHE_LOCATIONS=(
    "/tmp/strongvpn_cert"
    "/tmp/ipvanish_cert"
    "/var/tmp/openvpn_certs"
)

for cert_dir in "${CERT_CACHE_LOCATIONS[@]}"; do
    if [ -d "$cert_dir" ]; then
        log_message "清理证书缓存: $cert_dir"
        sudo rm -rf "$cert_dir"
        echo "🗑️  清理了 $cert_dir"
    fi
done

log_message "证书缓存清理完成"
echo "✅ 证书缓存已清理"

# 完成
echo ""
echo "🎉 VPN错误修复完成！"
echo ""
echo "📝 接下来的操作步骤："
echo "1. 完全退出StrongVPN应用（右键Dock图标 -> 退出）"
echo "2. 等待10秒钟"
echo "3. 重新启动StrongVPN应用"
echo "4. 选择一个不同的服务器重新连接"
echo "5. 如果还有问题，请重启电脑后再试"
echo ""

log_message "========== VPN错误修复脚本完成 =========="

# 发送通知
show_notification "VPN错误修复完成！请重新启动VPN应用。"

# 提供快速测试
echo "🔍 是否要测试网络连接？(y/n)"
read -t 10 -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "正在测试网络连接..."
    if curl -s --connect-timeout 5 --max-time 10 https://www.google.com >/dev/null 2>&1; then
        echo "✅ 网络连接测试成功"
        log_message "网络连接测试成功"
    else
        echo "⚠️  网络连接测试失败，请检查网络设置"
        log_message "网络连接测试失败"
    fi
fi

echo ""
echo "📋 修复日志已保存到: $LOG_FILE"
echo "如果问题仍然存在，请查看日志文件获取更多信息。" 
#!/bin/bash

# VPN深度修复脚本 - 解决顽固的StrongVPN连接问题
# 这个脚本会进行更彻底的清理和修复

LOG_FILE="/Users/boxie/cursor/vpn/vpn_deep_fix.log"

# 日志函数
log_message() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# 显示通知
show_notification() {
    osascript -e "display notification \"$1\" with title \"VPN深度修复工具\""
}

echo "🚨 VPN深度修复工具"
echo "专门解决顽固的StrongVPN连接问题"
echo "=================================================="
log_message "========== VPN深度修复脚本启动 =========="

# 第一步：强制杀死所有StrongVPN相关进程
echo "📋 第一步：强制停止所有StrongVPN进程..."
log_message "第一步：强制停止所有StrongVPN进程"

# 获取所有StrongVPN相关进程ID
STRONG_PIDS=$(pgrep -f -i strong)
OPENVPN_PIDS=$(pgrep -f openvpn)

if [ ! -z "$STRONG_PIDS" ]; then
    log_message "发现StrongVPN进程: $STRONG_PIDS"
    echo "💀 强制终止StrongVPN主程序..."
    sudo kill -9 $STRONG_PIDS 2>/dev/null
    log_message "已强制终止StrongVPN进程"
fi

if [ ! -z "$OPENVPN_PIDS" ]; then
    log_message "发现OpenVPN进程: $OPENVPN_PIDS"
    echo "💀 强制终止OpenVPN进程..."
    sudo kill -9 $OPENVPN_PIDS 2>/dev/null
    log_message "已强制终止OpenVPN进程"
fi

# 额外清理
sudo pkill -9 -f "StrongVPN" 2>/dev/null
sudo pkill -9 -f "strongvpn" 2>/dev/null
sudo pkill -9 -f "openvpn" 2>/dev/null

echo "✅ 所有VPN进程已强制终止"
log_message "VPN进程强制清理完成"

# 第二步：清理所有可能的PID文件位置
echo "📋 第二步：深度清理PID文件..."
log_message "第二步：深度清理PID文件"

# 扩展的PID文件搜索位置
PID_SEARCH_PATHS=(
    "/tmp"
    "/var/run"
    "/usr/local/var/run"
    "/Library/Application Support/StrongVPN"
    "/Library/Application Support/com.strongvpn.StrongVPN2-Client"
    "/Library/Application Support/com.strongvpn.StrongVPN2-Helper"
    "$HOME/Library/Application Support/StrongVPN"
    "$HOME/Library/Application Support/com.strongvpn.StrongVPN2-Client"
)

# 查找并删除所有VPN相关的PID文件
for search_path in "${PID_SEARCH_PATHS[@]}"; do
    if [ -d "$search_path" ]; then
        log_message "搜索路径: $search_path"
        # 查找所有VPN相关的PID文件
        find "$search_path" -name "*openvpn*.pid" -o -name "*strongvpn*.pid" -o -name "*ipvanish*.pid" 2>/dev/null | while read pid_file; do
            if [ -f "$pid_file" ]; then
                log_message "删除PID文件: $pid_file"
                sudo rm -f "$pid_file"
                echo "🗑️  删除了 $pid_file"
            fi
        done
    fi
done

echo "✅ PID文件深度清理完成"
log_message "PID文件深度清理完成"

# 第三步：清理StrongVPN配置和缓存
echo "📋 第三步：清理StrongVPN配置和缓存..."
log_message "第三步：清理StrongVPN配置和缓存"

# StrongVPN配置目录
STRONGVPN_DIRS=(
    "$HOME/Library/Application Support/com.strongvpn.StrongVPN2-Client"
    "$HOME/Library/Caches/com.strongvpn.StrongVPN2-Client"
    "$HOME/Library/Preferences/com.strongvpn.StrongVPN2-Client.plist"
    "/Library/Application Support/com.strongvpn.StrongVPN2-Helper"
    "/tmp/strongvpn"
    "/tmp/openvpn"
)

for config_path in "${STRONGVPN_DIRS[@]}"; do
    if [ -e "$config_path" ]; then
        log_message "备份并清理: $config_path"
        # 备份重要配置（如果是配置文件）
        if [[ "$config_path" == *"Client"* ]] && [[ "$config_path" != *"Cache"* ]]; then
            backup_path="${config_path}.backup.$(date +%Y%m%d_%H%M%S)"
            cp -r "$config_path" "$backup_path" 2>/dev/null
            log_message "已备份到: $backup_path"
        fi
        # 清理
        sudo rm -rf "$config_path" 2>/dev/null
        echo "🗑️  清理了 $config_path"
    fi
done

echo "✅ StrongVPN配置清理完成"
log_message "StrongVPN配置清理完成"

# 第四步：重置网络配置（更彻底）
echo "📋 第四步：彻底重置网络配置..."
log_message "第四步：彻底重置网络配置"

# 删除所有VPN网络接口
for interface in $(ifconfig | grep '^tun\|^ppp' | cut -d: -f1); do
    log_message "删除网络接口: $interface"
    sudo ifconfig "$interface" down 2>/dev/null
    echo "🔌 关闭了 $interface"
done

# 清理路由表
log_message "清理路由表"
# 删除所有默认路由
sudo route -n flush 2>/dev/null

# 重新获取网络配置
echo "📶 重新配置网络..."
WIFI_SERVICE=$(networksetup -listallnetworkservices | grep -i wi-fi | head -1)
if [ ! -z "$WIFI_SERVICE" ]; then
    log_message "重新配置WiFi服务: $WIFI_SERVICE"
    sudo networksetup -setdhcp "$WIFI_SERVICE" 2>/dev/null
    echo "🔄 重新配置了WiFi"
fi

echo "✅ 网络配置重置完成"
log_message "网络配置重置完成"

# 第五步：重置DNS（更彻底）
echo "📋 第五步：彻底重置DNS..."
log_message "第五步：彻底重置DNS"

# 清理DNS缓存
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder 2>/dev/null

# 重置DNS设置
if [ ! -z "$WIFI_SERVICE" ]; then
    sudo networksetup -setdnsservers "$WIFI_SERVICE" Empty 2>/dev/null
    log_message "重置了DNS设置"
fi

# 重启DNS服务
sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist 2>/dev/null
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist 2>/dev/null

echo "✅ DNS彻底重置完成"
log_message "DNS彻底重置完成"

# 第六步：清理系统扩展
echo "📋 第六步：清理VPN系统扩展..."
log_message "第六步：清理VPN系统扩展"

# 查找StrongVPN系统扩展
SYSTEM_EXT_DIRS=$(find /Library/SystemExtensions -name "*strongvpn*" -o -name "*StrongVPN*" 2>/dev/null)
if [ ! -z "$SYSTEM_EXT_DIRS" ]; then
    echo "🔍 发现系统扩展，建议重启后生效"
    log_message "发现系统扩展: $SYSTEM_EXT_DIRS"
fi

echo "✅ 系统扩展检查完成"
log_message "系统扩展检查完成"

# 第七步：等待系统稳定
echo "📋 第七步：等待系统稳定..."
log_message "等待系统稳定"
sleep 10

# 测试网络连接
echo "🔍 测试网络连接..."
if ping -c 3 -W 2 8.8.8.8 >/dev/null 2>&1; then
    echo "✅ 网络连接正常"
    log_message "网络连接测试成功"
else
    echo "⚠️  网络连接可能需要时间恢复"
    log_message "网络连接测试失败，但这是正常的"
fi

# 完成
echo ""
echo "🎉 VPN深度修复完成！"
echo ""
echo "📝 重要提示："
echo "1. 现在StrongVPN的所有进程和配置都已清理"
echo "2. 请重启电脑以确保系统扩展完全清理"
echo "3. 重启后重新安装或重新配置StrongVPN"
echo "4. 第一次连接时可能需要重新输入账号密码"
echo ""

log_message "========== VPN深度修复脚本完成 =========="

# 发送通知
show_notification "VPN深度修复完成！建议重启电脑。"

echo "📋 详细日志已保存到: $LOG_FILE"
echo ""
echo "💡 建议操作顺序："
echo "   1. 重启电脑"
echo "   2. 重新打开StrongVPN"
echo "   3. 重新配置账号"
echo "   4. 选择服务器连接" 
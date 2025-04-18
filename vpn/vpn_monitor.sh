#!/bin/bash

# VPN监控脚本
VPN_IPS=("207.204.224.*" "192.200.144.*" "216.169.131.*")  # 允许的VPN IP地址列表
CHECK_INTERVAL=20                    # 检查间隔（秒）
LOG_FILE="/Users/boxie/cursor/vpn_monitor.log"  # 日志文件

# 日志函数
log_message() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# 检查IP是否是允许的VPN IP
is_allowed_ip() {
    local ip=$1
    for vpn_ip in "${VPN_IPS[@]}"; do
        if [[ $ip == $vpn_ip ]]; then
            return 0  # IP在允许列表中
        fi
    done
    return 1  # IP不在允许列表中
}

# 获取当前公网IP
get_public_ip() {
    local ip=""
    # 尝试多个IP检测服务
    ip=$(curl -s --connect-timeout 5 --max-time 10 https://api.ipify.org 2>/dev/null)
    if [ -z "$ip" ]; then
        ip=$(curl -s --connect-timeout 5 --max-time 10 http://ifconfig.me/ip 2>/dev/null)
    fi
    
    if [ -z "$ip" ]; then
        log_message "无法获取当前IP地址"
        return 1
    fi
    
    echo "$ip"
    return 0
}

# 检查VPN连接状态
check_vpn_status() {
    # 检查VPN接口是否存在
    if ! ifconfig | grep -q "tun0" && ! ifconfig | grep -q "ppp0"; then
        log_message "VPN接口不存在"
        return 1
    fi
    
    # 获取当前IP
    CURRENT_IP=$(get_public_ip)
    if [ $? -ne 0 ]; then
        log_message "获取IP地址失败"
        return 1
    fi
    
    # 检查IP是否在允许列表中
    if ! is_allowed_ip "$CURRENT_IP"; then
        log_message "当前IP($CURRENT_IP)不在允许列表中"
        return 1
    fi
    
    log_message "VPN连接正常，当前IP: $CURRENT_IP"
    return 0
}

# 主程序
log_message "VPN监控脚本启动..."

while true; do
    if ! check_vpn_status; then
        log_message "VPN连接异常，发送通知"
        osascript -e 'display notification "VPN连接异常，请手动重新连接" with title "VPN状态提醒"'
    fi
    
    sleep $CHECK_INTERVAL
done 
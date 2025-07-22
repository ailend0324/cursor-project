#!/bin/bash

# 支持多个VPN IP地址，这样可以在IP地址变化时仍然认为VPN连接是成功的
VPN_IPS=("207.204.224.8" "192.200.144.49")  # 已知的VPN IP地址列表
CHECK_INTERVAL=60       # 检查间隔（秒）
STOP_FLAG="/Users/boxie/cursor/vpn_stop.flag"  # 停止标志文件
LOG_FILE="/Users/boxie/cursor/vpn_reconnect.log"  # 日志文件

# 日志函数
log_message() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# 检查IP是否是VPN IP
is_vpn_ip() {
    local ip=$1
    for vpn_ip in "${VPN_IPS[@]}"; do
        if [ "$ip" == "$vpn_ip" ]; then
            return 0  # 是VPN IP
        fi
    done
    return 1  # 不是VPN IP
}

# 检查网络连接
check_network() {
    log_message "检查网络连接..."
    
    # 先检查DNS解析
    if nslookup google.com >/dev/null 2>&1 || nslookup baidu.com >/dev/null 2>&1; then
        log_message "DNS解析正常"
    else
        log_message "DNS解析失败"
        # 重置DNS缓存
        sudo dscacheutil -flushcache
        sudo killall -HUP mDNSResponder
    fi
    
    # 检查网络连通性
    if ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1 || ping -c 1 -W 3 114.114.114.114 >/dev/null 2>&1; then
        log_message "网络连接正常"
        return 0
    else
        log_message "网络连接异常"
        return 1
    fi
}

# 修复网络
fix_network() {
    log_message "尝试修复网络连接..."
    
    # 重置DNS
    sudo dscacheutil -flushcache
    sudo killall -HUP mDNSResponder
    
    # 重启网络接口
    networksetup -setairportpower en0 off
    sleep 2
    networksetup -setairportpower en0 on
    sleep 5
    
    # 尝试使用手动DNS
    networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4
    
    # 检查网络修复是否成功
    if check_network; then
        log_message "网络修复成功"
        return 0
    else
        log_message "网络修复失败"
        return 1
    fi
}

# 检查VPN接口是否存在
check_vpn_interface() {
    ifconfig | grep -q "tun0" || ifconfig | grep -q "ppp0"
    return $?
}

# 清理VPN路由
cleanup_vpn_routes() {
    log_message "清理VPN路由..."
    
    # 清理IPv4路由
    DEFAULT_GATEWAY=$(netstat -rn | grep default | grep -v '::' | awk '{print $2}')
    if [ ! -z "$DEFAULT_GATEWAY" ]; then
        log_message "删除IPv4默认路由: $DEFAULT_GATEWAY"
        sudo route -n delete default "$DEFAULT_GATEWAY" 2>/dev/null
    fi
    
    # 清理所有tun接口
    for interface in $(ifconfig | grep '^tun' | cut -d: -f1); do
        log_message "删除接口 $interface"
        sudo ifconfig $interface down 2>/dev/null
    done
    
    # 刷新DNS缓存
    sudo dscacheutil -flushcache
    sudo killall -HUP mDNSResponder
    
    # 恢复DNS设置
    networksetup -setdnsservers Wi-Fi Empty
}

# 获取当前公网IP (使用多个服务，确保可靠性)
get_public_ip() {
    local ip=""
    # 尝试第一个服务，带DNS解析超时
    ip=$(curl -s --connect-timeout 5 --max-time 10 --retry 2 https://api.ipify.org 2>/dev/null)
    if [ -z "$ip" ] || [[ "$ip" == *"error"* ]]; then
        log_message "ipify.org 获取IP失败，尝试备用服务"
        # 尝试第二个服务
        ip=$(curl -s --connect-timeout 5 --max-time 10 --retry 2 http://ifconfig.me/ip 2>/dev/null)
    fi
    if [ -z "$ip" ] || [[ "$ip" == *"error"* ]]; then
        log_message "ifconfig.me 获取IP失败，尝试备用服务"
        # 尝试第三个服务
        ip=$(curl -s --connect-timeout 5 --max-time 10 --retry 2 http://icanhazip.com 2>/dev/null)
    fi
    if [ -z "$ip" ] || [[ "$ip" == *"error"* ]]; then
        log_message "icanhazip.com 获取IP失败，尝试备用服务"
        # 尝试第四个服务
        ip=$(curl -s --connect-timeout 5 --max-time 10 --retry 2 http://checkip.amazonaws.com 2>/dev/null)
    fi
    if [ -z "$ip" ] || [[ "$ip" == *"error"* ]]; then
        log_message "所有IP检测服务都失败了，尝试使用本地命令"
        # 尝试使用ifconfig获取IP
        ip=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
    fi
    
    # 清理IP，确保只包含有效字符
    ip=$(echo "$ip" | tr -dc '0-9.\n')
    
    if [ -z "$ip" ]; then
        log_message "所有方法都无法获取IP"
        return 1
    fi
    
    echo "$ip"
    return 0
}

# 主程序开始
log_message "VPN监控脚本启动..."

while true; do
    # 首先检查网络连接
    if ! check_network; then
        log_message "网络连接异常，尝试修复..."
        osascript -e 'display notification "网络连接异常，尝试修复..." with title "网络状态提醒"'
        
        # 修复网络
        if fix_network; then
            osascript -e 'display notification "网络修复成功" with title "网络状态提醒"'
        else
            osascript -e 'display notification "网络修复失败，请手动检查！" with title "网络状态提醒"'
            sleep 30
            continue
        fi
    fi
    
    # 获取当前公网IP
    CURRENT_IP=$(get_public_ip)
    if [ $? -ne 0 ] || [ -z "$CURRENT_IP" ]; then
        log_message "获取IP地址失败，尝试修复网络..."
        fix_network
        sleep 10
        CURRENT_IP=$(get_public_ip)
        if [ $? -ne 0 ] || [ -z "$CURRENT_IP" ]; then
            log_message "再次获取IP地址失败，将在下一循环重试"
            sleep $CHECK_INTERVAL
            continue
        fi
    fi
    log_message "当前公网IP: $CURRENT_IP"
    
    # 检查VPN接口状态
    if check_vpn_interface; then
        log_message "VPN接口仍然存在"
        if ! is_vpn_ip "$CURRENT_IP"; then
            log_message "VPN接口存在但IP不匹配，需要清理"
            cleanup_vpn_routes
        else
            log_message "VPN接口存在且IP匹配，连接正常"
        fi
    fi
    
    # 检查当前IP是否是VPN IP
    if is_vpn_ip "$CURRENT_IP"; then
        log_message "当前IP($CURRENT_IP)是VPN IP，连接正常"
    else
        osascript -e 'display notification "VPN已掉线，请手动重新连接" with title "VPN状态提醒"'
        log_message "VPN已掉线，需要手动重新连接"
        
        # 清理VPN路由，但不自动重连
        cleanup_vpn_routes
    fi
    
    # 检查停止标志前休眠
    sleep $CHECK_INTERVAL

    # 检查停止标志
    if [ -f "$STOP_FLAG" ]; then
        log_message "检测到停止标志，脚本退出..."
        rm "$STOP_FLAG"
        exit 0
    fi
done
#!/bin/bash

# StrongVPN 完全清理检查脚本
# 确保所有StrongVPN相关文件都被彻底删除

LOG_FILE="/Users/boxie/cursor/vpn/cleanup_check.log"

# 日志函数
log_message() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# 显示通知
show_notification() {
    osascript -e "display notification \"$1\" with title \"StrongVPN清理检查\""
}

echo "🧹 StrongVPN 完全清理检查工具"
echo "确保所有相关文件都被彻底删除"
echo "=================================================="
log_message "========== StrongVPN完全清理检查开始 =========="

# 检查和清理函数
check_and_clean() {
    local path="$1"
    local description="$2"
    
    if [ -e "$path" ]; then
        echo "🔍 发现残留: $description"
        echo "   路径: $path"
        log_message "发现残留文件: $path ($description)"
        
        # 询问是否删除
        echo "   是否删除? (y/n) [默认: y]"
        read -t 5 -r response
        response=${response:-y}
        
        if [[ "$response" =~ ^[Yy]$ ]]; then
            if sudo rm -rf "$path" 2>/dev/null; then
                echo "   ✅ 已删除"
                log_message "已删除: $path"
            else
                echo "   ❌ 删除失败"
                log_message "删除失败: $path"
            fi
        else
            echo "   ⏭️  跳过删除"
            log_message "用户跳过删除: $path"
        fi
        echo ""
    fi
}

# 第一部分：应用程序相关文件
echo "📋 第一部分：检查应用程序文件..."
log_message "第一部分：检查应用程序文件"

APP_LOCATIONS=(
    "/Applications/StrongVPN.app"
    "/Applications/strongvpn.app"
    "~/Applications/StrongVPN.app"
    "~/Applications/strongvpn.app"
)

for app_path in "${APP_LOCATIONS[@]}"; do
    # 展开波浪号
    expanded_path=$(eval echo "$app_path")
    check_and_clean "$expanded_path" "StrongVPN应用程序"
done

# 第二部分：用户配置和缓存文件
echo "📋 第二部分：检查用户配置文件..."
log_message "第二部分：检查用户配置文件"

USER_FILES=(
    "$HOME/Library/Application Support/StrongVPN"
    "$HOME/Library/Application Support/com.strongvpn.StrongVPN2-Client"
    "$HOME/Library/Application Support/com.strongvpn.StrongVPN2-Helper"
    "$HOME/Library/Caches/StrongVPN"
    "$HOME/Library/Caches/com.strongvpn.StrongVPN2-Client"
    "$HOME/Library/Preferences/StrongVPN.plist"
    "$HOME/Library/Preferences/com.strongvpn.StrongVPN2-Client.plist"
    "$HOME/Library/Preferences/com.strongvpn.StrongVPN2-Helper.plist"
    "$HOME/Library/Logs/StrongVPN"
    "$HOME/Library/Logs/com.strongvpn.StrongVPN2-Client"
    "$HOME/Library/Containers/com.strongvpn.StrongVPN2-Client"
    "$HOME/Library/Group Containers/group.com.strongvpn.StrongVPN2-Client"
    "$HOME/Library/Saved Application State/com.strongvpn.StrongVPN2-Client.savedState"
)

for user_file in "${USER_FILES[@]}"; do
    check_and_clean "$user_file" "用户配置/缓存文件"
done

# 第三部分：系统级文件
echo "📋 第三部分：检查系统级文件..."
log_message "第三部分：检查系统级文件"

SYSTEM_FILES=(
    "/Library/Application Support/StrongVPN"
    "/Library/Application Support/com.strongvpn.StrongVPN2-Client"
    "/Library/Application Support/com.strongvpn.StrongVPN2-Helper"
    "/Library/Caches/com.strongvpn.StrongVPN2-Client"
    "/Library/Preferences/com.strongvpn.StrongVPN2-Client.plist"
    "/Library/Preferences/com.strongvpn.StrongVPN2-Helper.plist"
    "/Library/LaunchAgents/com.strongvpn.StrongVPN2-Client.plist"
    "/Library/LaunchDaemons/com.strongvpn.StrongVPN2-Helper.plist"
    "/Library/PrivilegedHelperTools/com.strongvpn.StrongVPN2-Helper"
    "/Library/Logs/StrongVPN"
    "/var/log/strongvpn"
)

for system_file in "${SYSTEM_FILES[@]}"; do
    check_and_clean "$system_file" "系统级配置文件"
done

# 第四部分：系统扩展
echo "📋 第四部分：检查系统扩展..."
log_message "第四部分：检查系统扩展"

# 查找StrongVPN系统扩展
SYSTEM_EXTENSIONS=$(find /Library/SystemExtensions -name "*strongvpn*" -o -name "*StrongVPN*" 2>/dev/null)
if [ ! -z "$SYSTEM_EXTENSIONS" ]; then
    echo "🔍 发现系统扩展:"
    echo "$SYSTEM_EXTENSIONS"
    log_message "发现系统扩展: $SYSTEM_EXTENSIONS"
    
    echo "⚠️  注意: 系统扩展需要重启电脑才能完全清理"
    echo "   这些扩展在重启后会被系统自动清理"
    log_message "系统扩展需要重启后清理"
    echo ""
else
    echo "✅ 未发现系统扩展"
    log_message "未发现系统扩展"
fi

# 第五部分：临时文件和PID文件
echo "📋 第五部分：检查临时文件和PID文件..."
log_message "第五部分：检查临时文件和PID文件"

TEMP_LOCATIONS=(
    "/tmp"
    "/var/tmp"
    "/usr/local/var/run"
    "/var/run"
)

for temp_dir in "${TEMP_LOCATIONS[@]}"; do
    if [ -d "$temp_dir" ]; then
        echo "🔍 搜索 $temp_dir 中的StrongVPN文件..."
        
        # 查找StrongVPN相关的临时文件
        TEMP_FILES=$(find "$temp_dir" -name "*strongvpn*" -o -name "*StrongVPN*" -o -name "*ipvanish*openvpn*" 2>/dev/null)
        
        if [ ! -z "$TEMP_FILES" ]; then
            echo "$TEMP_FILES" | while read temp_file; do
                check_and_clean "$temp_file" "临时文件"
            done
        fi
    fi
done

# 第六部分：进程检查
echo "📋 第六部分：检查残留进程..."
log_message "第六部分：检查残留进程"

RUNNING_PROCESSES=$(ps aux | grep -i strong | grep -v grep)
if [ ! -z "$RUNNING_PROCESSES" ]; then
    echo "⚠️  发现可能的残留进程:"
    echo "$RUNNING_PROCESSES"
    log_message "发现残留进程: $RUNNING_PROCESSES"
    
    echo "是否强制终止这些进程? (y/n) [默认: y]"
    read -t 5 -r response
    response=${response:-y}
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        sudo pkill -f -i strong 2>/dev/null
        echo "✅ 已终止残留进程"
        log_message "已终止残留进程"
    fi
else
    echo "✅ 未发现残留进程"
    log_message "未发现残留进程"
fi

# 第七部分：网络配置检查
echo "📋 第七部分：检查网络配置残留..."
log_message "第七部分：检查网络配置残留"

# 检查VPN网络接口
VPN_INTERFACES=$(ifconfig | grep -E '^(tun|ppp)' | cut -d: -f1)
if [ ! -z "$VPN_INTERFACES" ]; then
    echo "🔍 发现VPN网络接口: $VPN_INTERFACES"
    log_message "发现VPN网络接口: $VPN_INTERFACES"
    
    echo "是否关闭这些VPN接口? (y/n) [默认: y]"
    read -t 5 -r response
    response=${response:-y}
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        for interface in $VPN_INTERFACES; do
            sudo ifconfig "$interface" down 2>/dev/null
            echo "🔌 已关闭接口: $interface"
            log_message "已关闭接口: $interface"
        done
    fi
else
    echo "✅ 未发现VPN网络接口"
    log_message "未发现VPN网络接口"
fi

# 第八部分：使用find命令全局搜索
echo "📋 第八部分：全局搜索残留文件..."
log_message "第八部分：全局搜索残留文件"

echo "🔍 正在全局搜索包含'strongvpn'的文件..."
echo "   (这可能需要一些时间，请耐心等待)"

# 搜索用户目录
USER_SEARCH_RESULT=$(find "$HOME" -iname "*strongvpn*" 2>/dev/null | head -20)
if [ ! -z "$USER_SEARCH_RESULT" ]; then
    echo "🔍 在用户目录发现:"
    echo "$USER_SEARCH_RESULT"
    log_message "用户目录搜索结果: $USER_SEARCH_RESULT"
    
    echo "是否查看并处理这些文件? (y/n) [默认: n]"
    read -t 10 -r response
    response=${response:-n}
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "$USER_SEARCH_RESULT" | while read found_file; do
            check_and_clean "$found_file" "全局搜索发现的文件"
        done
    fi
fi

# 完成总结
echo ""
echo "🎉 StrongVPN清理检查完成！"
echo ""

# 生成清理报告
echo "📊 清理报告："
TOTAL_ENTRIES=$(wc -l < "$LOG_FILE")
DELETED_COUNT=$(grep "已删除:" "$LOG_FILE" | wc -l)
FOUND_COUNT=$(grep "发现残留文件:" "$LOG_FILE" | wc -l)

echo "   总检查项目: $TOTAL_ENTRIES"
echo "   发现残留文件: $FOUND_COUNT"  
echo "   已删除文件: $DELETED_COUNT"
echo ""

if [ $FOUND_COUNT -eq 0 ]; then
    echo "✅ 恭喜！系统中没有发现StrongVPN残留文件"
    log_message "清理检查完成：无残留文件"
    show_notification "StrongVPN已完全清理干净！"
else
    remaining=$((FOUND_COUNT - DELETED_COUNT))
    if [ $remaining -eq 0 ]; then
        echo "✅ 所有发现的残留文件都已清理"
        log_message "清理检查完成：所有残留文件已清理"
        show_notification "StrongVPN残留文件已全部清理！"
    else
        echo "⚠️  还有 $remaining 个文件未清理"
        log_message "清理检查完成：还有 $remaining 个文件未清理"
        show_notification "StrongVPN大部分文件已清理，请检查报告。"
    fi
fi

echo ""
echo "💡 建议："
echo "   1. 重启电脑以确保系统扩展完全清理"
echo "   2. 重启后再次运行此脚本确认清理完成"
echo "   3. 如果要重新安装VPN，建议使用不同的VPN软件"
echo ""

log_message "========== StrongVPN完全清理检查完成 =========="
echo "📋 详细日志已保存到: $LOG_FILE" 
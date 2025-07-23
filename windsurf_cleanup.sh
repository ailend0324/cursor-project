#!/bin/bash

# Windsurf 完整清理脚本
# 作者：AI助手
# 功能：安全删除Windsurf应用程序及所有相关文件
# 日期：$(date '+%Y-%m-%d %H:%M:%S')

# 颜色定义（让输出更友好）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志文件
LOG_FILE="windsurf_cleanup_$(date '+%Y%m%d_%H%M%S').log"

# 记录日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 打印带颜色的消息
print_status() {
    echo -e "${BLUE}[信息]${NC} $1"
    log "INFO: $1"
}

print_success() {
    echo -e "${GREEN}[成功]${NC} $1"
    log "SUCCESS: $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
    log "WARNING: $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
    log "ERROR: $1"
}

# 检查文件/文件夹是否存在并删除
remove_if_exists() {
    local path="$1"
    local description="$2"
    
    if [ -e "$path" ]; then
        print_status "正在删除: $description ($path)"
        if rm -rf "$path" 2>/dev/null; then
            print_success "已删除: $description"
            return 0
        else
            print_error "删除失败: $description"
            return 1
        fi
    else
        print_warning "未找到: $description ($path)"
        return 0
    fi
}

# 获取文件/文件夹大小
get_size() {
    local path="$1"
    if [ -e "$path" ]; then
        du -sh "$path" 2>/dev/null | cut -f1 || echo "未知大小"
    else
        echo "不存在"
    fi
}

# 主清理函数
cleanup_windsurf() {
    print_status "开始Windsurf完整清理..."
    print_status "日志将保存到: $LOG_FILE"
    
    local total_freed=0
    local failed_count=0
    
    # 要删除的文件列表（路径，描述）
    declare -a cleanup_items=(
        "/Applications/Windsurf.app|主应用程序"
        "$HOME/.windsurf|用户配置文件夹"
        "$HOME/Library/Preferences/com.exafunction.windsurf.plist|用户偏好设置"
        "$HOME/Library/Caches/com.exafunction.windsurf|应用缓存"
        "$HOME/Library/Caches/com.exafunction.windsurf.ShipIt|更新缓存"
        "$HOME/Library/HTTPStorages/com.exafunction.windsurf|HTTP存储"
    )
    
    # 查找并添加ByHost配置文件
    for byhost_file in "$HOME"/Library/Preferences/ByHost/com.exafunction.windsurf.*.plist; do
        if [ -f "$byhost_file" ]; then
            cleanup_items+=("$byhost_file|ByHost配置文件")
        fi
    done
    
    # 显示将要删除的文件及其大小
    print_status "检测到以下Windsurf相关文件："
    echo
    printf "%-60s %-15s\n" "文件/文件夹" "大小"
    printf "%-60s %-15s\n" "$(printf '%*s' 60 '' | tr ' ' '-')" "$(printf '%*s' 15 '' | tr ' ' '-')"
    
    for item in "${cleanup_items[@]}"; do
        IFS='|' read -r path description <<< "$item"
        size=$(get_size "$path")
        printf "%-60s %-15s\n" "$description" "$size"
    done
    
    echo
    print_warning "这将永久删除所有Windsurf相关文件！"
    print_warning "删除后无法恢复，请确保你不再需要Windsurf的配置和扩展。"
    echo
    
    # 确认删除
    read -p "你确定要继续吗？(输入 'YES' 确认): " confirmation
    
    if [ "$confirmation" != "YES" ]; then
        print_status "操作已取消。"
        log "用户取消了清理操作"
        exit 0
    fi
    
    echo
    print_status "开始删除文件..."
    
    # 执行删除
    for item in "${cleanup_items[@]}"; do
        IFS='|' read -r path description <<< "$item"
        if remove_if_exists "$path" "$description"; then
            # 这里应该累加实际释放的空间，但为了简化，我们只计数成功的操作
            ((total_freed++))
        else
            ((failed_count++))
        fi
    done
    
    # 清理Chrome浏览器中的相关数据（可选）
    print_status "检查Chrome浏览器中的windsurf数据..."
    
    chrome_paths=(
        "$HOME/Library/Application Support/Google/Chrome/Default/IndexedDB/https_windsurf.com_0.indexeddb.leveldb"
        "$HOME/Library/Application Support/Google/Chrome/Profile 2/IndexedDB/https_windsurf.com_0.indexeddb.leveldb"
    )
    
    for chrome_path in "${chrome_paths[@]}"; do
        if [ -e "$chrome_path" ]; then
            remove_if_exists "$chrome_path" "Chrome浏览器windsurf数据"
        fi
    done
    
    # 检查是否还有残留进程
    print_status "检查残留进程..."
    windsurf_processes=$(ps aux | grep -i windsurf | grep -v grep | wc -l)
    if [ "$windsurf_processes" -gt 0 ]; then
        print_warning "发现${windsurf_processes}个Windsurf相关进程仍在运行"
        print_status "正在尝试结束这些进程..."
        pkill -f -i windsurf 2>/dev/null
        sleep 2
        remaining=$(ps aux | grep -i windsurf | grep -v grep | wc -l)
        if [ "$remaining" -eq 0 ]; then
            print_success "所有Windsurf进程已结束"
        else
            print_warning "仍有${remaining}个进程未能结束，可能需要手动结束"
        fi
    else
        print_success "未发现运行中的Windsurf进程"
    fi
    
    # 最终报告
    echo
    print_status "清理完成！"
    print_success "成功删除 $total_freed 项"
    if [ "$failed_count" -gt 0 ]; then
        print_warning "删除失败 $failed_count 项"
    fi
    
    # 验证清理结果
    print_status "验证清理结果..."
    remaining_items=0
    
    for item in "${cleanup_items[@]}"; do
        IFS='|' read -r path description <<< "$item"
        if [ -e "$path" ]; then
            print_warning "仍然存在: $description ($path)"
            ((remaining_items++))
        fi
    done
    
    if [ "$remaining_items" -eq 0 ]; then
        print_success "✅ Windsurf已完全清理！"
        print_success "所有相关文件和配置已删除"
    else
        print_warning "⚠️  仍有 $remaining_items 项未被删除，请检查日志文件"
    fi
    
    print_status "详细日志已保存到: $LOG_FILE"
    print_status "建议重启系统以确保所有变更生效"
}

# 显示脚本信息
echo -e "${BLUE}"
echo "=================================================="
echo "          Windsurf 完整清理工具"
echo "=================================================="
echo -e "${NC}"
echo "这个脚本将帮助你完全删除Windsurf及其所有相关文件"
echo "包括："
echo "  • 主应用程序 (/Applications/Windsurf.app)"
echo "  • 用户配置文件 (~/.windsurf)"
echo "  • 系统偏好设置和缓存"
echo "  • 浏览器相关数据"
echo ""

# 检查是否为macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "此脚本仅适用于macOS系统"
    exit 1
fi

# 开始清理
cleanup_windsurf

echo
print_status "脚本执行完毕！" 
#!/bin/bash

# 🚀 自动化页面发布脚本
# 使用方法: ./publish.sh

set -e  # 遇到错误立即退出

echo "🚀 开始自动化页面发布流程..."

# 检查 content.md 是否存在
if [ ! -f "content.md" ]; then
    echo "❌ 错误：找不到 content.md 文件"
    echo "请先创建 content.md 文件并填入要发布的内容"
    exit 1
fi

# 解析 content.md 中的配置信息
echo "📖 读取配置信息..."

# 提取页面标题
PAGE_TITLE=$(grep -F "**页面标题**:" content.md | sed 's/.*: *//' | tr -d '\r')
if [ -z "$PAGE_TITLE" ]; then
    PAGE_TITLE="我的分享页面"
fi

# 提取页面副标题
PAGE_SUBTITLE=$(grep -F "**页面副标题**:" content.md | sed 's/.*: *//' | tr -d '\r')
if [ -z "$PAGE_SUBTITLE" ]; then
    PAGE_SUBTITLE="记录生活中的美好时光"
fi

# 提取模板类型
TEMPLATE_TYPE=$(grep -F "**模板类型**:" content.md | sed 's/.*: *//' | tr -d '\r' | xargs)
if [ -z "$TEMPLATE_TYPE" ]; then
    TEMPLATE_TYPE="travel"
fi

# 提取页面文件名
PAGE_FILENAME=$(grep -F "**页面文件名**:" content.md | sed 's/.*: *//' | tr -d '\r' | xargs)
if [ -z "$PAGE_FILENAME" ]; then
    PAGE_FILENAME="my_new_page"
fi

echo "✅ 配置信息读取完成："
echo "   📝 页面标题: $PAGE_TITLE"
echo "   📄 页面副标题: $PAGE_SUBTITLE" 
echo "   🎨 模板类型: $TEMPLATE_TYPE"
echo "   📁 文件名: $PAGE_FILENAME"

# 选择模板文件（更新为新的路径）
case $TEMPLATE_TYPE in
    "travel")
        TEMPLATE_DIR="templates/travel_blog"
        echo "🌍 使用旅行日记模板"
        ;;
    "investment")
        TEMPLATE_DIR="templates/investment_notes"
        echo "💰 使用投资笔记模板"
        ;;
    "reading")
        TEMPLATE_DIR="templates/reading_summary"
        echo "📚 使用读书分享模板"
        ;;
    "study")
        TEMPLATE_DIR="templates/demo_new_page"
        echo "📖 使用学习笔记模板"
        ;;
    "professional")
        TEMPLATE_DIR="examples/phoenix_report"
        echo "💼 使用专业分析模板"
        ;;
    *)
        echo "⚠️  未知模板类型，使用默认旅行模板"
        TEMPLATE_DIR="templates/travel_blog"
        ;;
esac

# 检查模板是否存在
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "❌ 错误：模板目录 $TEMPLATE_DIR 不存在"
    exit 1
fi

# 创建输出目录（在项目根目录）
OUTPUT_DIR="../$PAGE_FILENAME"
echo "📁 创建输出目录: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# 复制模板文件
echo "📋 复制模板文件..."
cp "$TEMPLATE_DIR/index.html" "$OUTPUT_DIR/index.html"

# 提取页面内容
echo "🔄 处理页面内容..."

# 提取核心亮点内容
HIGHLIGHT_CONTENT=$(sed -n '/### 🎯 核心亮点/,/### 📝 主要内容/p' content.md | sed '1d;$d' | sed 's/^[ \t]*//')

# 提取主要内容
MAIN_CONTENT=$(sed -n '/### 📝 主要内容/,/### 💡 个人感悟/p' content.md | sed '1d;$d')

# 提取感悟内容
INSIGHT_CONTENT=$(sed -n '/### 💡 个人感悟/,/### 📊 下一步计划/p' content.md | sed '1d;$d')

# 提取计划内容
PLAN_CONTENT=$(sed -n '/### 📊 下一步计划/,/---/p' content.md | sed '1d;$d')

# 替换HTML模板中的内容
echo "🔧 替换模板内容..."

# 基于不同模板类型进行内容替换
case $TEMPLATE_TYPE in
    "travel")
        # 替换旅行模板的内容
        sed -i.bak "s/🌍 我的旅行日记/$PAGE_TITLE/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/记录旅途中的美好时光和难忘经历/$PAGE_SUBTITLE/g" "$OUTPUT_DIR/index.html"
        
        # 替换核心亮点
        if [ ! -z "$HIGHLIGHT_CONTENT" ]; then
            # 转换换行符为HTML
            HIGHLIGHT_HTML=$(echo "$HIGHLIGHT_CONTENT" | sed 's/$/\\n/g' | tr -d '\n' | sed 's/\\n/<br>/g')
            sed -i.bak "s/这次去了美丽的三亚，感受到了海南的热带风情。白色的沙滩、碧蓝的海水，还有当地的椰子鸡火锅，每一个瞬间都让人难忘！/$HIGHLIGHT_HTML/g" "$OUTPUT_DIR/index.html"
        fi
        ;;
        
    "investment")
        # 替换投资模板的内容
        sed -i.bak "s/💰 我的投资学习笔记/$PAGE_TITLE/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/记录投资路上的学习心得和实战经验/$PAGE_SUBTITLE/g" "$OUTPUT_DIR/index.html"
        ;;
        
    "reading")
        # 替换读书模板的内容
        sed -i.bak "s/📚 读书分享/$PAGE_TITLE/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/分享读书心得，记录思考感悟/$PAGE_SUBTITLE/g" "$OUTPUT_DIR/index.html"
        ;;
        
    "study")
        # 替换学习模板的内容
        sed -i.bak "s/📖 我的学习笔记分享/$PAGE_TITLE/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/记录学习过程中的重要知识点和心得体会/$PAGE_SUBTITLE/g" "$OUTPUT_DIR/index.html"
        ;;
esac

# 清理备份文件
rm -f "$OUTPUT_DIR/index.html.bak"

# 生成当前日期
CURRENT_DATE=$(date "+%Y年%m月%d日")
sed -i.bak "s/2025年7月22日/$CURRENT_DATE/g" "$OUTPUT_DIR/index.html"
rm -f "$OUTPUT_DIR/index.html.bak"

echo "✅ 页面生成完成: $OUTPUT_DIR/index.html"

# Git 操作
echo "📤 开始发布到GitHub..."

# 切换到项目根目录
cd ..

# 添加文件
git add "$PAGE_FILENAME/"

# 提交
COMMIT_MSG="发布新页面: $PAGE_TITLE"
git commit -m "$COMMIT_MSG"

# 推送到远程
git push origin main

echo ""
echo "🎉 发布成功！"
echo ""
echo "📱 你的页面将在2-3分钟后上线："
echo "🔗 https://ailend0324.github.io/cursor-project/$PAGE_FILENAME/"
echo ""
echo "💡 小贴士："
echo "   - 如需修改内容，直接编辑 content.md 然后重新运行 ./publish.sh"
echo "   - 如需发布新页面，修改 content.md 中的页面文件名"
echo "   - 所有页面都可以在 https://ailend0324.github.io/cursor-project/ 下找到"
echo "" 
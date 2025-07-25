#!/bin/bash

# 自动化页面发布脚本
echo "🚀 开始自动化页面发布流程..."

# 设置变量
TEMPLATE_DIR="templates"
EXAMPLES_DIR="examples"
OUTPUT_DIR=""

# 检查 content.md 文件是否存在
if [ ! -f "content.md" ]; then
    echo "❌ 错误：找不到 content.md 文件"
    echo "请先创建 content.md 文件并填入内容"
    exit 1
fi

# 读取配置信息
echo "📖 读取配置信息..."

# 提取页面标题
PAGE_TITLE=$(grep -F "**页面标题**:" content.md | sed 's/\*\*页面标题\*\*: *//')

# 提取页面副标题
PAGE_SUBTITLE=$(grep -F "**页面副标题**:" content.md | sed 's/\*\*页面副标题\*\*: *//')

# 提取模板类型
TEMPLATE_TYPE=$(grep -F "**模板类型**:" content.md | sed 's/\*\*模板类型\*\*: *//')

# 提取页面文件名
PAGE_FILENAME=$(grep -F "**页面文件名**:" content.md | sed 's/\*\*页面文件名\*\*: *//')

# 验证必要的配置
if [ -z "$PAGE_TITLE" ] || [ -z "$PAGE_SUBTITLE" ] || [ -z "$TEMPLATE_TYPE" ] || [ -z "$PAGE_FILENAME" ]; then
    echo "❌ 错误：content.md 中缺少必要的配置信息"
    echo "请确保包含以下配置："
    echo "**页面标题**: 您的页面标题"
    echo "**页面副标题**: 您的页面副标题"
    echo "**模板类型**: travel/investment/reading/study/work"
    echo "**页面文件名**: 您的文件名"
    exit 1
fi

echo "✅ 配置信息读取完成："
echo "   📝 页面标题: $PAGE_TITLE"
echo "   📄 页面副标题: $PAGE_SUBTITLE"
echo "   🎨 模板类型: $TEMPLATE_TYPE"
echo "   📁 文件名: $PAGE_FILENAME"

# 提取内容区域
echo "📖 提取页面内容..."

# 提取核心亮点内容
HIGHLIGHT_CONTENT=$(sed -n '/### 🎯 核心亮点/,/### 📝 主要内容/p' content.md | sed '1d;$d' | sed 's/^[ \t]*//')

# 提取完整的主要内容
FULL_MAIN_CONTENT=$(sed -n '/### 📝 主要内容/,/### 💡 个人感悟/p' content.md | sed '$d')

# 提取感悟内容
INSIGHT_CONTENT=$(sed -n '/### 💡 个人感悟/,/### 📊 下一步计划/p' content.md | sed '1d;$d')

# 提取计划内容
PLAN_CONTENT=$(sed -n '/### 📊 下一步计划/,/---/p' content.md | sed '1d;$d')

# 根据模板类型选择源目录
case $TEMPLATE_TYPE in
    "travel")
        echo "🌍 使用旅行日记模板"
        TEMPLATE_SOURCE="$EXAMPLES_DIR/travel_blog"
        ;;
    "investment")
        echo "💰 使用投资笔记模板"
        TEMPLATE_SOURCE="$EXAMPLES_DIR/investment_notes"
        ;;
    "reading")
        echo "📚 使用读书分享模板"
        TEMPLATE_SOURCE="$EXAMPLES_DIR/reading_summary"
        ;;
    "study")
        echo "📖 使用学习笔记模板"
        TEMPLATE_SOURCE="$TEMPLATE_DIR/demo_new_page"
        ;;
    "work")
        echo "💼 使用工作总结模板"
        TEMPLATE_SOURCE="$EXAMPLES_DIR/work_summary"
        ;;
    *)
        echo "❌ 错误：不支持的模板类型 '$TEMPLATE_TYPE'"
        echo "支持的模板类型：travel, investment, reading, study, work"
        exit 1
        ;;
esac

# 创建输出目录
OUTPUT_DIR="../$PAGE_FILENAME"
echo "📁 创建输出目录: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# 复制模板文件
echo "📋 复制模板文件..."
if [ ! -d "$TEMPLATE_SOURCE" ]; then
    echo "❌ 错误：找不到模板目录 $TEMPLATE_SOURCE"
    exit 1
fi

cp -r "$TEMPLATE_SOURCE"/* "$OUTPUT_DIR/"

# 处理页面内容
echo "🔄 处理页面内容..."

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
        # 替换学习模板的标题
        sed -i.bak "s/📖 我的学习笔记分享/$PAGE_TITLE/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/记录学习过程中的重要知识点和心得体会/$PAGE_SUBTITLE/g" "$OUTPUT_DIR/index.html"
        
        # 替换核心亮点内容
        if [ ! -z "$HIGHLIGHT_CONTENT" ]; then
            HIGHLIGHT_HTML=$(echo "$HIGHLIGHT_CONTENT" | sed 's/$/\\n/g' | tr -d '\n' | sed 's/\\n/<br>/g')
            sed -i.bak "s/今天学习了网页制作的基础知识，掌握了HTML、CSS的基本用法。最重要的收获是理解了如何将静态内容转换为可分享的网页形式，这为知识传播提供了新的可能性。/$HIGHLIGHT_HTML/g" "$OUTPUT_DIR/index.html"
        fi
        
        # 从 content.md 动态创建学习内容HTML
        echo "🔄 从content.md动态生成内容..."
        
        # 创建学习要点区域
        cat > /tmp/sql_content.html << 'EOF'
        <!-- 核心学习要点 -->
        <div class="learning-points">
            <h3>🎯 核心亮点</h3>
EOF
        
        # 添加核心亮点内容
        echo "            <p>$HIGHLIGHT_CONTENT</p>" >> /tmp/sql_content.html
        echo "        </div>" >> /tmp/sql_content.html
        echo "" >> /tmp/sql_content.html
        
        # 创建主要内容区域
        echo "        <!-- 详细内容区域 -->" >> /tmp/sql_content.html
        echo "        <section class=\"content-section\">" >> /tmp/sql_content.html
        
        # 将主要内容部分转换为HTML并添加（使用改进的转换函数）
        MAIN_CONTENT_HTML=$(echo "$FULL_MAIN_CONTENT" | awk '
            BEGIN { in_table = 0; in_quote = 0; in_code = 0; quote_content = "" }
            
            # 处理表格
            /^\|.*\|.*\|/ {
                # 结束任何开放的引用块
                if (in_quote == 1) {
                    print "<blockquote>" quote_content "</blockquote>"
                    in_quote = 0
                    quote_content = ""
                }
                
                if (in_table == 0) {
                    # 开始表格
                    print "<table class=\"data-table\">"
                    print "<thead>"
                    print "<tr>"
                    # 处理表头
                    gsub(/^\|/, "")
                    gsub(/\|$/, "")
                    split($0, cols, /\|/)
                    for (i = 1; i <= length(cols); i++) {
                        gsub(/^[ \t]+|[ \t]+$/, "", cols[i])
                        print "<th>" cols[i] "</th>"
                    }
                    print "</tr>"
                    print "</thead>"
                    print "<tbody>"
                    in_table = 1
                    next
                } else {
                    # 跳过分隔符行
                    if (/^[|:\-\s]+$/) {
                        next
                    }
                    # 处理表格数据行
                    print "<tr>"
                    gsub(/^\|/, "")
                    gsub(/\|$/, "")
                    split($0, cols, /\|/)
                    for (i = 1; i <= length(cols); i++) {
                        gsub(/^[ \t]+|[ \t]+$/, "", cols[i])
                        # 处理代码标记
                        gsub(/`([^`]*)`/, "<code>\\1</code>", cols[i])
                        print "<td>" cols[i] "</td>"
                    }
                    print "</tr>"
                    next
                }
            }
            
            # 非表格行，结束表格
            !/^\|.*\|.*\|/ && in_table == 1 {
                print "</tbody>"
                print "</table>"
                in_table = 0
            }
            
            # 处理其他内容
            !/^\|.*\|.*\|/ {
                # 处理标题
                if (/^#### /) { 
                    # 结束任何开放的引用块
                    if (in_quote == 1) {
                        print "<blockquote>" quote_content "</blockquote>"
                        in_quote = 0
                        quote_content = ""
                    }
                    gsub(/^#### /, ""); print "<h4>" $0 "</h4>"; next 
                }
                if (/^### /) { 
                    # 结束任何开放的引用块
                    if (in_quote == 1) {
                        print "<blockquote>" quote_content "</blockquote>"
                        in_quote = 0
                        quote_content = ""
                    }
                    gsub(/^### /, ""); print "<h3>" $0 "</h3>"; next 
                }
                if (/^## /) { 
                    # 结束任何开放的引用块
                    if (in_quote == 1) {
                        print "<blockquote>" quote_content "</blockquote>"
                        in_quote = 0
                        quote_content = ""
                    }
                    gsub(/^## /, ""); print "<h2>" $0 "</h2>"; next 
                }
                
                # 处理代码块
                if (/^```/) {
                    # 结束任何开放的引用块
                    if (in_quote == 1) {
                        print "<blockquote>" quote_content "</blockquote>"
                        in_quote = 0
                        quote_content = ""
                    }
                    if (in_code == 0) {
                        print "<pre><code>"
                        in_code = 1
                    } else {
                        print "</code></pre>"
                        in_code = 0
                    }
                    next
                }
                
                # 处理引用块（合并连续的引用行）
                if (/^> /) {
                    gsub(/^> /, "")
                    # 处理粗体
                    gsub(/\*\*([^*]*)\*\*/, "<strong>\\1</strong>")
                    if (in_quote == 0) {
                        quote_content = "<p>" $0
                        in_quote = 1
                    } else {
                        quote_content = quote_content "<br>" $0
                    }
                    next
                }
                
                # 非引用行，结束引用块
                if (in_quote == 1 && !/^> /) {
                    print "<blockquote>" quote_content "</p></blockquote>"
                    in_quote = 0
                    quote_content = ""
                }
                
                # 处理分隔符
                if (/^---$/) {
                    print "<hr>"
                    next
                }
                
                # 处理列表项
                if (/^- /) {
                    gsub(/^- /, "")
                    # 处理代码标记和粗体
                    gsub(/`([^`]*)`/, "<code>\\1</code>")
                    gsub(/\*\*([^*]*)\*\*/, "<strong>\\1</strong>")
                    print "<li>" $0 "</li>"
                    next
                }
                
                # 处理空行
                if (/^$/) {
                    next
                }
                
                # 处理普通段落
                if (!/^[<#*`>-]/ && !/^```/ && !/^\|/ && !/^---$/) {
                    # 处理粗体和代码标记
                    gsub(/\*\*([^*]*)\*\*/, "<strong>\\1</strong>")
                    gsub(/`([^`]*)`/, "<code>\\1</code>")
                    print "<p>" $0 "</p>"
                }
            }
            
            END {
                # 确保引用块和表格正确结束
                if (in_quote == 1) {
                    print "<blockquote>" quote_content "</p></blockquote>"
                }
                if (in_table == 1) {
                    print "</tbody>"
                    print "</table>"
                }
            }
        ')
        
        echo "$MAIN_CONTENT_HTML" >> /tmp/sql_content.html
        echo "        </section>" >> /tmp/sql_content.html
        echo "" >> /tmp/sql_content.html
        
        # 添加个人感悟部分
        echo "        <!-- 学习心得 -->" >> /tmp/sql_content.html
        echo "        <section class=\"content-section\">" >> /tmp/sql_content.html
        echo "            <h2>💡 个人感悟</h2>" >> /tmp/sql_content.html
        
        INSIGHT_HTML=$(echo "$INSIGHT_CONTENT" | sed '
            s/\*\*\([^*]*\)\*\*/<strong>\1<\/strong>/g
            /^$/s/^$/<br>/g
            /^[^<]/s/^/<p>/
            /^<p>/s/$/<\/p>/
        ')
        echo "$INSIGHT_HTML" >> /tmp/sql_content.html
        echo "        </section>" >> /tmp/sql_content.html
        echo "" >> /tmp/sql_content.html
        
        # 添加下一步计划部分
        echo "        <!-- 下一步计划 -->" >> /tmp/sql_content.html
        echo "        <section class=\"content-section\">" >> /tmp/sql_content.html
        echo "            <h2>📊 下一步计划</h2>" >> /tmp/sql_content.html
        
        PLAN_HTML=$(echo "$PLAN_CONTENT" | sed '
            s/\*\*\([^*]*\)\*\*/<strong>\1<\/strong>/g
            s/^- \(.*\)/<li>\1<\/li>/g
            /^$/s/^$/<br>/g
            /^[^<-]/s/^/<p>/
            /^<p>/s/$/<\/p>/
        ')
        echo "$PLAN_HTML" >> /tmp/sql_content.html
        echo "        </section>" >> /tmp/sql_content.html
        
        # 使用更简单的方法：分割HTML文件并重新组合
        # 获取HTML头部（到核心学习要点之前）
        sed -n '1,/<!-- 核心学习要点 -->/p' "$OUTPUT_DIR/index.html" | sed '$d' > /tmp/html_head.tmp
        
        # 获取HTML尾部（从分享按钮开始）
        sed -n '/<!-- 分享按钮 -->/,$p' "$OUTPUT_DIR/index.html" > /tmp/html_tail.tmp
        
        # 重新组合HTML文件
        cat /tmp/html_head.tmp > "$OUTPUT_DIR/index.html"
        echo "<!-- 替换为完整的SQL学习内容 -->" >> "$OUTPUT_DIR/index.html"
        cat /tmp/sql_content.html >> "$OUTPUT_DIR/index.html"
        cat /tmp/html_tail.tmp >> "$OUTPUT_DIR/index.html"
        
        # 清理临时文件
        rm -f /tmp/sql_content.html /tmp/html_head.tmp /tmp/html_tail.tmp
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
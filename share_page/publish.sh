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
        
        # 替换核心亮点内容
        if [ ! -z "$HIGHLIGHT_CONTENT" ]; then
            HIGHLIGHT_HTML=$(echo "$HIGHLIGHT_CONTENT" | sed 's/$/\\n/g' | tr -d '\n' | sed 's/\\n/<br>/g')
            sed -i.bak "s/今天学习了网页制作的基础知识，掌握了HTML、CSS的基本用法。最重要的收获是理解了如何将静态内容转换为可分享的网页形式，这为知识传播提供了新的可能性。/$HIGHLIGHT_HTML/g" "$OUTPUT_DIR/index.html"
        fi
        
        # 替换"今日学习要点"标题
        sed -i.bak "s/💡 今日学习要点/🎯 核心亮点/g" "$OUTPUT_DIR/index.html"
        
        # 替换"学习内容总结"标题
        sed -i.bak "s/学习内容总结/📝 主要内容/g" "$OUTPUT_DIR/index.html"
        
        # 彻底替换主要内容部分 - 用SQL学习相关内容
        sed -i.bak "s/今天的学习主要围绕<strong>网页制作技术<\/strong>展开，涵盖了以下几个重要方面：/已完成回收宝业务数据库深度分析，掌握了以下SQL核心技能：/g" "$OUTPUT_DIR/index.html"
        
        # 替换具体的学习内容列表
        sed -i.bak "s/<strong>🎯 HTML基础：<\/strong><br>/<strong>📊 SQL基础语法：<\/strong><br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 了解了HTML的基本结构和常用标签<br>/• 掌握了SELECT、FROM、WHERE等基础查询语法<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 学会了如何组织页面内容的层次结构<br>/• 学会了JOIN表连接和GROUP BY分组统计<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 掌握了语义化标签的重要性和使用方法/• 掌握了窗口函数和复杂子查询技巧/g" "$OUTPUT_DIR/index.html"
        
        sed -i.bak "s/<strong>🎨 CSS样式：<\/strong><br>/<strong>🏢 业务理解能力：<\/strong><br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 学习了CSS选择器和基本属性<br>/• 深度理解回收宝二手电商业务模式<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 理解了盒模型的概念和布局原理<br>/• 掌握数据仓库分层架构设计原理<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 掌握了响应式设计的基本思路/• 学会了实时监控和质量控制体系设计/g" "$OUTPUT_DIR/index.html"
        
        sed -i.bak "s/<strong>🚀 实战应用：<\/strong><br>/<strong>📈 实际成果：<\/strong><br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 成功创建了个人分享页面<br>/• 已完成20个SQL文件的注释和分析<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 学会了使用GitHub Pages发布网站<br>/• 掌握了55个数据库表的业务逻辑<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 理解了版本控制的重要性/• 建立了完整的数据分析知识体系/g" "$OUTPUT_DIR/index.html"
        
        # 替换学习心得部分
        sed -i.bak "s/学习心得/💡 个人感悟/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/通过今天的学习，我深刻体会到<strong>技术学习的乐趣<\/strong>。从最初的一头雾水，到最后成功发布自己的网页，这个过程让我明白了：/通过这次深入的SQL学习和回收宝数据库分析，我深刻体会到<strong>技术与业务结合的重要性<\/strong>。从零基础到掌握企业级数据分析，这个过程让我明白了：/g" "$OUTPUT_DIR/index.html"
        
        # 替换下一步计划标题和内容
        sed -i.bak "s/下一步学习计划/📊 下一步计划/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/基于今天的学习成果，我制定了以下学习计划：/基于SQL学习成果，我制定了以下数据分析发展计划：/g" "$OUTPUT_DIR/index.html"
        
        # 替换短期目标
        sed -i.bak "s/• 深入学习CSS高级特性，如动画和过渡效果<br>/• 完成剩余35个SQL文件的注释理解<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 练习制作更多不同类型的网页<br>/• 深入学习窗口函数和高级SQL特性<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 学习JavaScript基础，为网页添加交互功能/• 掌握SQL性能调优和数据分析工具/g" "$OUTPUT_DIR/index.html"
        
        # 替换中期目标
        sed -i.bak "s/• 掌握响应式设计的高级技巧<br>/• 能够独立设计数据库表结构<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 学习使用前端框架（如Bootstrap）<br>/• 掌握数据仓库建模方法<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 创建一个完整的个人网站项目/• 具备独立的数据分析和可视化能力/g" "$OUTPUT_DIR/index.html"
        
        # 替换长期目标
        sed -i.bak "s/• 学习后端开发基础<br>/• 成为数据分析领域的专家<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 理解全栈开发的概念<br>/• 具备完整的数据架构设计能力<br>/g" "$OUTPUT_DIR/index.html"
        sed -i.bak "s/• 能够独立完成小型Web应用项目/• 能够为业务决策提供数据支撑/g" "$OUTPUT_DIR/index.html"
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
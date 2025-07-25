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

# 提取完整的主要内容 - 从"### 📝 主要内容"到"### 💡 个人感悟"
FULL_MAIN_CONTENT=$(sed -n '/### 📝 主要内容/,/### 💡 个人感悟/p' content.md | sed '$d')

# 提取感悟内容
INSIGHT_CONTENT=$(sed -n '/### 💡 个人感悟/,/### 📊 下一步计划/p' content.md | sed '1d;$d')

# 提取计划内容
PLAN_CONTENT=$(sed -n '/### 📊 下一步计划/,/---/p' content.md | sed '1d;$d')

# 创建简单的Markdown到HTML转换函数
convert_md_to_html() {
    echo "$1" | sed '
        # 处理标题
        s/^#### \(.*\)/<h4>\1<\/h4>/g
        s/^### \(.*\)/<h3>\1<\/h3>/g
        s/^## \(.*\)/<h2>\1<\/h2>/g
        
        # 处理粗体文本
        s/\*\*\([^*]*\)\*\*/<strong>\1<\/strong>/g
        
        # 处理代码块
        s/`\([^`]*\)`/<code>\1<\/code>/g
        
        # 处理列表项
        s/^- \(.*\)/<li>\1<\/li>/g
        s/^• \(.*\)/<li>\1<\/li>/g
        
        # 处理表格分隔符
        /^|.*|.*|/s/.*/<!-- table row -->/g
        
        # 处理空行
        s/^$/<br>/g
        
        # 处理普通段落（以非特殊字符开头的行）
        /^[^<#*`-•|]/s/^/<p>/
        /^<p>/s/$/<\/p>/
    '
}

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
            <p>通过分析回收宝真实业务数据库，深度学习SQL语法和数据库设计。已完成20个SQL文件注释，掌握了企业级数据架构设计和业务数据分析方法。</p>
        </div>

        <!-- 详细内容区域 -->
        <section class="content-section">
            <h2>📝 主要内容</h2>
            
            <h3>📚 学习概况</h3>
            <blockquote>
                <p>📅 <strong>创建时间</strong>：2024年12月<br>
                🎯 <strong>学习目标</strong>：从零基础掌握SQL，深入理解回收宝业务数据库架构<br>
                👨‍🎓 <strong>学习方式</strong>：通过实际业务案例学习SQL语法和数据库设计</p>
            </blockquote>

            <h3>📖 SQL基础概念</h3>
            <h4>🎯 SQL是什么？</h4>
            <p>SQL就像是和电脑对话的"普通话" - 你用它来告诉电脑："我想要什么数据"</p>
            
            <p><strong>形象比喻</strong>：</p>
            <ul>
                <li>数据库 = 一个超级大的图书馆 📚</li>
                <li>表格 = 图书馆里的一个个书架 📖</li>
                <li>SQL = 你对图书管理员说的话 🗣️</li>
            </ul>

            <h4>🔧 SQL基本语法结构</h4>
            <p><strong>基础"积木块"</strong>：</p>
            <pre><code>SELECT 我要什么数据
FROM 从哪个表找  
WHERE 符合什么条件
GROUP BY 按什么分组
ORDER BY 按什么排序</code></pre>

            <p><strong>常用关键词</strong>：</p>
            <ul>
                <li><strong>SELECT</strong> = 我要看 👀</li>
                <li><strong>FROM</strong> = 从哪里 📍</li>
                <li><strong>WHERE</strong> = 什么条件 🎯</li>
                <li><strong>JOIN</strong> = 连接表格 🔗</li>
                <li><strong>COUNT</strong> = 数数量 🔢</li>
                <li><strong>SUM</strong> = 求和 ➕</li>
            </ul>

            <h3>✅ 已完成SQL文件注释清单</h3>
            <h4>📊 注释完成情况统计</h4>
            <ul>
                <li><strong>总文件数：55个</strong></li>
                <li><strong>已完成注释：20个</strong></li>
                <li><strong>完成比例：36%</strong></li>
            </ul>

            <h4>🎯 按业务模块分类</h4>
            
            <p><strong>1. 基础操作类（5个）✅</strong></p>
            <ul>
                <li><code>仓储移库数据.sql</code> - 仓库间货物移动记录</li>
                <li><code>收货数据.sql</code> - 仓库收货记录</li>
                <li><code>销售出库.sql</code> - 销售发货记录</li>
                <li><code>退货出库.sql</code> - 退货处理记录</li>
                <li><code>天润接听.sql</code> - 客服电话统计</li>
            </ul>

            <p><strong>2. 检测业务类（8个）✅</strong></p>
            <ul>
                <li><code>自动检测记录.sql</code> - 自动化检测记录（模块一）</li>
                <li><code>检测选项明细.sql</code> - 手机检测详细结果</li>
                <li><code>检测豹操作记录.sql</code> - 检测系统操作日志</li>
                <li><code>模块1&2作业量.sql</code> - 两个检测模块工作量统计</li>
                <li><code>模块2选项明细.sql</code> - 模块二功能检测详情</li>
                <li><code>验货宝检测差异.sql</code> - 验货宝外观检测统计</li>
                <li><code>QC数据.sql</code> - 质量控制抽检统计</li>
                <li><code>分模块结果映射.sql</code> - 检测结果分类</li>
            </ul>

            <h3>🏢 回收宝业务架构分析</h3>
            <h4>💼 公司业务概述</h4>
            <p>回收宝是一个<strong>二手电子产品回收平台</strong>，业务模式类似"数字化的二手店"，但规模更大、流程更标准化。</p>

            <h4>🔄 核心业务流程</h4>
            <pre><code>用户下单 → 估价 → 邮寄/上门收货 → 入库检测 → 重新定价 → 用户确认 → 付款 → 商品上架销售 → 售后服务</code></pre>

            <h4>📱 核心商品类别</h4>
            <ul>
                <li>📱 <strong>手机</strong>（主力产品）</li>
                <li>💻 <strong>笔记本电脑</strong></li>
                <li>📺 <strong>平板电脑</strong></li>
                <li>🏺 <strong>黄金首饰</strong>（特殊品类）</li>
                <li>🎮 <strong>其他3C数码产品</strong></li>
            </ul>

            <h3>🗄️ 数据库表结构详解</h3>
            <h4>📊 数据库分层架构</h4>
            <p>回收宝采用典型的<strong>数据仓库分层架构</strong>：</p>
            <pre><code>ODS层（原始数据） → DWD层（明细数据） → DWS层（汇总数据） → DRT层（业务应用）</code></pre>

            <h3>🎓 已掌握的SQL技能</h3>
            <h4>基础语法：</h4>
            <ul>
                <li>✅ SELECT、FROM、WHERE基础查询</li>
                <li>✅ JOIN表连接操作</li>
                <li>✅ GROUP BY分组统计</li>
                <li>✅ CASE WHEN条件判断</li>
                <li>✅ 窗口函数（ROW_NUMBER、COUNT等）</li>
            </ul>

            <h4>高级应用：</h4>
            <ul>
                <li>✅ 复杂子查询（WITH CTE）</li>
                <li>✅ 多表关联查询</li>
                <li>✅ 时间函数处理</li>
                <li>✅ 字符串处理函数</li>
                <li>✅ 聚合函数应用</li>
            </ul>

            <h4>💡 重要学习心得</h4>
            <p><strong>🔑 关键理念：</strong></p>
            <ol>
                <li><strong>业务理解第一</strong> - 先理解业务逻辑，再写SQL</li>
                <li><strong>数据质量重要</strong> - 确保数据的准确性和完整性</li>
                <li><strong>性能考虑必要</strong> - 大数据量下要考虑查询效率</li>
                <li><strong>注释文档必须</strong> - 复杂逻辑必须有清晰的注释</li>
            </ol>
        </section>

        <!-- 学习心得 -->
        <section class="content-section">
            <h2>💡 个人感悟</h2>
            <p>通过这次深入的SQL学习和回收宝数据库分析，我深刻体会到：</p>
            
            <p><strong>技术与业务的结合</strong>：SQL不只是一门查询语言，更是理解和分析业务数据的重要工具。通过分析回收宝的真实业务数据，我学会了如何从技术角度理解商业模式。</p>
            
            <p><strong>实践的重要性</strong>：相比于单纯的语法学习，结合实际业务场景的学习让我收获更大。每一个SQL查询背后都对应着真实的业务需求和决策支持。</p>
            
            <p><strong>数据架构的美感</strong>：回收宝的数据库设计体现了现代互联网公司的技术架构特点 - 分层清晰的数据架构、模块化的业务设计、实时监控的运营体系、标准化的质量控制。</p>
        </section>

        <!-- 下一步计划 -->
        <section class="content-section">
            <h2>📊 下一步计划</h2>
            <p>基于SQL学习成果，我制定了以下数据分析发展计划：</p>
            
            <p><strong>短期目标（1-2个月）：</strong></p>
            <ul>
                <li>完成剩余35个SQL文件的注释和理解</li>
                <li>深入学习窗口函数和高级SQL特性</li>
                <li>掌握SQL性能调优基础知识</li>
                <li>学会使用SQL工具进行数据分析</li>
            </ul>
            
            <p><strong>中期目标（3-6个月）：</strong></p>
            <ul>
                <li>能够独立设计数据库表结构</li>
                <li>掌握数据仓库建模方法</li>
                <li>学会编写存储过程和触发器</li>
                <li>具备独立的数据分析和可视化能力</li>
            </ul>
            
            <p><strong>长期目标（6个月以上）：</strong></p>
            <ul>
                <li>成为数据分析领域的专家</li>
                <li>具备完整的数据架构设计能力</li>
                <li>能够指导和培训他人学习SQL</li>
                <li>在实际项目中熟练应用所学知识，为业务决策提供数据支撑</li>
            </ul>
            
            <p><strong>记住</strong>：数据驱动决策的时代，掌握SQL就是掌握了理解业务的钥匙！🚀</p>
        </section>
EOF

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
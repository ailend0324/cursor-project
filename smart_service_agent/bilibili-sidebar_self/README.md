# Bilibili 广告跳过工具（切片广告之友）

这是一个Chrome扩展，用于自动跳过哔哩哔哩(Bilibili)视频中的广告内容。它提供了直观的用户界面和丰富的功能，使视频观看体验更加流畅。

## 项目迁移状态

本项目正在从 Manifest V2 向 Manifest V3 进行迁移。迁移进度如下：

- ✅ **核心通信架构** - 已完成服务工作者(Service Worker)的实现和通信模块的迁移
- ✅ **网络请求模块** - 已完成基于后台服务工作者的网络请求机制改造
- ⬜ **存储机制优化** - 计划中
- ⬜ **内容脚本优化** - 计划中
- ⬜ **权限模型调整** - 计划中
- ⬜ **UI交互适配** - 计划中

### 迁移执行标准

- **单一路径原则** - 所有业务逻辑必须有一条清晰且唯一的执行路径，不允许存在向后兼容或妥协分支代码
- **零容错处理** - 在关键路径上使用"不是0就是1"的设计理念，失败时快速抛出错误而非尝试恢复
- **模块化通信** - 所有跨模块通信必须通过标准化的接口进行，避免直接依赖
- **权限最小化** - 严格遵循最小权限原则，仅声明必要的权限

### 已处理干净的模块

- ✅ **background.js** - 基于Service Worker的后台服务模块
- ✅ **communication.js** - 内容脚本与后台通信模块
- ✅ **services/serviceIndex.js** - 所有API服务已迁移至使用后台通信
- ⬜ **storage.js** - 部分迁移完成，仍需进一步优化
- ⬜ **videoMonitor.js** - 部分迁移完成，仍需进一步优化
- ⬜ **utils.js** - 部分迁移完成，仍需进一步优化

## 功能特点

- 自动检测和跳过视频中的广告
- 广告区域在进度条上可视化标记
- 支持为每个视频单独设置广告时间段
- 自动保存广告时间段，再次观看时无需重复设置
- 支持通过URL参数共享广告时间段
- UP主白名单功能，支持特定UP主视频切换为手动跳过模式
- 全局开关控制，随时可以启用/禁用功能
- 支持调整广告跳过的触发范围（从1%到100%）
- 管理员模式，用于高级设置和数据管理

## 安装步骤

1. 下载本项目并解压
2. 将SVG图标转换为PNG格式（需要使用图像编辑软件）
   - `icons/icon16.svg` -> `icons/icon16.png`
   - `icons/icon48.svg` -> `icons/icon48.png`
   - `icons/icon128.svg` -> `icons/icon128.png`
3. 打开Chrome浏览器，进入扩展管理页面（chrome://extensions/）
4. 开启"开发者模式"
5. 点击"加载已解压的扩展程序"
6. 选择项目文件夹

## 使用方法

1. 访问B站视频页面时，会在右上角显示"⏩ 广告跳过"按钮
2. 点击按钮设置广告时间段，格式: `开始-结束,开始-结束`
3. 例如: `61-87,120-145` 表示跳过61秒到87秒和120秒到145秒的广告
4. 点击"更新跳过设置"按钮使设置生效
5. 设置会自动保存，下次观看该视频时会自动跳过广告

### 广告位可视化标记

- 视频进度条上以红色区域标记完整广告区间
- 粉红色区域表示触发广告跳过的实际区间（基于设置的百分比）
- 鼠标悬停在广告标记上可显示详细信息
- 点击广告标记可以手动跳过广告

### 全局开关与跳过百分比

- 点击"⏩ 广告跳过"按钮打开控制面板
- 面板顶部有一个开关，可以临时启用/禁用广告跳过功能
- 使用百分比滑块控制广告跳过的触发范围：
  - 1%: 仅在广告开始时触发跳过
  - 50%: 在广告前半段触发跳过
  - 100%: 整个广告区间都会触发跳过

### UP主白名单功能

1. 在视频页面点击"⏩ 广告跳过"按钮
2. 在控制面板中会显示当前UP主信息
3. 使用"白名单"开关将当前UP主添加/移除白名单
4. 白名单中UP主的视频不会自动跳过广告，但仍可通过点击广告标记手动跳过
5. 在扩展选项页面的"UP主白名单"选项卡可以批量管理白名单

### 通过URL分享

1. 在设置界面输入广告时间段后，点击"创建分享链接"按钮
2. 复制生成的链接分享给他人
3. 他人点击链接后，插件会自动应用广告跳过设置

## 项目架构

插件采用模块化设计，主要由以下模块组成：

1. **核心模块** (core.js)：插件入口点，初始化和全局状态管理
2. **工具模块** (utils.js)：通用工具函数，日志处理、DOM操作等
3. **存储模块** (storage.js)：数据存储和加载，管理广告时间戳和白名单
4. **视频监控** (videoMonitor.js)：视频播放监控和广告跳过逻辑
5. **用户界面** (ui.js)：控制面板和交互界面管理
6. **管理面板** (adminPanel.js)：管理员功能和数据管理
7. **选项页面** (options.js)：插件设置和白名单批量管理
8. **弹出页面** (popup.js)：快速访问和插件信息
9. **后台服务** (background.js)：后台服务工作者，处理跨页面通信和网络请求
10. **通信模块** (communication.js)：内容脚本与后台服务工作者的通信接口

## 后续优化方向

1. **完成 Manifest V3 迁移**：按照执行标准完成所有模块的迁移工作
   - ✅ 解决广告跳过百分比在UI.js和options.js之间的同步问题
   - ⏳ 解决白名单在UI.js和options.js之间的同步问题
   - ⬜ 重构存储模块，遵循服务工作者的生命周期特性
   - ⬜ 优化权限模型，遵循最小权限原则

2. **状态管理改进**：实现集中式状态管理，提高状态同步效率
   - 开发统一的状态管理器，处理UI和选项页面的状态同步
   - 重构现有的基于chrome.storage.onChanged机制的事件监听
   - 确保白名单数据在不同上下文间保持一致

3. **组件化重构**：将UI逻辑抽象为可复用组件，简化维护

4. **懒加载优化**：按需加载和初始化模块，提高性能

5. **事件系统优化**：统一事件处理机制，减少冗余代码

6. **白名单管理优化**：统一白名单操作，完善数据结构
   - 重新设计白名单数据的存储和同步方式
   - 优化查询效率和更新机制
   - 解决UI.js和options.js的白名单状态不同步问题

## 备忘优化-latest 250404
URL和储存数据的优化逻辑——处理顺序的简化。但可以先跑通。

## 许可证

MIT
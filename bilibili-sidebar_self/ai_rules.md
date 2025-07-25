# 代码优化规范与标准

本文档定义了Chrome插件项目的代码优化标准，特别是针对存储模块的重构和优化。这些规则适用于所有代码审查和优化工作。

## 1. 冗余代码界定标准

冗余代码是指不必要的、重复的或可合并的代码，具体标准如下：

### 1.1 功能重复
- 同一功能在多个地方有不同实现
- 未使用统一的公共方法处理相同逻辑
- 多个模块执行相同的存储操作

### 1.2 职责混乱
- 与模块主要责任无关的功能应当移除
- 不符合单一职责原则的代码设计
- 存储操作未集中在storage模块

### 1.3 重复存储
- 同一数据在多处重复管理和存储
- 未使用统一的键名常量
- 直接使用字符串作为存储键而非常量引用

## 2. 低效代码界定标准

低效代码是指执行效率不高、结构复杂或难以维护的代码，具体标准如下：

### 2.1 异步处理问题
- 使用多层回调函数嵌套而非Promise链式调用
- 未使用async/await简化异步流程
- 缺少错误处理或错误传递机制

### 2.2 性能问题
- 重复计算：频繁执行的函数中存在可缓存的计算
- 未使用节流/防抖处理频繁事件
- 存在不必要的DOM操作或查询

### 2.3 结构问题
- 过长函数（超过50行）未拆分为小函数
- 使用全局变量而非模块内私有变量
- 使用同步阻塞操作而非异步操作

## 3. 不能接受的修改情况

以下情况在代码优化中绝对不允许出现：

### 3.1 业务逻辑问题
- 破坏核心功能或导致功能失效
- 改变既有API的行为或返回值结构
- 移除必要的业务检查或验证
- **不可约化原则**：每个业务判断、分支条件和处理逻辑都必须保持原样，不得擅自简化或合并
- **逻辑等价原则**：必须保证修改前后的逻辑功能完全等价，不能改变任何输入与输出的对应关系

### 3.2 设计问题
- 添加不必要的复杂性
- 引入过度设计和不需要的抽象层
- 创建不符合项目风格的新模式
- **禁止简化**：不得擅自简化既有设计，即使代码看起来冗余也必须保持原设计意图
- **修改标准**：只有在完全理解代码意图且能确保行为一致的情况下才能进行修改

### 3.3 迁移问题
- 存储相关功能未完全集中到storage.js
- 未移除直接调用chrome.storage.local的代码
- 保留不必要的兼容性逻辑或旧版本代码
- **功能等同**：修改后的代码必须与原代码在所有可能的情况下都产生相同的结果
- **保留控制流**：不得改变原有代码的执行路径、条件检查顺序和错误处理机制

## 4. 模块职责分配

### 4.1 storage.js
- 负责所有与存储相关的操作
- 提供统一的存储接口
- 处理数据验证和格式化
- 管理存储键名常量

### 4.2 videoMonitor.js
- 负责视频监控和广告跳过
- 通过storage.js接口获取和保存数据
- 不直接操作chrome.storage
- 处理视频状态变化和广告检测

### 4.3 core.js
- 负责全局初始化和协调
- 管理全局状态和配置
- 协调各模块之间的交互
- 处理插件生命周期事件

## 5. 代码风格规范

### 5.1 日志输出
- 统一使用adskipUtils.logDebug记录日志
- 避免使用console.log、console.error等直接输出
- 合理使用日志级别和节流控制

### 5.2 异步处理
- 优先使用Promise和async/await
- 避免多层嵌套回调
- 确保异步错误被正确捕获和处理

### 5.3 变量声明
- 使用let/const代替var
- 避免全局变量污染
- 使用有意义的变量名和注释

### 5.4 函数设计
- 遵循单一职责原则
- 函数参数不超过3个
- 提供清晰的函数文档注释
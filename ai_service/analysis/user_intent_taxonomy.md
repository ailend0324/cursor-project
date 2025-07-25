# 回收宝用户意图分类体系（基于数据分析）

*生成时间: 2025-04-16 10:06:26*

## 意图分类总览

- 业务场景意图: 10 个
- 交互类意图: 1 个
- 其他意图: 4 个

## 1. 业务场景意图

### 1.1 回收业务

#### 流程咨询
- **关键词**: 你好, 验货, 手机, 回收, 摄像头
- **示例**:
  - "你好我昨天说的450结果怎么样"
  - "你好，显示物流配送异常"
  - "你好 验机报告中摄像头黑斑是否有摄像头污渍？"

#### 流程咨询
- **关键词**: 这么, 划痕, 质检, 你们, 拍照
- **示例**:
  - "都是这么说"
  - "这么大的变色区域"
  - "这么压价"

#### 价格咨询
- **关键词**: 价格, 回收, 预估, 满意, 太低
- **示例**:
  - "你刚刚提到的系统申请价格从628变化到574，我们让当事人现场进行调查"
  - "会不会？ 到时候过去故意压低我的价格，到时候把我零件换了"
  - "预估价和到手价格应该不会差太多吧"

### 1.2 售后服务

#### 订单跟踪
- **关键词**: 验货, 手机, 退回, 划痕, 回收
- **示例**:
  - "jc"
  - "退货不包邮？"
  - "2505895032555682879"

#### 订单跟踪
- **关键词**: 订单号, 4263065173189898940, 2516074035909682879, 2426685242420682879, 2508634056668309373
- **示例**:
  - "订单号为以上的苹果笔记本电脑可否重新报价"
  - "那请问哪里看订单号呀"
  - "订单号:2492479563874682879"

#### 故障咨询
- **关键词**: 没有, 划痕, 屏幕, 手机, 你们
- **示例**:
  - "没有物流信息"
  - "物流没有信息"
  - "没有拆机验机吗？"

#### 订单跟踪
- **关键词**: 卖家, 验货, 发货, 聊天记录, 充电
- **示例**:
  - "卖家拒收我信息"
  - "因为卖家承诺无拆修 我想问问"
  - "卖家着急"

#### 订单跟踪
- **关键词**: 这个, 订单, 手机, 验货, 回收
- **示例**:
  - "这个收货地址是哪里"
  - "我这个是相机，他们顺丰打包会不会包装"
  - "我这个单还要多久能收货啊"

### 1.3 客户服务

#### 人工服务
- **关键词**: 人工, 服务, 直连, 联系, 等级
- **示例**:
  - "人工电话"
  - "人工联系我处理"
  - "高X等级用户直连人工请求"

#### 人工服务
- **关键词**: 客服, 人工, 联系, 验货, 语音
- **示例**:
  - "昨天我问客服"
  - "客服"
  - "客服呢"

## 2. 交互类意图

### 2.1 问候类

### 2.2 确认类

#### 用户确认
- **关键词**: 可以, 验货, 手机, 检测, 开机
- **示例**:
  - "可以拍拆机内部图片给我吗"
  - "不取消的情况可以给我更换其他工作人员上门吗"
  - "收到后是可以的，但是一恢复出厂设置就黑屏了"

## 3. 其他意图

#### 聚类3
- **关键词**: img, src, https, alicdn, com
- **示例**:
  - "<img src='https://img.alicdn.com/imgextra/i2/2201405633007/O1CN01H58kcX1Y5G11ir9Vl_!!2201405633007-0-alxm.jpg'>"
  - "<img src='https://img.alicdn.com/imgextra/i1/4062835174/O1CN01N67ikQ1o5kHozaxFH_!!4062835174-0-alxm.jpg'>"
  - "<img src='https://img.alicdn.com/imgextra/i1/3787018373/O1CN01xYYQ3n2BitIcO19iG_!!3787018373-0-alxm.jpg'>"

#### 聚类8
- **关键词**: 谢谢, 一下, 没事, 麻烦, 尽快
- **示例**:
  - "尽快谢谢"
  - "谢谢 尽快哈"
  - "嗯呐，尽快吧谢谢"

#### 聚类12
- **关键词**: 你们, 检测, 手机, 验货, 顺丰
- **示例**:
  - "回来如果机器受到额外的损伤的话，你们就等着被投诉吧"
  - "你们要是这样压价  那我直接投诉12345或者消协"
  - "因为你们要是拆机的话会影响我在咸鱼售卖"

#### 聚类13
- **关键词**: 不是, 手机, 你们, 划痕, 回收
- **示例**:
  - "不是说签收24小时之内吗"
  - "因为图片看的不是太直观"
  - "之前不是说24小时"

## 应用指导

### 知识库构建
基于以上意图分类，建议按以下方向构建知识库：

1. **价格咨询**: 建立不同设备型号的价格查询系统
2. **流程咨询**: 详细说明回收流程、步骤和所需材料
3. **设备信息**: 创建设备型号库，包含各型号详细规格
4. **数据安全**: 提供数据删除指南和隐私保护措施
5. **订单跟踪**: 设计订单状态查询接口和自动通知系统

### 机器人设计
在对话机器人设计中建议重点关注：

1. 优化**交互类意图**处理，确保基础对话流畅
2. 针对**价格咨询**和**流程咨询**这两个高频业务场景进行深度优化
3. 对**人工服务**请求设置智能识别和转接规则
4. 设计兜底策略，处理未能识别的意图

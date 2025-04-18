# 回收宝AI客服知识库样例

## 1. 常见问题示例（FAQs）

### 1.1 产品咨询类

#### 价格咨询
```json
{
  "id": "FAQ_001",
  "category": "产品咨询类/产品价格",
  "question": {
    "standard": "回收价格是如何确定的？",
    "variants": [
      "手机回收能卖多少钱？",
      "如何知道我的设备价值多少？",
      "回收估价是怎么算的？"
    ]
  },
  "answer": {
    "standard": "回收价格根据设备型号、配置、使用年限和外观成色综合评估。您可以在APP首页选择对应机型并填写真实信息获得初步估价，最终价格将在设备检测后确定。",
    "keywords": ["价格", "估价", "评估", "机型", "检测"]
  },
  "related_faqs": ["FAQ_002", "FAQ_010"],
  "update_time": "2025-04-15"
}
```

#### 估价准确性
```json
{
  "id": "FAQ_002",
  "category": "产品咨询类/产品价格",
  "question": {
    "standard": "预估价与实际回收价格会相差多少？",
    "variants": [
      "估价和实际价格一样吗？",
      "为什么最终价格和预估不一样？",
      "预估价准确吗？"
    ]
  },
  "answer": {
    "standard": "预估价是根据您提供的信息初步评估的参考价格，最终回收价格将由专业质检师根据实际收到的设备状况确定。为确保预估准确，请在填写信息时如实描述设备情况。一般情况下，如填写信息与实际相符，价格差异会在10%以内。",
    "keywords": ["预估价", "实际价格", "差异", "质检", "准确"]
  },
  "related_faqs": ["FAQ_001", "FAQ_003"],
  "update_time": "2025-04-15"
}
```

### 1.2 服务支持类

#### 运费问题
```json
{
  "id": "FAQ_010",
  "category": "服务支持类/物流问题",
  "question": {
    "standard": "设备寄出的运费谁来承担？",
    "variants": [
      "邮费谁付？",
      "寄快递要自己出钱吗？",
      "回收的运费怎么算？"
    ]
  },
  "answer": {
    "standard": "极速回收寄出运费一般由服务商承担，顺丰免费上门取件。部分品类特殊说明如下：1. 家电、大件、乐器等会由服务商安排免费上门拆卸或评测；2. 黄金品类≥20g，免运费及保价费。\n\n温馨提示：1. 如已自行垫付运费，可联系客服报销（至高25元）；2. 因包装和保价等产生的额外费用，需自行承担；3. 因寄送假货/高仿、寄错商品、设备无法解锁等违约行为而产生的运费，需自行承担。",
    "keywords": ["运费", "邮费", "顺丰", "上门", "报销"]
  },
  "related_faqs": ["FAQ_011", "FAQ_012"],
  "update_time": "2025-04-15"
}
```

#### 退回流程
```json
{
  "id": "FAQ_015",
  "category": "服务支持类/退款问题",
  "question": {
    "standard": "如何申请退回设备？",
    "variants": [
      "不满意价格怎么退回？",
      "检测不满意想退回",
      "不想卖了怎么退？"
    ]
  },
  "answer": {
    "standard": "如对检测结果或回收价格不满意，可申请退回设备。操作流程：1. 联系在线客服说明退回需求；2. 提供订单号及退回原因；3. 客服确认后会为您安排退回；4. 设备将通过顺丰寄回您的收货地址；5. 退回过程一般需要3-5个工作日完成。退回运费由回收宝承担，无需您支付额外费用。",
    "keywords": ["退回", "不满意", "申请", "顺丰", "运费"]
  },
  "related_faqs": ["FAQ_010", "FAQ_016"],
  "update_time": "2025-04-15"
}
```

### 1.3 技术问题类

#### 设备检测
```json
{
  "id": "FAQ_020",
  "category": "技术问题类/操作指导",
  "question": {
    "standard": "设备检测需要多长时间？",
    "variants": [
      "什么时候能完成质检？",
      "检测要多久？",
      "几天能出结果？"
    ]
  },
  "answer": {
    "standard": "我们承诺在收到设备后的48小时内完成质检。实际检测时间取决于设备类型和当前检测工作量，一般情况下手机和平板会在24小时内完成，电脑和其他设备可能需要24-48小时。质检完成后，系统会自动发送短信通知您检测结果和回收价格。",
    "keywords": ["检测", "质检", "时间", "48小时", "通知"]
  },
  "related_faqs": ["FAQ_021", "FAQ_022"],
  "update_time": "2025-04-15"
}
```

## 2. 解决方案示例

### 2.1 设备退回解决方案
```json
{
  "id": "SOL_001",
  "category": "服务支持类/退款问题",
  "issue": "用户申请退回设备",
  "solution_flow": [
    {
      "step": 1,
      "action": "确认订单信息",
      "details": "查询用户订单号，确认当前订单状态"
    },
    {
      "step": 2,
      "action": "核实退回原因",
      "details": "了解用户退回设备的具体原因，如价格不满意、检测结果异议等"
    },
    {
      "step": 3,
      "action": "说明退回流程",
      "details": "向用户说明设备退回流程、预计时间和物流方式"
    },
    {
      "step": 4,
      "action": "记录退回请求",
      "details": "在系统中记录退回请求，生成退回工单"
    },
    {
      "step": 5,
      "action": "安排退回物流",
      "details": "向用户确认收件信息，安排物流退回"
    }
  ],
  "templates": ["TEMP_005", "TEMP_008", "TEMP_012"],
  "tips": "如用户强烈不满，应主动提出适当补偿或转接专员处理",
  "update_time": "2025-04-15"
}
```

### 2.2 订单查询解决方案
```json
{
  "id": "SOL_002",
  "category": "服务支持类/订单问题",
  "issue": "用户查询订单状态",
  "solution_flow": [
    {
      "step": 1,
      "action": "获取订单信息",
      "details": "请用户提供订单号或下单手机号"
    },
    {
      "step": 2,
      "action": "查询订单状态",
      "details": "在系统中查询并确认当前订单状态"
    },
    {
      "step": 3,
      "action": "告知订单进度",
      "details": "向用户详细说明当前订单进度和后续流程"
    },
    {
      "step": 4,
      "action": "解答相关疑问",
      "details": "回答用户关于订单的其他疑问"
    },
    {
      "step": 5,
      "action": "提供跟进服务",
      "details": "告知用户如有后续问题如何联系以及何时会收到下一步通知"
    }
  ],
  "templates": ["TEMP_002", "TEMP_007", "TEMP_013"],
  "tips": "查询订单时一定要核实用户身份，确保信息安全",
  "update_time": "2025-04-15"
}
```

## 3. 回复模板示例

### 3.1 首次回复模板
```json
{
  "id": "TEMP_001",
  "category": "通用/开场白",
  "scenario": "首次回复",
  "content": "亲，您已经进入人工服务，我是回收宝小宝客服！为了帮助您尽快解答，请您提供订单编号或者下单手机号，快速为您解决问题哦。",
  "variables": [],
  "usage_tips": "用于客户首次咨询时的标准开场白",
  "update_time": "2025-04-15"
}
```

### 3.2 查询等待模板
```json
{
  "id": "TEMP_002",
  "category": "服务支持/查询",
  "scenario": "订单查询等待",
  "content": "好的呢，马上为您查询订单，请您稍等1-2分钟",
  "variables": [],
  "usage_tips": "用于告知用户正在查询订单信息，设置合理期望",
  "update_time": "2025-04-15"
}
```

### 3.3 满意度收集模板
```json
{
  "id": "TEMP_003",
  "category": "通用/结束语",
  "scenario": "服务结束满意度收集",
  "content": "亲，可以请您帮忙动一下您的发财手，帮我在服务评价点一下【很满意】吗，您的评价对我非常重要，先在此谢谢您！",
  "variables": [],
  "usage_tips": "在问题解决后使用，请求用户进行服务评价",
  "update_time": "2025-04-15"
}
```

### 3.4 运费说明模板
```json
{
  "id": "TEMP_004",
  "category": "服务支持/物流",
  "scenario": "运费政策说明",
  "content": "我们承担您下单后寄出设备的运费，您使用顺丰到付即可，对于手机、平板等小件设备，我们承担的运费上限为25元，对于电脑和显示屏，上限为40元，不含包装费和保价费等额外服务费用[ww:抱抱]",
  "variables": [],
  "usage_tips": "用于解答客户关于运费政策的咨询",
  "update_time": "2025-04-15"
}
```

### 3.5 退回道歉模板
```json
{
  "id": "TEMP_005",
  "category": "服务支持/退回",
  "scenario": "设备退回道歉",
  "content": "实在抱歉给到不好体验，已经反馈退回了，顺丰会在1-2个工作日内联系您安排取件，请保持手机畅通。",
  "variables": [],
  "usage_tips": "用于处理客户对检测结果不满意要求退回的情况",
  "update_time": "2025-04-15"
}
```

## 4. 多轮对话流程示例

### 4.1 订单查询流程
```json
{
  "id": "FLOW_001",
  "name": "订单查询流程",
  "category": "服务支持/订单查询",
  "trigger": ["查询订单", "订单状态", "查订单"],
  "nodes": [
    {
      "id": "node_001",
      "type": "ask",
      "message": "请问您的订单号是多少呢？如果没有订单号，也可以提供下单手机号码。",
      "expected_entity": "order_id|phone_number",
      "next": {
        "default": "node_002",
        "no_info": "node_001_retry"
      }
    },
    {
      "id": "node_001_retry",
      "type": "ask",
      "message": "抱歉，我没有获取到您的订单信息，请您提供订单号或下单时使用的手机号码，方便我为您查询。",
      "expected_entity": "order_id|phone_number",
      "next": {
        "default": "node_002",
        "no_info": "node_transfer"
      }
    },
    {
      "id": "node_002",
      "type": "system",
      "action": "query_order",
      "parameters": {
        "id_type": "${entity_type}",
        "id_value": "${entity_value}"
      },
      "next": {
        "success": "node_003",
        "not_found": "node_004",
        "error": "node_transfer"
      }
    },
    {
      "id": "node_003",
      "type": "tell",
      "message": "已经为您查询到订单信息，您的订单当前状态为${order_status}。${status_description}",
      "next": {
        "default": "node_005"
      }
    },
    {
      "id": "node_004",
      "type": "tell",
      "message": "抱歉，未能查询到您提供的订单信息，请确认订单号或手机号是否正确。",
      "next": {
        "default": "node_001_retry"
      }
    },
    {
      "id": "node_005",
      "type": "ask",
      "message": "请问您还有其他关于订单的问题吗？",
      "expected_entity": "yes_no|question",
      "next": {
        "yes": "node_006",
        "no": "node_end",
        "question": "node_006",
        "default": "node_end"
      }
    },
    {
      "id": "node_006",
      "type": "system",
      "action": "analyze_question",
      "next": {
        "order_related": "node_007",
        "other": "node_transfer"
      }
    },
    {
      "id": "node_007",
      "type": "ask",
      "message": "关于您的问题"${user_question}"，${answer}。请问还有其他疑问吗？",
      "expected_entity": "yes_no",
      "next": {
        "yes": "node_006",
        "no": "node_end",
        "default": "node_end"
      }
    },
    {
      "id": "node_transfer",
      "type": "transfer",
      "message": "您的问题可能需要专业客服进一步处理，正在为您转接人工客服，请稍候...",
      "next": {
        "default": "node_end"
      }
    },
    {
      "id": "node_end",
      "type": "tell",
      "message": "感谢您的咨询，如果后续有任何问题，随时可以联系我们。祝您生活愉快！",
      "next": null
    }
  ],
  "update_time": "2025-04-15"
}
```

### 4.2 退回申请流程
```json
{
  "id": "FLOW_002",
  "name": "设备退回申请流程",
  "category": "服务支持/退回申请",
  "trigger": ["退回设备", "不满意", "不想卖了", "退货"],
  "nodes": [
    {
      "id": "node_001",
      "type": "ask",
      "message": "您好，请问您需要申请退回设备吗？可以提供一下您的订单号吗？",
      "expected_entity": "order_id",
      "next": {
        "default": "node_002",
        "no_info": "node_001_retry"
      }
    },
    {
      "id": "node_001_retry",
      "type": "ask",
      "message": "为了帮您处理退回申请，需要您提供订单号。如果您不知道订单号，也可以提供下单手机号。",
      "expected_entity": "order_id|phone_number",
      "next": {
        "default": "node_002",
        "no_info": "node_transfer"
      }
    },
    {
      "id": "node_002",
      "type": "system",
      "action": "query_order",
      "parameters": {
        "id_type": "${entity_type}",
        "id_value": "${entity_value}"
      },
      "next": {
        "success": "node_003",
        "not_found": "node_004",
        "error": "node_transfer"
      }
    },
    {
      "id": "node_003",
      "type": "ask",
      "message": "已查询到您的订单，当前状态为${order_status}。请问您申请退回的原因是什么呢？",
      "expected_entity": "return_reason",
      "next": {
        "default": "node_005"
      }
    },
    {
      "id": "node_004",
      "type": "tell",
      "message": "抱歉，未能查询到您提供的订单信息，请确认订单号或手机号是否正确。",
      "next": {
        "default": "node_001_retry"
      }
    },
    {
      "id": "node_005",
      "type": "system",
      "action": "check_return_eligibility",
      "parameters": {
        "order_id": "${order_id}",
        "reason": "${return_reason}"
      },
      "next": {
        "eligible": "node_006",
        "not_eligible": "node_007",
        "need_review": "node_transfer"
      }
    },
    {
      "id": "node_006",
      "type": "ask",
      "message": "您的订单符合退回条件。退回后，设备将通过顺丰寄回您的收货地址，运费由我们承担。请确认您的收货地址是：${shipping_address}，是否正确？",
      "expected_entity": "yes_no",
      "next": {
        "yes": "node_008",
        "no": "node_009",
        "default": "node_008"
      }
    },
    {
      "id": "node_007",
      "type": "tell",
      "message": "抱歉，您的订单当前状态为${order_status}，根据我们的政策，此状态下不支持直接申请退回。建议您联系人工客服进一步处理。",
      "next": {
        "default": "node_transfer"
      }
    },
    {
      "id": "node_008",
      "type": "system",
      "action": "create_return_request",
      "parameters": {
        "order_id": "${order_id}",
        "reason": "${return_reason}",
        "address": "${shipping_address}"
      },
      "next": {
        "success": "node_010",
        "error": "node_transfer"
      }
    },
    {
      "id": "node_009",
      "type": "ask",
      "message": "请提供您的正确收货地址，包括省市区、详细街道地址、收件人姓名和联系电话。",
      "expected_entity": "address",
      "next": {
        "default": "node_011"
      }
    },
    {
      "id": "node_010",
      "type": "tell",
      "message": "您的退回申请已成功提交，退回单号为${return_id}。顺丰快递会在1-2个工作日内联系您安排取件，请保持手机畅通。退回过程一般需要3-5个工作日完成。",
      "next": {
        "default": "node_012"
      }
    },
    {
      "id": "node_011",
      "type": "system",
      "action": "update_shipping_address",
      "parameters": {
        "order_id": "${order_id}",
        "new_address": "${address}"
      },
      "next": {
        "success": "node_008",
        "error": "node_transfer"
      }
    },
    {
      "id": "node_012",
      "type": "ask",
      "message": "关于退回流程，您还有其他问题吗？",
      "expected_entity": "yes_no|question",
      "next": {
        "yes": "node_013",
        "no": "node_end",
        "question": "node_013",
        "default": "node_end"
      }
    },
    {
      "id": "node_013",
      "type": "system",
      "action": "analyze_question",
      "next": {
        "return_related": "node_014",
        "other": "node_transfer"
      }
    },
    {
      "id": "node_014",
      "type": "tell",
      "message": "关于您的问题"${user_question}"，${answer}。",
      "next": {
        "default": "node_012"
      }
    },
    {
      "id": "node_transfer",
      "type": "transfer",
      "message": "您的问题可能需要专业客服进一步处理，正在为您转接人工客服，请稍候...",
      "next": {
        "default": "node_end"
      }
    },
    {
      "id": "node_end",
      "type": "tell",
      "message": "感谢您的咨询，如果后续有任何问题，随时可以联系我们。祝您生活愉快！",
      "next": null
    }
  ],
  "update_time": "2025-04-15"
}
``` 
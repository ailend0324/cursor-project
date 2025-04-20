# 数据清洗报告

生成时间: 2025-04-20 20:46:43

原始文件: /Users/boxie/Downloads/windsurf/一步步来/sample_5000.xlsx

输出文件: /Users/boxie/Downloads/windsurf/一步步来/sample_5000_cleaned_step1.xlsx

## 原始数据状态

### 原始数据形状（行数，列数）：
(5000, 12)

### 原始数据前五行：
```
         touch_id       user_name      user_start_time        user_end_time servicer_name new_feedback_name          create_time   group_name            send_time  sender_type                                    send_content  seq_no
0  10167147480827  xy492181393082  2025-03-30 09:00:42  2025-03-30 09:11:28        随风而走的莎               NaN  2025-03-30 09:00:42  上门&到店回收-回收宝  2025-03-30 09:05:52          2.0                               好的亲，辛苦提供一下退回的地址信息     9.0
1  10167147480827  xy492181393082  2025-03-30 09:00:42  2025-03-30 09:11:28        随风而走的莎               NaN  2025-03-30 09:00:42  上门&到店回收-回收宝  2025-03-30 09:00:50          1.0                                          反悔了不卖了     1.0
2  10167147480827  xy492181393082  2025-03-30 09:00:42  2025-03-30 09:11:28        随风而走的莎               NaN  2025-03-30 09:00:42  上门&到店回收-回收宝  2025-03-30 09:09:16          2.0                您可以查看一下顺丰小程序当时邮寄过来是多少的哈，应该不会差很多的    19.0
3  10167147480827  xy492181393082  2025-03-30 09:00:42  2025-03-30 09:11:28        随风而走的莎               NaN  2025-03-30 09:00:42  上门&到店回收-回收宝  2025-03-30 09:07:19          2.0  亲亲，很荣幸为您服务~辛苦您稍后给我一个很满意的好评，这对夏目很重要，十分感谢[ww:飞吻]    12.0
4  10167147480827  xy492181393082  2025-03-30 09:00:42  2025-03-30 09:11:28        随风而走的莎               NaN  2025-03-30 09:00:42  上门&到店回收-回收宝  2025-03-30 09:06:40          2.0       好的亲亲，核实后会安排机器退回，到时候会有短信告知物流单号，是到付退回的哈，请知悉    11.0
```

### 原始数据信息：
```
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 5000 entries, 0 to 4999
Data columns (total 12 columns):
 #   Column             Non-Null Count  Dtype  
---  ------             --------------  -----  
 0   touch_id           5000 non-null   int64  
 1   user_name          5000 non-null   object 
 2   user_start_time    5000 non-null   object 
 3   user_end_time      5000 non-null   object 
 4   servicer_name      4992 non-null   object 
 5   new_feedback_name  1365 non-null   object 
 6   create_time        5000 non-null   object 
 7   group_name         5000 non-null   object 
 8   send_time          4970 non-null   object 
 9   sender_type        4970 non-null   float64
 10  send_content       4970 non-null   object 
 11  seq_no             4970 non-null   float64
dtypes: float64(2), int64(1), object(9)
memory usage: 468.9+ KB

```

### 原始数据缺失值统计：
```
touch_id                0
user_name               0
user_start_time         0
user_end_time           0
servicer_name           8
new_feedback_name    3635
create_time             0
group_name              0
send_time              30
sender_type            30
send_content           30
seq_no                 30
```

### 原始数据重复 touch_id 数量：
4681

## 数据清洗过程

以下是对数据进行的清洗步骤和变化

1. 删除 send_content 缺失的行
   - 删除前行数: 5000
   - 删除后行数: 4970
   - 删除的行数: 30

2. 填充 servicer_name 的缺失值
   - 填充的单元格数: 3
   - 填充值: '未知客服'

3. 填充 new_feedback_name 的缺失值
   - 填充的单元格数: 3605
   - 填充值: '无反馈'

4. 填充 group_name 的缺失值
   - 填充的单元格数: 0
   - 填充值: '未知分组'

## 清洗后数据状态

### 清洗后数据形状（行数，列数）：
(4970, 12)

### 清洗后数据前五行：
```
         touch_id       user_name      user_start_time        user_end_time servicer_name new_feedback_name          create_time   group_name            send_time  sender_type                                    send_content  seq_no
0  10167147480827  xy492181393082  2025-03-30 09:00:42  2025-03-30 09:11:28        随风而走的莎               无反馈  2025-03-30 09:00:42  上门&到店回收-回收宝  2025-03-30 09:05:52          2.0                               好的亲，辛苦提供一下退回的地址信息     9.0
1  10167147480827  xy492181393082  2025-03-30 09:00:42  2025-03-30 09:11:28        随风而走的莎               无反馈  2025-03-30 09:00:42  上门&到店回收-回收宝  2025-03-30 09:00:50          1.0                                          反悔了不卖了     1.0
2  10167147480827  xy492181393082  2025-03-30 09:00:42  2025-03-30 09:11:28        随风而走的莎               无反馈  2025-03-30 09:00:42  上门&到店回收-回收宝  2025-03-30 09:09:16          2.0                您可以查看一下顺丰小程序当时邮寄过来是多少的哈，应该不会差很多的    19.0
3  10167147480827  xy492181393082  2025-03-30 09:00:42  2025-03-30 09:11:28        随风而走的莎               无反馈  2025-03-30 09:00:42  上门&到店回收-回收宝  2025-03-30 09:07:19          2.0  亲亲，很荣幸为您服务~辛苦您稍后给我一个很满意的好评，这对夏目很重要，十分感谢[ww:飞吻]    12.0
4  10167147480827  xy492181393082  2025-03-30 09:00:42  2025-03-30 09:11:28        随风而走的莎               无反馈  2025-03-30 09:00:42  上门&到店回收-回收宝  2025-03-30 09:06:40          2.0       好的亲亲，核实后会安排机器退回，到时候会有短信告知物流单号，是到付退回的哈，请知悉    11.0
```

### 清洗后数据信息：
```
<class 'pandas.core.frame.DataFrame'>
Index: 4970 entries, 0 to 4999
Data columns (total 12 columns):
 #   Column             Non-Null Count  Dtype  
---  ------             --------------  -----  
 0   touch_id           4970 non-null   int64  
 1   user_name          4970 non-null   object 
 2   user_start_time    4970 non-null   object 
 3   user_end_time      4970 non-null   object 
 4   servicer_name      4970 non-null   object 
 5   new_feedback_name  4970 non-null   object 
 6   create_time        4970 non-null   object 
 7   group_name         4970 non-null   object 
 8   send_time          4970 non-null   object 
 9   sender_type        4970 non-null   float64
 10  send_content       4970 non-null   object 
 11  seq_no             4970 non-null   float64
dtypes: float64(2), int64(1), object(9)
memory usage: 504.8+ KB

```

### 清洗后数据缺失值统计：
```
touch_id             0
user_name            0
user_start_time      0
user_end_time        0
servicer_name        0
new_feedback_name    0
create_time          0
group_name           0
send_time            0
sender_type          0
send_content         0
seq_no               0
```

### 清洗后数据重复 touch_id 数量：
4681

## 数据变化摘要

以下是数据清洗前后的主要变化

1. 行数变化: 5000 → 4970 (减少了 30 行)

2. 填充的缺失值总数: 3608 个单元格

3. 处理后的数据已保存到: /Users/boxie/Downloads/windsurf/一步步来/sample_5000_cleaned_step1.xlsx


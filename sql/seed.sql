-- TS_ERP 种子数据

USE ts_erp;

-- ==================== 初始化权限数据 ====================

-- 权限数据
INSERT INTO `permissions` (`code`, `name`, `resource_type`, `action`) VALUES
-- 客户权限
('customer:view', '查看客户', 'customer', 'view'),
('customer:create', '创建客户', 'customer', 'create'),
('customer:update', '更新客户', 'customer', 'update'),
('customer:delete', '删除客户', 'customer', 'delete'),
-- 订单权限
('order:view', '查看订单', 'order', 'view'),
('order:create', '创建订单', 'order', 'create'),
('order:update', '更新订单', 'order', 'update'),
('order:delete', '删除订单', 'order', 'delete'),
-- 库存权限
('inventory:view', '查看库存', 'inventory', 'view'),
('inventory:manage', '管理库存', 'inventory', 'manage'),
-- 财务权限
('finance:view', '查看财务', 'finance', 'view'),
('finance:manage', '管理财务', 'finance', 'manage'),
-- 智能客服权限
('agent:chat', '使用智能客服', 'agent', 'chat'),
('agent:debug', '调试智能客服', 'agent', 'debug'),
-- 知识库权限
('knowledge:view', '查看知识库', 'knowledge', 'view'),
('knowledge:manage', '管理知识库', 'knowledge', 'manage');

-- 角色数据
INSERT INTO `roles` (`name`, `description`, `is_system`) VALUES
('超级管理员', '系统超级管理员，拥有所有权限', 1),
('管理员', '系统管理员，拥有大部分权限', 1),
('销售经理', '负责客户和订单管理', 0),
('仓库管理员', '负责库存管理', 0),
('财务人员', '负责财务记录', 0),
('普通员工', '基础查看权限', 0);

-- 角色权限关联
-- 超级管理员拥有所有权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 1, `id` FROM `permissions`;

-- 管理员拥有大部分权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 2, `id` FROM `permissions` WHERE `code` NOT LIKE 'agent:debug';

-- 销售经理权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 3, `id` FROM `permissions` WHERE `code` IN (
    'customer:view', 'customer:create', 'customer:update',
    'order:view', 'order:create', 'order:update',
    'inventory:view',
    'finance:view',
    'agent:chat'
);

-- 仓库管理员权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 4, `id` FROM `permissions` WHERE `code` IN (
    'inventory:view', 'inventory:manage',
    'customer:view',
    'agent:chat'
);

-- 财务人员权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 5, `id` FROM `permissions` WHERE `code` IN (
    'finance:view', 'finance:manage',
    'customer:view',
    'order:view',
    'agent:chat'
);

-- 普通员工权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 6, `id` FROM `permissions` WHERE `code` IN (
    'customer:view',
    'order:view',
    'inventory:view',
    'finance:view',
    'agent:chat'
);

-- ==================== 初始化部门数据 ====================

INSERT INTO `departments` (`name`, `parent_id`, `level`) VALUES
('总公司', NULL, 1),
('销售部', 1, 2),
('仓库部', 1, 2),
('财务部', 1, 2),
('人事部', 1, 2);

-- ==================== 初始化用户数据 ====================

-- 密码都是 admin123 (bcrypt hash)
INSERT INTO `users` (`username`, `email`, `hashed_password`, `full_name`, `department_id`) VALUES
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYL0L0L0L0.', '系统管理员', 1),
('sales_manager', 'sales@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYL0L0L0L0.', '销售经理', 2),
('warehouse_manager', 'warehouse@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYL0L0L0L0.', '仓库管理员', 3),
('finance', 'finance@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYL0L0L0L0.', '财务人员', 4),
('staff', 'staff@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYL0L0L0L0.', '普通员工', 2);

-- 用户角色关联
INSERT INTO `user_roles` (`user_id`, `role_id`) VALUES
(1, 1),  -- admin -> 超级管理员
(2, 3),  -- sales_manager -> 销售经理
(3, 4),  -- warehouse_manager -> 仓库管理员
(4, 5),  -- finance -> 财务人员
(5, 6);  -- staff -> 普通员工

-- ==================== 初始化业务数据 ====================

-- 产品数据
INSERT INTO `products` (`name`, `sku`, `price`, `unit`, `category`) VALUES
('笔记本电脑', 'PROD001', 5999.00, '台', '电子产品'),
('无线鼠标', 'PROD002', 89.00, '个', '配件'),
('机械键盘', 'PROD003', 399.00, '个', '配件'),
('显示器', 'PROD004', 1599.00, '台', '电子产品'),
('耳机', 'PROD005', 299.00, '副', '配件'),
('U盘 64GB', 'PROD006', 49.00, '个', '存储'),
('移动硬盘 1TB', 'PROD007', 399.00, '个', '存储'),
('路由器', 'PROD008', 199.00, '个', '网络');

-- 仓库数据
INSERT INTO `warehouses` (`name`, `address`, `manager`) VALUES
('北京总仓', '北京市朝阳区xxx路1号', '张三'),
('上海分仓', '上海市浦东新区xxx路2号', '李四'),
('广州分仓', '广州市天河区xxx路3号', '王五');

-- 客户数据
INSERT INTO `customers` (`name`, `contact`, `phone`, `email`, `level`, `address`, `department_id`) VALUES
('北京科技有限公司', '张经理', '13800138001', 'bj@example.com', 'svip', '北京市海淀区', 2),
('上海实业集团', '李总', '13800138002', 'sh@example.com', 'vip', '上海市浦东新区', 2),
('广州贸易公司', '王经理', '13800138003', 'gz@example.com', 'normal', '广州市天河区', 2),
('深圳电子科技', '刘总', '13800138004', 'sz@example.com', 'vip', '深圳市南山区', 2),
('杭州网络科技', '陈经理', '13800138005', 'hz@example.com', 'normal', '杭州市西湖区', 2);

-- 库存数据
INSERT INTO `inventory` (`product_id`, `warehouse_id`, `quantity`, `min_stock_level`) VALUES
(1, 1, 50, 10),
(2, 1, 200, 50),
(3, 1, 80, 20),
(4, 1, 30, 5),
(5, 1, 150, 30),
(6, 1, 500, 100),
(7, 1, 60, 15),
(8, 1, 100, 20),
(1, 2, 20, 5),
(2, 2, 100, 30),
(3, 2, 40, 10),
(5, 2, 80, 20),
(6, 2, 200, 50);

-- 订单数据
INSERT INTO `orders` (`order_no`, `customer_id`, `amount`, `status`, `payment_method`, `created_by`) VALUES
('ORD202401001', 1, 12598.00, 'completed', 'bank_transfer', 2),
('ORD202401002', 2, 5999.00, 'paid', 'alipay', 2),
('ORD202401003', 3, 1197.00, 'shipped', 'wechat', 2),
('ORD202401004', 4, 25997.00, 'pending', 'bank_transfer', 2),
('ORD202401005', 5, 299.00, 'pending', 'wechat', 5),
('ORD202401006', 1, 7998.00, 'completed', 'alipay', 2);

-- 财务记录数据
INSERT INTO `finance_records` (`customer_id`, `type`, `amount`, `record_date`, `order_id`, `payment_method`, `created_by`) VALUES
(1, 'receipt', 12598.00, '2024-01-15', 1, 'bank_transfer', 4),
(2, 'receipt', 5999.00, '2024-01-16', 2, 'alipay', 4),
(4, 'receipt', 25997.00, '2024-01-17', 4, 'bank_transfer', 4),
(3, 'receipt', 1197.00, '2024-01-18', 3, 'wechat', 4);

-- 知识库数据
INSERT INTO `knowledge_bases` (`name`, `description`, `module`, `created_by`) VALUES
('公司制度', '公司内部规章制度', 'general', 1),
('销售流程', '销售相关流程文档', 'order', 1),
('库存管理', '库存管理制度', 'inventory', 1),
('财务管理', '财务管理制度', 'finance', 1);

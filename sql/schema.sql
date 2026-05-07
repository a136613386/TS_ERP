-- TS_ERP 数据库初始化脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS ts_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ts_erp;

-- ==================== 用户与权限相关表 ====================

-- 用户表
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    `email` VARCHAR(100) UNIQUE COMMENT '邮箱',
    `hashed_password` VARCHAR(255) NOT NULL COMMENT '密码哈希',
    `full_name` VARCHAR(100) COMMENT '姓名',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否激活',
    `is_superuser` TINYINT(1) DEFAULT 0 COMMENT '是否超级管理员',
    `department_id` INT COMMENT '部门ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_username` (`username`),
    INDEX `idx_department` (`department_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 角色表
CREATE TABLE IF NOT EXISTS `roles` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '角色ID',
    `name` VARCHAR(50) NOT NULL UNIQUE COMMENT '角色名称',
    `description` VARCHAR(200) COMMENT '角色描述',
    `is_system` TINYINT(1) DEFAULT 0 COMMENT '是否系统内置',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS `user_roles` (
    `user_id` INT NOT NULL,
    `role_id` INT NOT NULL,
    PRIMARY KEY (`user_id`, `role_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';

-- 权限表
CREATE TABLE IF NOT EXISTS `permissions` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID',
    `code` VARCHAR(100) NOT NULL UNIQUE COMMENT '权限代码',
    `name` VARCHAR(100) NOT NULL COMMENT '权限名称',
    `resource_type` VARCHAR(50) COMMENT '资源类型',
    `action` VARCHAR(50) COMMENT '操作类型',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限表';

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS `role_permissions` (
    `role_id` INT NOT NULL,
    `permission_id` INT NOT NULL,
    PRIMARY KEY (`role_id`, `permission_id`),
    FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`permission_id`) REFERENCES `permissions`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限关联表';

-- 部门表
CREATE TABLE IF NOT EXISTS `departments` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '部门ID',
    `name` VARCHAR(100) NOT NULL COMMENT '部门名称',
    `parent_id` INT COMMENT '父部门ID',
    `level` INT DEFAULT 1 COMMENT '层级',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`parent_id`) REFERENCES `departments`(`id`) ON DELETE SET NULL,
    INDEX `idx_parent` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='部门表';

-- ==================== 业务相关表 ====================

-- 客户表
CREATE TABLE IF NOT EXISTS `customers` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '客户ID',
    `name` VARCHAR(100) NOT NULL COMMENT '客户名称',
    `contact` VARCHAR(50) COMMENT '联系人',
    `phone` VARCHAR(20) COMMENT '联系电话',
    `email` VARCHAR(100) COMMENT '邮箱',
    `level` VARCHAR(20) DEFAULT 'normal' COMMENT '客户等级: normal/vip/svip',
    `address` TEXT COMMENT '地址',
    `department_id` INT COMMENT '负责部门',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否有效',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_name` (`name`),
    INDEX `idx_department` (`department_id`),
    INDEX `idx_level` (`level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户表';

-- 产品表
CREATE TABLE IF NOT EXISTS `products` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '产品ID',
    `name` VARCHAR(100) NOT NULL COMMENT '产品名称',
    `sku` VARCHAR(50) UNIQUE COMMENT '产品编码',
    `price` DECIMAL(10, 2) COMMENT '单价',
    `unit` VARCHAR(20) DEFAULT '件' COMMENT '单位',
    `category` VARCHAR(50) COMMENT '分类',
    `is_active` TINYINT(1) DEFAULT 1,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_sku` (`sku`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='产品表';

-- 仓库表
CREATE TABLE IF NOT EXISTS `warehouses` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '仓库ID',
    `name` VARCHAR(100) NOT NULL COMMENT '仓库名称',
    `address` TEXT COMMENT '地址',
    `manager` VARCHAR(50) COMMENT '管理员',
    `is_active` TINYINT(1) DEFAULT 1,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='仓库表';

-- 订单表
CREATE TABLE IF NOT EXISTS `orders` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '订单ID',
    `order_no` VARCHAR(50) UNIQUE NOT NULL COMMENT '订单号',
    `customer_id` INT NOT NULL COMMENT '客户ID',
    `amount` DECIMAL(12, 2) NOT NULL COMMENT '订单金额',
    `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/paid/shipped/completed/cancelled',
    `payment_method` VARCHAR(20) COMMENT '支付方式',
    `remark` TEXT COMMENT '备注',
    `created_by` INT COMMENT '创建人',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`),
    FOREIGN KEY (`created_by`) REFERENCES `users`(`id`),
    INDEX `idx_order_no` (`order_no`),
    INDEX `idx_customer` (`customer_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- 订单明细表
CREATE TABLE IF NOT EXISTS `order_items` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '明细ID',
    `order_id` INT NOT NULL COMMENT '订单ID',
    `product_id` INT NOT NULL COMMENT '产品ID',
    `quantity` INT NOT NULL COMMENT '数量',
    `unit_price` DECIMAL(10, 2) NOT NULL COMMENT '单价',
    `subtotal` DECIMAL(12, 2) NOT NULL COMMENT '小计',
    FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`product_id`) REFERENCES `products`(`id`),
    INDEX `idx_order` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单明细表';

-- 库存表
CREATE TABLE IF NOT EXISTS `inventory` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '库存ID',
    `product_id` INT NOT NULL COMMENT '产品ID',
    `warehouse_id` INT NOT NULL COMMENT '仓库ID',
    `quantity` INT DEFAULT 0 COMMENT '库存数量',
    `min_stock_level` INT DEFAULT 10 COMMENT '最小库存预警',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`product_id`) REFERENCES `products`(`id`),
    FOREIGN KEY (`warehouse_id`) REFERENCES `warehouses`(`id`),
    UNIQUE KEY `uk_product_warehouse` (`product_id`, `warehouse_id`),
    INDEX `idx_warehouse` (`warehouse_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存表';

-- 财务记录表
CREATE TABLE IF NOT EXISTS `finance_records` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
    `customer_id` INT COMMENT '客户ID',
    `type` VARCHAR(20) NOT NULL COMMENT '类型: receipt/payment',
    `amount` DECIMAL(12, 2) NOT NULL COMMENT '金额',
    `record_date` DATE NOT NULL COMMENT '记录日期',
    `order_id` INT COMMENT '关联订单',
    `payment_method` VARCHAR(20) COMMENT '支付方式',
    `remark` TEXT COMMENT '备注',
    `created_by` INT COMMENT '创建人',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`),
    FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`),
    FOREIGN KEY (`created_by`) REFERENCES `users`(`id`),
    INDEX `idx_customer` (`customer_id`),
    INDEX `idx_type` (`type`),
    INDEX `idx_record_date` (`record_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务记录表';

-- ==================== 知识库相关表 ====================

-- 知识库表
CREATE TABLE IF NOT EXISTS `knowledge_bases` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '知识库ID',
    `name` VARCHAR(100) NOT NULL COMMENT '知识库名称',
    `description` TEXT COMMENT '描述',
    `module` VARCHAR(50) DEFAULT 'general' COMMENT '所属模块',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `created_by` INT COMMENT '创建人',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_module` (`module`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库表';

-- 文档表
CREATE TABLE IF NOT EXISTS `knowledge_documents` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '文档ID',
    `base_id` INT NOT NULL COMMENT '知识库ID',
    `title` VARCHAR(200) NOT NULL COMMENT '文档标题',
    `file_path` VARCHAR(500) COMMENT '文件路径',
    `file_type` VARCHAR(50) COMMENT '文件类型',
    `file_hash` VARCHAR(64) COMMENT '文件哈希',
    `file_size` BIGINT COMMENT '文件大小',
    `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/processing/completed/failed',
    `uploaded_by` INT COMMENT '上传人',
    `uploaded_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `indexed_at` DATETIME COMMENT '索引完成时间',
    FOREIGN KEY (`base_id`) REFERENCES `knowledge_bases`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`uploaded_by`) REFERENCES `users`(`id`),
    INDEX `idx_base` (`base_id`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档表';

-- Chunk 表
CREATE TABLE IF NOT EXISTS `knowledge_chunks` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '块ID',
    `document_id` INT NOT NULL COMMENT '文档ID',
    `chunk_index` INT COMMENT '块序号',
    `content` TEXT COMMENT '内容',
    `summary` VARCHAR(500) COMMENT '摘要',
    `es_doc_id` VARCHAR(100) COMMENT 'ES文档ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`document_id`) REFERENCES `knowledge_documents`(`id`) ON DELETE CASCADE,
    INDEX `idx_document` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识块表';

-- 知识权限表
CREATE TABLE IF NOT EXISTS `knowledge_permissions` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `base_id` INT COMMENT '知识库ID',
    `document_id` INT COMMENT '文档ID',
    `permission_scope` VARCHAR(50) NOT NULL COMMENT '权限范围: public/dept_xxx/user_xxx',
    `permission_type` VARCHAR(20) NOT NULL COMMENT '权限类型: role/department/user',
    `permission_value` VARCHAR(100) COMMENT '权限值',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`base_id`) REFERENCES `knowledge_bases`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`document_id`) REFERENCES `knowledge_documents`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识权限表';

-- ==================== 日志相关表 ====================

-- SQL审计日志表
CREATE TABLE IF NOT EXISTS `sql_audit_logs` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT COMMENT '用户ID',
    `username` VARCHAR(50) COMMENT '用户名',
    `query` TEXT NOT NULL COMMENT '查询语句',
    `sql` TEXT COMMENT '生成的SQL',
    `intent` VARCHAR(50) COMMENT '意图类型',
    `status` VARCHAR(20) COMMENT '状态',
    `error_message` TEXT COMMENT '错误信息',
    `execution_time` INT COMMENT '执行时间(ms)',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_user` (`user_id`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SQL审计日志表';

-- RAG查询日志表
CREATE TABLE IF NOT EXISTS `rag_query_logs` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT COMMENT '用户ID',
    `username` VARCHAR(50) COMMENT '用户名',
    `query` TEXT NOT NULL COMMENT '用户问题',
    `intent` VARCHAR(50) COMMENT '识别的意图',
    `retrieved_chunks` TEXT COMMENT '检索到的块',
    `citations` TEXT COMMENT '引用来源',
    `answer` TEXT COMMENT '回答内容',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_user` (`user_id`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RAG查询日志表';

-- 登录日志表
CREATE TABLE IF NOT EXISTS `login_logs` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT COMMENT '用户ID',
    `username` VARCHAR(50) COMMENT '用户名',
    `ip` VARCHAR(50) COMMENT 'IP地址',
    `user_agent` VARCHAR(500) COMMENT 'User-Agent',
    `status` VARCHAR(20) COMMENT '登录状态',
    `message` VARCHAR(200) COMMENT '消息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_user` (`user_id`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='登录日志表';

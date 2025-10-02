# Node Order System API 文档

本文档总结了 `node-order-system` 中的所有 API 端点。

## 商品 (Product) API

### 1. 获取商品详情

- **Method:** `GET`
- **Path:** `/products/:id`
- **功能:** 根据商品 ID 获取单个商品的详细信息。优先从 Redis 缓存中读取，如果缓存不存在，则查询数据库并将结果存入缓存。
- **URL 参数:**
  - `id` (必需): 商品的唯一标识符。
- **成功响应 (200):**
  ```json
  {
    "source": "cache" | "database",
    "data": {
      "id": 1,
      "name": "示例商品",
      "stock": 100,
      "image_url": "http://example.com/image.jpg"
    }
  }
  ```
- **失败响应 (404):**
  ```json
  { "error": "商品不存在" }
  ```

### 2. 获取所有商品列表

- **Method:** `GET`
- **Path:** `/products`
- **功能:** 获取数据库中所有商品的列表，按 ID 降序排列。
- **成功响应 (200):**
  ```json
  {
    "data": [
      {
        "id": 2,
        "name": "另一个商品",
        "stock": 50,
        "image_url": null
      },
      {
        "id": 1,
        "name": "示例商品",
        "stock": 100,
        "image_url": "http://example.com/image.jpg"
      }
    ]
  }
  ```

### 3. 创建新商品

- **Method:** `POST`
- **Path:** `/products`
- **功能:** 创建一个新商品，并将其库存信息同步写入 Redis。
- **请求体 (Body):**
  ```json
  {
    "name": "新商品",
    "stock": 200,
    "imageUrl": "http://example.com/new.jpg"
  }
  ```
- **参数:**
  - `name` (必需): 商品名称。
  - `stock` (必需): 商品库存，必须为非负整数。
  - `imageUrl` (可选): 商品图片的 URL。
- **成功响应 (201):**
  ```json
  {
    "message": "商品创建成功",
    "data": {
      "id": 3,
      "name": "新商品",
      "stock": 200,
      "image_url": "http://example.com/new.jpg"
    }
  }
  ```
- **失败响应 (400):**
  ```json
  { "error": "无效的商品名称或库存" }
  ```

### 4. 删除商品

- **Method:** `DELETE`
- **Path:** `/products/:id`
- **功能:** 根据 ID 删除一个商品。如果该商品有关联的订单，则无法删除。删除成功后会同步清理 Redis 中的商品信息和库存缓存。
- **URL 参数:**
  - `id` (必需): 要删除的商品的唯一标识符。
- **成功响应 (200):**
  ```json
  { "message": "商品删除成功" }
  ```
- **失败响应:**
  - **400:** `{ "error": "无法删除，该商品存在关联订单" }`
  - **404:** `{ "error": "商品未找到" }`

---

## 订单 (Order) API

### 1. 创建订单（下单）

- **Method:** `POST`
- **Path:** `/orders`
- **功能:** 创建一个新订单。此接口会先在 Redis 中进行库存预扣减，如果成功，则将订单消息发送到 Kafka 队列等待后续处理。
- **请求体 (Body):**
  ```json
  {
    "productId": 1,
    "quantity": 2
  }
  ```
- **参数:**
  - `productId` (必需): 所购买商品的 ID。
  - `quantity` (必需): 购买数量，必须为正整数。
- **成功响应 (202):**
  ```json
  { "message": "订单请求已接受，正在处理中" }
  ```
- **失败响应:**
  - **400 (参数无效):** `{ "error": "无效的请求参数" }`
  - **400 (库存不足):** `{ "error": "库存不足" }`

### 2. 获取所有订单列表

- **Method:** `GET`
- **Path:** `/orders`
- **功能:** 获取所有已创建订单的列表，包含关联的商品名称，按订单日期降序排列。
- **成功响应 (200):**
  ```json
  {
    "data": [
      {
        "id": 1,
        "quantity": 2,
        "order_date": "2023-10-27T10:00:00.000Z",
        "productName": "示例商品"
      }
    ]
  }
  ```

### 3. 撤回订单

- **Method:** `DELETE`
- **Path:** `/orders/:id`
- **功能:** 根据订单 ID 撤回一个已存在的订单。此操作会通过数据库事务将商品库存归还，并同步更新 Redis 中的库存。
- **URL 参数:**
  - `id` (必需): 要撤回的订单的唯一标识符。
- **成功响应 (200):**
  ```json
  { "message": "订单撤回成功" }
  ```
- **失败响应 (404):**
  ```json
  { "error": "订单未找到" }
  ```

<template>
  <div id="app-wrapper">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <h1>订单系统</h1>
      <nav class="app-nav">
        <button :class="{ active: currentPage === 'main' }" @click="navigateTo('main')">库存管理</button>
        <button :class="{ active: currentPage === 'orders' }" @click="navigateTo('orders')">订单列表</button>
      </nav>
    </header>

    <!-- 主页面：库存管理 -->
    <main v-if="currentPage === 'main'" class="main-container">
      <!-- 左侧操作面板 -->
      <div class="left-panel">
        <div class="module">
          <h2>添加新商品</h2>
          <div class="input-group">
            <input v-model="newProduct.name" placeholder="商品名称" />
            <input v-model.number="newProduct.stock" type="number" placeholder="初始库存" />
          </div>
          <div class="input-group">
            <input v-model="newProduct.imageUrl" placeholder="商品图片URL (可选)" />
            <button @click="addProduct">添加商品</button>
          </div>
        </div>

        <div class="module">
          <h2>查询与操作</h2>
          <div class="input-group">
            <input v-model.number="productId" type="number" placeholder="输入或点击右侧列表选择" />
            <button @click="fetchProduct">查询商品</button>
          </div>
          
          <div v-if="productInfo" class="product-info">
            <h3>商品详情</h3>
            <img v-if="productInfo.image_url" :src="productInfo.image_url || 'https://i.ibb.co/9H6GY9vc/2401758881242-pic-thumb.jpg'" alt="商品图片" class="product-image"/>
            <p><strong>名称:</strong> {{ productInfo.name }}</p>
            <p><strong>当前库存:</strong> {{ productInfo.stock }}</p>
          </div>
        </div>

        <div class="module" v-if="productInfo">
          <h2>创建订单</h2>
          <div class="input-group">
            <input v-model.number="quantity" type="number" placeholder="输入购买数量" />
            <button @click="createOrder">创建订单</button>
          </div>
        </div>

        <div v-if="message" class="message" :class="{ 'is-error': isError }">
          <p>{{ message }}</p>
        </div>
      </div>

      <!-- 右侧商品列表 -->
      <div class="right-panel">
        <h2>库存列表</h2>
        <input v-model="searchTerm" class="search-bar" placeholder="搜索商品名称..." />
        <div class="product-list">
          <div v-if="!filteredProducts.length" class="list-empty-state">
            <p>没有找到匹配的商品</p>
          </div>
          <div v-for="product in filteredProducts.slice(0, 10)" :key="product.id" class="product-list-item" @click="selectProduct(product)">
            <img :src="product.image_url || 'https://i.ibb.co/9H6GY9vc/2401758881242-pic-thumb.jpg'" alt="商品图" class="list-item-image" />
            <div class="list-item-details">
              <p class="list-item-name">{{ product.name }}</p>
              <p class="list-item-stock">库存: {{ product.stock }}</p>
            </div>
            <div class="list-item-actions">
              <button class="btn-danger btn-small" @click.stop="deleteProduct(product.id)">删除</button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 新页面：订单列表 -->
    <main v-if="currentPage === 'orders'" class="orders-container">
      <h2>订单列表</h2>
      <div class="table-wrapper">
        <table class="orders-table">
          <thead>
            <tr>
              <th>订单ID</th>
              <th>商品名称</th>
              <th>数量</th>
              <th>下单时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!orders.length">
              <td colspan="5" class="empty-state">暂无订单</td>
            </tr>
            <tr v-for="order in orders.slice(0, 10)" :key="order.id">
              <td>#{{ order.id }}</td>
              <td>{{ order.productName }}</td>
              <td>{{ order.quantity }}</td>
              <td>{{ new Date(order.order_date).toLocaleString() }}</td>
              <td>
                <button class="btn-danger" @click="withdrawOrder(order.id)">撤回</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import axios from 'axios';

// --- 页面状态 ---
const currentPage = ref('main'); // 'main' 或 'orders'

// --- 响应式状态 ---
const productId = ref(null);
const quantity = ref(1);
const productInfo = ref(null);
const message = ref('');
const isError = ref(false);
const allProducts = ref([]);
const searchTerm = ref('');
const orders = ref([]);

const newProduct = reactive({ name: '', stock: 0, imageUrl: '' });

// --- 计算属性 ---
const filteredProducts = computed(() => {
  if (!searchTerm.value) return allProducts.value;
  return allProducts.value.filter(p => p.name.toLowerCase().includes(searchTerm.value.toLowerCase()));
});

// --- 方法 ---

function showMessage(text, error = false) {
  message.value = text;
  isError.value = error;
  setTimeout(() => message.value = '', 4000);
}

function navigateTo(page) {
  currentPage.value = page;
  if (page === 'orders') {
    fetchOrders();
  }
  if (page === 'main') {
    fetchAllProducts();
  }
}

async function fetchAllProducts() {
  try {
    const response = await axios.get('/api/products');
    allProducts.value = response.data.data;
  } catch (error) {
    showMessage('加载商品列表失败！', true);
  }
}

async function addProduct() {
  if (!newProduct.name || newProduct.stock <= 0) {
    return showMessage('请输入有效的商品名称和大于0的库存。', true);
  }
  showMessage('正在添加商品...');
  try {
    const response = await axios.post('/api/products', { ...newProduct });
    showMessage(`商品 "${response.data.data.name}" 添加成功！`, false);
    newProduct.name = '';
    newProduct.stock = 0;
    newProduct.imageUrl = '';
    await fetchAllProducts(); // 刷新列表
  } catch (error) {
    showMessage(`添加失败: ${error.response?.data?.error || error.message}`, true);
  }
}

async function fetchProduct() {
  if (!productId.value) {
    return showMessage('请输入有效的商品ID。', true);
  }
  showMessage('正在查询...');
  productInfo.value = null;
  try {
    const response = await axios.get(`/api/products/${productId.value}`);
    productInfo.value = response.data.data;
    showMessage(`查询成功！数据来源: ${response.data.source}`, false);
  } catch (error) {
    productInfo.value = null;
    showMessage(error.response?.status === 404 ? `错误：找不到ID为 ${productId.value} 的商品。` : `查询失败: ${error.message}`, true);
  }
}

async function createOrder() {
  if (!productInfo.value) return showMessage('请先查询一个有效的商品。', true);
  if (quantity.value <= 0) return showMessage('购买数量必须大于0。', true);
  showMessage('正在提交订单...');
  try {
    await axios.post('/api/orders', { productId: productInfo.value.id, quantity: quantity.value });
    showMessage(`下单成功！`, false);
    await fetchProduct(); // 刷新详情
    await fetchAllProducts(); // 刷新列表
  } catch (error) {
    showMessage(`下单失败: ${error.response?.data?.error || error.message}`, true);
  }
}

function selectProduct(product) {
  productId.value = product.id;
  fetchProduct();
}

async function deleteProduct(productIdToDelete) {
  if (!confirm(`确定要删除ID为 #${productIdToDelete} 的商品吗？`)) return;

  try {
    const response = await axios.delete(`/api/products/${productIdToDelete}`);
    showMessage(response.data.message, false);
    // 如果删除的商品是当前正在查看的商品，则清空详情
    if (productInfo.value && productInfo.value.id === productIdToDelete) {
      productInfo.value = null;
    }
    await fetchAllProducts(); // 刷新商品列表
  } catch (error) {
    showMessage(`删除失败: ${error.response?.data?.error || error.message}`, true);
  }
}

async function fetchOrders() {
  try {
    const response = await axios.get('/api/orders');
    orders.value = response.data.data;
  } catch (error) {
    showMessage('加载订单列表失败！', true);
  }
}

async function withdrawOrder(orderId) {
  if (!confirm(`确定要撤回订单 #${orderId} 吗？此操作会恢复商品库存。`)) return;
  
  try {
    const response = await axios.delete(`/api/orders/${orderId}`);
    showMessage(response.data.message, false);
    await fetchOrders(); // 刷新订单列表
    await fetchAllProducts(); // 刷新商品列表（因为库存变了）
  } catch (error) {
    showMessage(`撤回失败: ${error.response?.data?.error || error.message}`, true);
  }
}

// --- 生命周期钩子 ---
onMounted(() => {
  // 初始加载时，只加载主页的商品列表
  fetchAllProducts();
});
</script>

<style>
:root {
  --brand-color: #4299e1; /* blue-500 */
  --brand-color-dark: #2b6cb0; /* blue-700 */
  --gray-50: #f7fafc;
  --gray-100: #edf2f7;
  --gray-200: #e2e8f0;
  --gray-400: #a0aec0;
  --gray-600: #718096;
  --gray-700: #4a5568;
  --gray-800: #2d3748;
  --red-100: #fff5f5;
  --red-500: #e53e3e;
  --red-700: #c53030;
  --green-100: #f0fff4;
  --green-700: #2f855a;
}

body { 
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
  background-color: var(--gray-50);
  color: var(--gray-700);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  margin: 0;
}

#app-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  margin-bottom: 10px;
}

.app-header h1 { 
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--gray-800);
  text-align: center;
  margin: 0;
}

.app-nav button {
  margin-left: 10px;
  background-color: transparent;
  color: var(--gray-600);
  border: 1px solid var(--gray-200);
  box-shadow: none;
  padding: 10px 20px;
  font-weight: 600;
}
.app-nav button:hover {
  background-color: var(--gray-100);
  color: var(--gray-800);
  transform: none;
  box-shadow: none;
}
.app-nav button.active {
  background-color: var(--brand-color);
  color: white;
  border-color: var(--brand-color);
}

.main-container { 
  display: flex; 
  align-items: flex-start; /* 顶部对齐 */
  gap: 30px; 
}

.left-panel { flex: 1; min-width: 450px; }
.right-panel { 
  flex: 1; 
  min-width: 450px; 
  background: #fff; 
  padding: 25px;
  border-radius: 12px; 
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  position: sticky; /* 让右侧栏在滚动时固定 */
  top: 30px;
  max-height: calc(100vh - 60px);
  display: flex; 
  flex-direction: column; 
}

h2 { 
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--gray-800);
  text-align: left;
  margin-top: 0;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--gray-200);
}

.module { 
  background: #fff; 
  padding: 25px; 
  margin-bottom: 25px; 
  border-radius: 12px; 
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.input-group { display: flex; flex-wrap: wrap; align-items: center; gap: 15px; margin-bottom: 15px; }

input {
  padding: 12px;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  flex: 1;
  font-size: 14px;
  transition: all 0.2s ease-in-out;
}
input:focus {
  outline: none;
  border-color: var(--brand-color);
  box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.5);
}

button {
  padding: 12px 20px;
  border: none;
  background-color: var(--brand-color);
  color: white;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}
button:hover {
  background-color: var(--brand-color-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.product-info { margin-top: 20px; padding: 15px; border-radius: 8px; background-color: var(--gray-50); border: 1px solid var(--gray-200); }
.product-info h3 { margin-top: 0; font-size: 1rem; font-weight: 600; }
.product-image { max-width: 100%; height: auto; border-radius: 8px; margin-bottom: 15px; }

.message { margin-top: 20px; padding: 12px; border-radius: 8px; text-align: center; font-weight: 500; }
.message.is-error { background-color: var(--red-100); border: 1px solid var(--red-500); color: var(--red-700); }
.message:not(.is-error) { background-color: var(--green-100); border: 1px solid var(--green-700); color: var(--green-700); }

.search-bar { width: 100%; padding: 12px; font-size: 16px; margin-bottom: 15px; box-sizing: border-box; }

.product-list { overflow-y: auto; }
.list-empty-state { text-align: center; padding: 40px; color: var(--gray-600); }

.product-list-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 16px;
  border-bottom: 1px solid var(--gray-100);
  cursor: pointer;
  transition: background-color 0.2s ease-in-out;
  border-radius: 8px;
}
.product-list-item:hover { background-color: var(--gray-100); }

.list-item-image { 
  width: 100px;
  height: 60px;
  object-fit: contain;
  border-radius: 6px; 
  background-color: var(--gray-100); 
}
.list-item-details { flex: 1; }
.list-item-name { font-weight: 600; color: var(--gray-800); margin: 0 0 5px 0; }
.list-item-stock { font-size: 13px; color: var(--gray-600); margin: 0; }
.list-item-actions { margin-left: auto; }

.orders-container {
  background: #fff;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.table-wrapper { overflow-x: auto; }

.orders-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}
.orders-table th, .orders-table td {
  padding: 12px 15px;
  border-bottom: 1px solid var(--gray-100);
}
.orders-table th {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-600);
  background-color: var(--gray-50);
}
.orders-table td {
  font-size: 14px;
}
.orders-table .empty-state {
  text-align: center;
  color: var(--gray-600);
  padding: 40px 0;
}

.btn-danger {
  background-color: transparent;
  color: var(--red-500);
  padding: 5px 10px;
  font-weight: 500;
  border: 1px solid var(--red-100);
}
.btn-danger:hover {
  background-color: var(--red-100);
  color: var(--red-700);
  transform: none;
  box-shadow: none;
}

.btn-small {
  padding: 4px 8px;
  font-size: 12px;
}
</style>

// App.jsx
/**
 * @file App.jsx
 * @description
 * 这是整个前端应用的根组件。它负责管理核心的响应式状态，
 * 如产品列表(products)和订单列表(orders)，并协调子组件的渲染和交互。
 *
 * @vue-logic
 * - `ref` 用于创建独立的响应式变量 (e.g., selectedProduct, currentView)。
 * - `onMounted` 是一个生命周期钩子，在组件挂载到 DOM 后执行，非常适合用来获取初始数据。
 * - `computed` 用于创建计算属性，它会根据依赖的响应式变量自动更新。
 */
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import ProductList from './components/ProductList.vue';
import OrderForm from './components/OrderForm.vue';
import OrderList from './components/OrderList.vue';

export default {
  components: {
    ProductList,
    OrderForm,
    OrderList,
  },
  setup() {
    // --- 响应式状态定义 (Reactive State) ---
    const products = ref([]); // 存放所有商品
    const orders = ref([]); // 存放所有订单
    const selectedProduct = ref(null); // 当前选中的、用于下单的商品
    const currentView = ref('products'); // 控制当前显示哪个视图 ('products' 或 'orders')
    const notification = ref({ message: '', type: '' }); // 用于显示操作结果的通知

    // --- 计算属性 (Computed Properties) ---
    // @why 使用计算属性？
    // 为了将视图逻辑与状态分离。当 `currentView` 的值改变时，
    // 这两个计算属性会自动重新计算，从而控制对应视图的显示与隐藏，
    // 而无需在模板中使用复杂的 `v-if` 判断。
    const showProducts = computed(() => currentView.value === 'products');
    const showOrders = computed(() => currentView.value === 'orders');

    // --- 数据获取方法 (Data Fetching Methods) ---
    
    /**
     * @function fetchProducts
     * @description 从后端API获取商品列表。
     * @why 使用 axios 和 /api 前缀？
     *      `vite.config.js` 中配置了代理，所有 `/api` 开头的请求都会被转发到
     *      `http://localhost:3000`，这解决了前端开发中的跨域问题。
     */
    const fetchProducts = async () => {
      try {
        const response = await axios.get('/api/products');
        products.value = response.data.data;
      } catch (error) {
        showNotification('获取商品失败', 'error');
        console.error('获取商品列表失败:', error);
      }
    };

    /**
     * @function fetchOrders
     * @description 从后端API获取订单列表。
     */
    const fetchOrders = async () => {
      try {
        const response = await axios.get('/api/orders');
        orders.value = response.data.data;
      } catch (error) {
        showNotification('获取订单失败', 'error');
        console.error('获取订单列表失败:', error);
      }
    };

    // --- 事件处理方法 (Event Handlers) ---

    /**
     * @function handleSelectProduct
     * @description 处理从 ProductList 组件传来的商品选择事件。
     * @param {object} product - 被选中的商品对象。
     */
    const handleSelectProduct = (product) => {
      selectedProduct.value = product;
    };

    /**
     * @function handleOrderSubmitted
     * @description 处理订单提交后的逻辑。
     * @param {object} result - 订单提交的结果。
     */
    const handleOrderSubmitted = (result) => {
      if (result.success) {
        showNotification(result.message, 'success');
        // 订单提交成功后，清空选择并重新获取商品列表以更新库存
        selectedProduct.value = null;
        fetchProducts();
      } else {
        showNotification(result.message, 'error');
      }
    };

    /**
     * @function switchView
     * @description 切换 'products' 和 'orders' 视图。
     * @param {string} viewName - 目标视图的名称。
     */
    const switchView = (viewName) => {
      currentView.value = viewName;
      if (viewName === 'orders') {
        fetchOrders(); // 切换到订单视图时，自动加载订单数据
      } 
    };

    /**
     * @function showNotification
     * @description 显示一个短暂的通知消息。
     */
    const showNotification = (message, type) => {
      notification.value = { message, type };
      setTimeout(() => {
        notification.value = { message: '', type: '' };
      }, 3000); // 3秒后自动消失
    };

    // --- 生命周期钩子 (Lifecycle Hooks) ---
    // 在组件挂载后，立即获取初始的商品列表。
    onMounted(fetchProducts);

    // 将所有状态和方法暴露给模板
    return {
      products,
      orders,
      selectedProduct,
      currentView,
      notification,
      showProducts,
      showOrders,
      handleSelectProduct,
      handleOrderSubmitted,
      switchView,
    };
  },
};
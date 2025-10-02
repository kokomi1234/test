// ProductList.jsx
/**
 * @file ProductList.jsx
 * @description
 * 负责展示商品列表，并允许用户选择一个商品进行下单。
 *
 * @vue-logic
 * - `defineProps` 用于声明该组件可以从父组件接收哪些属性 (props)。
 * - `defineEmits` 用于声明该组件可以触发哪些自定义事件，以通知父组件。
 * - `@click="$emit('select-product', product)"` 是 Vue 的事件绑定和触发语法。
 *   点击按钮时，会触发一个名为 `select-product` 的自定义事件，并将 `product` 对象作为参数传递给父组件。
 */
import { defineProps, defineEmits } from 'vue';

export default {
  props: {
    // 从父组件接收商品列表数组
    products: {
      type: Array,
      required: true,
    },
  },
  emits: ['select-product'], // 声明可以触发 'select-product' 事件
  setup(props, { emit }) {
    /**
     * @function selectProduct
     * @description 当用户点击“下单”按钮时，触发事件通知父组件。
     * @param {object} product - 被点击的商品。
     */
    const selectProduct = (product) => {
      // 使用 emit 方法触发事件
      emit('select-product', product);
    };

    return {
      selectProduct,
    };
  },
};
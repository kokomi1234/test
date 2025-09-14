#!/bin/bash

# Redis集群统一管理脚本 - DNS服务发现版本
# 使用方法: ./redis-cluster.sh [start|restart|stop|status]

case "$1" in
  "start"|"")
    echo "🚀 启动Redis集群..."
    cd "$(dirname "$0")/.."
    docker-compose up -d
    sleep 3
    
    echo "⚡ 创建集群（DNS服务发现）..."
    # 清理可能存在的旧状态
    docker exec redis-node-1 redis-cli FLUSHALL 2>/dev/null || true
    docker exec redis-node-2 redis-cli FLUSHALL 2>/dev/null || true
    docker exec redis-node-3 redis-cli FLUSHALL 2>/dev/null || true
    
    docker exec redis-node-1 redis-cli CLUSTER RESET HARD 2>/dev/null || true
    docker exec redis-node-2 redis-cli CLUSTER RESET HARD 2>/dev/null || true
    docker exec redis-node-3 redis-cli CLUSTER RESET HARD 2>/dev/null || true
    
    # 使用容器名创建集群
    docker exec redis-node-1 redis-cli --cluster create redis-node-1:6379 redis-node-2:6379 redis-node-3:6379 --cluster-replicas 0 --cluster-yes
    
    # 等待集群稳定
    echo "⏳ 等待集群稳定..."
    sleep 5
    
    echo "✅ 集群启动完成！"
    echo ""
    echo "📝 使用方式："
    echo "  容器内连接: docker exec -it redis-node-1 redis-cli -c"
    echo "  外部连接端口: localhost:7001, localhost:7002, localhost:7003"
    echo "  Python客户端: RedisCluster(startup_nodes=[{'host':'localhost','port':7001}])"
    ;;
    
  "restart")
    echo "🔄 重启Redis集群..."
    docker-compose down
    sleep 2
    $0 start
    ;;
    
  "restart-keep-data"|"soft-restart")
    echo "🔄 温和重启Redis集群（保留数据）..."
    docker-compose stop
    sleep 2
    docker-compose start
    sleep 5
    
    # 检查集群状态
    cluster_state=$(docker exec redis-node-1 redis-cli cluster info 2>/dev/null | grep cluster_state || echo "cluster_state:fail")
    
    if [[ $cluster_state == *"ok"* ]]; then
        echo "✅ 集群自动恢复成功，数据已保留！"
    else
        echo "🔧 集群需要重新建立连接..."
        # 尝试修复连接而不清空数据
        docker exec redis-node-1 redis-cli cluster meet redis-node-2 6379 2>/dev/null || true
        docker exec redis-node-1 redis-cli cluster meet redis-node-3 6379 2>/dev/null || true
        sleep 5
        
        final_state=$(docker exec redis-node-1 redis-cli cluster info | grep cluster_state)
        echo "  最终状态: $final_state"
    fi
    ;;
    
  "stop")
    echo "🛑 停止Redis集群..."
    docker-compose down
    echo "✅ 集群已停止"
    ;;
    
  "status")
    echo "📊 Redis集群状态："
    echo ""
    
    # 检查容器状态
    if docker-compose ps | grep -q redis-node-1.*Up; then
        echo "🟢 容器状态: 运行中"
        
        # 检查集群状态
        cluster_state=$(docker exec redis-node-1 redis-cli cluster info 2>/dev/null | grep cluster_state || echo "cluster_state:无法连接")
        echo "🔗 $cluster_state"
        
        if [[ $cluster_state == *"ok"* ]]; then
            # 显示节点信息
            echo ""
            echo "📍 集群节点:"
            docker exec redis-node-1 redis-cli cluster nodes 2>/dev/null | while read line; do
                if [[ $line == *"master"* ]]; then
                    node_name=$(echo "$line" | awk '{print $2}' | cut -d':' -f1)
                    slots=$(echo "$line" | grep -o '\[.*\]' || echo "无槽位")
                    echo "  🔹 $node_name $slots"
                fi
            done
            
            # 显示数据统计
            total_keys=$(docker exec redis-node-1 redis-cli -c DBSIZE 2>/dev/null || echo "0")
            echo ""
            echo "📊 总键数: $total_keys"
            
            if [[ $total_keys -gt 0 ]]; then
                echo "🔍 数据示例:"
                docker exec redis-node-1 redis-cli -c --scan | head -3 | while read key; do
                    if [ -n "$key" ]; then
                        value=$(docker exec redis-node-1 redis-cli -c get "$key" 2>/dev/null | head -c 50)
                        echo "  $key = $value"
                    fi
                done
            fi
        else
            echo "⚠️ 集群状态异常"
        fi
    else
        echo "🔴 容器状态: 已停止"
        echo "💡 运行 '$0 start' 来启动集群"
    fi
    ;;
    
  "test")
    echo "🧪 测试Redis集群功能..."
    
    if ! docker exec redis-node-1 redis-cli ping &>/dev/null; then
        echo "❌ 无法连接到Redis，请先启动集群"
        exit 1
    fi
    
    echo "📝 写入测试数据..."
    docker exec redis-node-1 redis-cli -c set test:key1 "Hello Redis Cluster"
    docker exec redis-node-1 redis-cli -c set test:key2 "DNS Discovery Works"
    docker exec redis-node-1 redis-cli -c set test:counter 100
    
    echo "📖 读取测试数据..."
    val1=$(docker exec redis-node-1 redis-cli -c get test:key1)
    val2=$(docker exec redis-node-1 redis-cli -c get test:key2)
    val3=$(docker exec redis-node-1 redis-cli -c get test:counter)
    
    echo "  test:key1 = $val1"
    echo "  test:key2 = $val2"
    echo "  test:counter = $val3"
    
    if [[ "$val1" == "Hello Redis Cluster" ]]; then
        echo "✅ 集群功能测试通过！"
    else
        echo "❌ 集群功能测试失败"
    fi
    ;;
    
  *)
    echo "🔧 Redis集群统一管理工具"
    echo ""
    echo "使用方式:"
    echo "  $0 start                   # 启动集群（清空数据）"
    echo "  $0 restart                 # 重启集群（清空数据）"
    echo "  $0 restart-keep-data       # 温和重启（保留数据）"
    echo "  $0 stop                    # 停止集群"
    echo "  $0 status                  # 查看集群状态"
    echo "  $0 test                    # 测试集群功能"
    echo ""
    echo "🚀 特性："
    echo "  ✅ DNS服务发现 - 快速稳定的集群创建"
    echo "  ✅ 外部访问支持 - 通过localhost:7001-7003访问"
    echo "  ✅ 数据持久化 - AOF + RDB双重保护"
    echo "  ✅ 温和重启 - 可选择保留数据重启"
    echo ""
    echo "📖 连接方式："
    echo "  容器内: docker exec -it redis-node-1 redis-cli -c"
    echo "  Python: RedisCluster(startup_nodes=[{'host':'localhost','port':7001}])"
    ;;
esac
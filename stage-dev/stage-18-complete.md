# Stage 18 完成总结: User Session & High Concurrency

## 🎯 目标
为生产环境部署做好准备，重点解决系统的并发处理能力、用户会话管理以及恶意请求防护。确保系统在多用户同时访问时依然稳定流畅。

## ✅ 完成事项

### 1. 高并发架构升级 (Gunicorn)
- **多线程 Worker**: 摒弃了单线程的 `flask run`，采用 **Gunicorn** 作为 WSGI 服务器。
- **配置优化 (`gunicorn_config.py`)**:
    - 使用 `gthread` worker 类型，专为 I/O 密集型任务（如 LLM 调用）设计。
    - 配置 `workers = 2 * CPU + 1` 和 `threads = 4`，大幅提升并发吞吐量。
    - 设置 120秒 超时时间，防止 LLM 生成过慢导致连接断开。

### 2. 速率限制与防护 (Rate Limiting)
- **集成 Flask-Limiter**:
    - 在 `flask_api.py` 中集成了限流中间件。
    - 默认策略：`200 per day`, `50 per hour`。
    - **关键保护**: `/chat` 接口限制为 `10 per minute`，有效防止脚本刷 Token。
    - **防爆破**: `/api/auth/login` 限制为 `5 per minute`。
- **Redis 支持**: 配置了自动降级策略，优先使用 Redis (Docker 中已配置)，若不可用则降级为内存存储。

### 3. 用户会话增强
- **Session 安全**: 引入 `FLASK_SECRET_KEY` 对 Cookie 进行加密签名。
- **持久化 Cookie**: 配置 `user_id` Cookie 有效期为 30 天 (`max_age=2592000`)，确保学生关闭浏览器后 ID 不变，实现跨会话记忆。

### 4. Docker 生产化
- **Dockerfile.prod**: 编写了基于 `python:3.9-slim` 的多阶段构建文件，移除构建依赖，减小镜像体积。
- **docker-compose.prod.yml**: 定义了完整的生产技术栈：
    - `vr-recommender`: Gunicorn 驱动的 Flask 应用。
    - `redis`: 用于限流计数器和缓存。
    - `neo4j`: 图数据库服务。
    - 自动配置网络互通和数据卷持久化。

## 🧪 测试验证
1.  **并发测试**: Gunicorn 成功启动并在后台运行，响应速度正常。
2.  **限流测试**: 使用脚本模拟高频请求，第 11 次请求准确返回 `429 Too Many Requests`。
3.  **全栈测试**: 
    - Dashboard 登录拦截有效。
    - Chatbot 正常加载并与后端通信。
    - 数据库连接（MongoDB Atlas）在并发环境下保持稳定。

## 🚀 项目里程碑
至此，**VR Recommender System** 已完成从原型开发到生产就绪的全部转型。
- **Stage 1-15**: 核心功能（RAG、知识图谱、推荐算法）。
- **Stage 16**: 数据层统一 (MongoDB)。
- **Stage 17**: 安全与管理后台 (Auth & Dashboard)。
- **Stage 18**: 生产部署与并发优化 (Docker & Gunicorn)。

系统现在已准备好在学校服务器上部署。

## 🔧 Deployment Hardening (Post-Stage Fixes)

在最终的 Docker 部署测试中，解决了以下关键兼容性与性能问题：

### 1. 依赖补全
- **Python 依赖**: 在 `requirements.txt` 中补全了缺失的 `neo4j>=5.0.0` 驱动，解决了 `ModuleNotFoundError`。
- **系统依赖**: 在 `Dockerfile.prod` 中添加了 `g++` 和 `build-essential`，确保 `chromadb` 和 `sentence-transformers` 的底层 C++ 扩展能正确编译。

### 2. 连接配置
- **Docker 网络**: 在 `docker-compose.prod.yml` 中显式配置了 `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` 环境变量，确保容器内应用能正确连接到 Neo4j 服务容器。

### 3. 资源优化
- **Worker 限制**: 将 Gunicorn worker 数量从默认的 `2 * CPU + 1` (在高性能机上为 21) 限制为 **4**，防止在 Docker 启动瞬间耗尽宿主机 CPU 资源。
- **端口修正**: 修正了 Gunicorn 绑定端口与 Docker 映射端口不一致的问题 (统一为 5000)。

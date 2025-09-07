# 智能体编排管道架构图

## 当前智能体编排架构

```mermaid
graph TD
    A[开始] --> B[阶段1: 文献收集]
    B --> C[阶段2: 预处理和过滤]
    C --> D[阶段3: 分类和聚类]
    D --> E[阶段4: 趋势分析]
    E --> F[阶段5: 调研生成]
    F --> G[阶段6: 评估和质量评估]
    G --> H[输出: 自主生成的科学文献调研]

    subgraph "智能体组件"
        RA[检索智能体<br/>Retriever Agent]
        PA[预处理组件<br/>Preprocessor]
        CA[分类智能体<br/>Classifier Agent]
        SA[总结智能体<br/>Summarizer Agent]
        CRA[批评智能体<br/>Critic Agent]
    end

    subgraph "数据源"
        ARXIV[arXiv]
        OPENALEX[OpenAlex]
        SEMANTIC[Semantic Scholar]
        GOOGLE[Google Scholar]
    end

    subgraph "技术栈"
        PYTHON[Python 3.9+]
        LANGCHAIN[LangChain]
        CLAUDE[Anthropic Claude]
        VECTOR[向量数据库]
        SQLITE[SQLite]
    end

    %% 智能体与阶段的连接
    B -.-> RA
    C -.-> PA
    D -.-> CA
    F -.-> SA
    G -.-> CRA

    %% 数据源连接
    RA --> ARXIV
    RA --> OPENALEX
    RA --> SEMANTIC
    RA --> GOOGLE

    %% 技术栈连接
    RA -.-> PYTHON
    CA -.-> LANGCHAIN
    SA -.-> CLAUDE
    PA -.-> VECTOR
    CRA -.-> SQLITE

    %% 数据流
    B --> |原始论文| C
    C --> |清理后数据| D
    D --> |分类结果| E
    E --> |趋势分析| F
    F --> |生成内容| G
    G --> |质量评估| H

    %% 样式
    classDef agentClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef stageClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef sourceClass fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef techClass fill:#fff3e0,stroke:#e65100,stroke-width:2px

    class RA,PA,CA,SA,CRA agentClass
    class B,C,D,E,F,G stageClass
    class ARXIV,OPENALEX,SEMANTIC,GOOGLE sourceClass
    class PYTHON,LANGCHAIN,CLAUDE,VECTOR,SQLITE techClass
```

## 智能体详细工作流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant RA as 检索智能体
    participant PA as 预处理组件
    participant CA as 分类智能体
    participant SA as 总结智能体
    participant CRA as 批评智能体
    participant Output as 输出

    User->>RA: 启动文献收集
    RA->>RA: 多源搜索策略
    RA->>PA: 传递原始论文数据
    
    PA->>PA: 文本处理和清理
    PA->>PA: 质量评估
    PA->>CA: 传递清理后数据
    
    CA->>CA: 内容分析和分类
    CA->>CA: 主题建模
    CA->>SA: 传递分类结果
    
    SA->>SA: 生成调研内容
    SA->>SA: 质量检查
    SA->>CRA: 传递生成内容
    
    CRA->>CRA: 多维度评估
    CRA->>CRA: 与人工调研对比
    CRA->>Output: 输出最终调研
    
    Output->>User: 返回自主生成的文献调研
```

## 智能体间通信机制

```mermaid
graph LR
    subgraph "通信层"
        JSON[JSON数据格式]
        STATE[共享状态管理]
        ERROR[错误处理]
        MONITOR[进度监控]
    end

    subgraph "智能体"
        RA[检索智能体]
        CA[分类智能体]
        SA[总结智能体]
        CRA[批评智能体]
    end

    RA <--> JSON
    CA <--> JSON
    SA <--> JSON
    CRA <--> JSON

    RA <--> STATE
    CA <--> STATE
    SA <--> STATE
    CRA <--> STATE

    RA <--> ERROR
    CA <--> ERROR
    SA <--> ERROR
    CRA <--> ERROR

    RA <--> MONITOR
    CA <--> MONITOR
    SA <--> MONITOR
    CRA <--> MONITOR

    classDef commClass fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    classDef agentClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px

    class JSON,STATE,ERROR,MONITOR commClass
    class RA,CA,SA,CRA agentClass
```

## 关键特性

### 1. 模块化设计
- 每个智能体负责特定任务
- 松耦合架构便于维护和扩展
- 可独立测试和优化各组件

### 2. 透明度和可解释性
- 完整的AI贡献声明
- 详细的流程文档
- 源追踪和引用管理
- 人工监督和验证

### 3. 质量保证
- 多维度评估指标
- 与人工调研对比
- 事实验证和一致性检查
- 持续的质量监控

### 4. 性能优化
- 批处理和平行处理
- 中间结果缓存
- API使用限制管理
- 增量更新机制

